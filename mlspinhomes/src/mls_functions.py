import re as re
import time
import zipcode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException

from bs4 import BeautifulSoup
# import pdb

def init_driver(file_path):
    # Starting maximized fixes https://github.com/ChrisMuir/Zillow/issues/1
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("headless")

    driver = webdriver.Chrome(executable_path=file_path, 
                              chrome_options=options)
    driver.wait = WebDriverWait(driver, 10)
    return(driver)

def navigate_to_website(driver, site):
    driver.get(site)
    # Check to make sure a captcha page is not displayed.
    check_for_captcha(driver)

def click_find_agent(driver):
    try:
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="Master_Viewport"]/div/div[4]/div/div/ul/li[1]/div/a[1]')))
        button.click()
        time.sleep(10)
    except (TimeoutException, NoSuchElementException):
        raise ValueError("Clicking the 'FIND AN AGENT' button failed")
    # Check to make sure a captcha page is not displayed.
    check_for_captcha(driver)

def click_new_search(driver):
    try:
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.ID, "NewSearch")))
        button.click()
        time.sleep(10)
    except (TimeoutException, NoSuchElementException):
        raise ValueError("Clicking the 'New Search' button failed")
    # Check to make sure a captcha page is not displayed.
    check_for_captcha(driver)

def enter_search_term(driver, search_term):
    if not isinstance(search_term, str):
        search_term = str(search_term)
    try:
        search_bar = driver.wait.until(EC.presence_of_element_located(
            ((By.ID, "Master_Zip"))))
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.ID, "Master_btnSubmit")))
        search_bar.clear()
        time.sleep(3)
        search_bar.send_keys(search_term)
        time.sleep(3)
        button.click()
        time.sleep(3)
        return(True)
    except (TimeoutException, NoSuchElementException, WebDriverException):
        return(False)
    # Check to make sure a captcha page is not displayed.
    check_for_captcha(driver)

def test_for_no_results(driver):
    no_results = _is_element_displayed(driver, 
        "//*[contains(text(), 'Sorry, no matches were found.')]", "xpath")
    return(no_results)


def get_html(driver):
    output = []
    keep_going = True
    page = 1
    while keep_going:
        next_page_button = '//*[@id="Master_AOResults"]/div[1]/table/tbody/tr/td[3]/span/a[{}]'.format(page + 1)
        # Pull page HTML
        try:
            output.append(driver.page_source)
        except TimeoutException:
            pass
        # Check to see if a "next page" link exists.
        keep_going = _is_element_displayed(driver, next_page_button, "xpath")
        if keep_going:
            try:
                driver.wait.until(EC.element_to_be_clickable((By.XPATH, next_page_button))).click()
                time.sleep(5)
                # Check to make sure a captcha page is not displayed.
                check_for_captcha(driver)
                page += 1
            except TimeoutException:
                keep_going = False

        else:
            keep_going = False

    return(output)

def get_realtors(list_obj):
    output = []
    for i in list_obj:
        soup = BeautifulSoup(i, "lxml")
        htmlSplit = soup.find_all('div', {'class': 'ao-info-container'})
        output += htmlSplit
    return(output)

def get_info(soup_obj, html_type, info):
    try:
        content = soup_obj.find(
            html_type, {"class" : info}).get_text().split()
        content = ' '.join(content)
    except (ValueError, AttributeError):
        content = "NA"
    if _is_empty(content):
        content = "NA"
    return(content)

# Helper function for testing if an object is "empty" or not.
def _is_empty(obj):
    if any([len(obj) == 0, obj == "null", obj.isspace()]):
        return(True)
    else:
        return(False)

# Helper function for checking for the presence of a web element.
def _is_element_displayed(driver, elem_text, elem_type):
    if elem_type == "class":
        try:
            out = driver.find_element_by_class_name(elem_text).is_displayed()
        except (NoSuchElementException, TimeoutException):
            out = False
    elif elem_type == "css":
        try:
            out = driver.find_element_by_css_selector(elem_text).is_displayed()
        except (NoSuchElementException, TimeoutException):
            out = False
    elif elem_type == "id":
        try:
            out = driver.find_element_by_id(elem_text).is_displayed()
        except (NoSuchElementException, TimeoutException):
            out = False
    elif elem_type == "xpath":
        try:
            out = driver.find_element_by_xpath(elem_text).is_displayed()
        except (NoSuchElementException, TimeoutException):
            out = False
    else:
        raise ValueError("arg 'elem_type' must be either 'class', 'css', 'xpath' or 'id")
    return(out)

# If captcha page is displayed, this function will run indefinitely until the 
# captcha page is no longer displayed (checks for it every 30 seconds).
# Purpose of the function is to "pause" execution of the scraper until the 
# user has manually completed the captcha requirements.
def _pause_for_captcha(driver):
    while True:
        time.sleep(30)
        if not _is_element_displayed(driver, "captcha-container", "class"):
            break

# Check to see if the page is currently stuck on a captcha page. If so, pause 
# the scraper until user has manually completed the captcha requirements.
def check_for_captcha(driver):
    if _is_element_displayed(driver, "captcha-container", "class"):
        print("\nCAPTCHA!\n"\
              "Manually complete the captcha requirements.\n"\
              "Once that's done, if the program was in the middle of scraping "\
              "(and is still running), it should resume scraping after ~30 seconds.")
        _pause_for_captcha(driver)

def close_connection(driver):
    driver.quit()