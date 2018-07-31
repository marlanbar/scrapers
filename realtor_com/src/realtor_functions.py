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

import requests
from requests.exceptions import ProxyError

import time
import random
import requests
from lxml.html import fromstring
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# import pdb

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:80]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def init_driver(file_path, proxy):
    # Starting maximized fixes https://github.com/ChrisMuir/Zillow/issues/1
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # options.add_argument("headless")
        options.add_argument('--proxy-server=%s' % proxy)

        driver = webdriver.Chrome(executable_path=file_path, 
                                  chrome_options=options)
        driver.wait = WebDriverWait(driver, 10)
    except ConnectionError:
        raise
    return(driver)

def navigate_to_website(driver, site):
    driver.get(site)
    # Check to make sure a captcha page is not displayed.
    check_for_captcha(driver)

def enter_search_term(driver, search_term):
    if not isinstance(search_term, str):
        search_term = str(search_term)
    try:
        search_bar = driver.wait.until(EC.presence_of_element_located(
            ((By.ID, "searchBox"))))
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, "js-searchButton")))
        search_bar.clear()
        time.sleep(5)
        search_bar.send_keys(search_term)
        time.sleep(5)
        button.click()
        time.sleep(5)
        return(True)
    except WebDriverException:
        print("Something failed...Trying again")
        time.sleep(5)
        check_for_feedback(driver)
        enter_search_term(driver, search_term)
    except (TimeoutException, NoSuchElementException):
        return(False)
    # Check to make sure a captcha page is not displayed.
    check_for_feedback(driver)
    check_for_captcha(driver)


def get_html(driver):
    output = []
    keep_going = True
    pages = 1
    while keep_going:
        # Pull page HTML
        try:
            output.append(driver.page_source)
        except TimeoutException:
            pass
        # Check to see if a "next page" link exists.
        check_for_feedback(driver)
        keep_going = _is_element_displayed(driver, "next", "class")
        last_page = _is_element_displayed(driver, "next-last-page", "class")
        if keep_going and not last_page and pages <= 5:
            try:
                # pdb.set_trace()
                check_for_feedback(driver)
                driver.wait.until(EC.element_to_be_clickable(
                    (By.CLASS_NAME, "next"))).click()
                time.sleep(5)
                pages += 1
                # Check to make sure a captcha page is not displayed.
                check_for_captcha(driver)
            except WebDriverException:
                check_for_feedback(driver)
            except TimeoutException:
                keep_going = False
        else:
            keep_going = False

    return(output)


# Split the raw page source into segments, one for each home listing.
def get_listings(list_obj):
    output = []
    for i in list_obj:
        soup = BeautifulSoup(i, "lxml")
        htmlSplit = soup.find_all('li', {'data-listingid' : re.compile(r".*")})
        output += htmlSplit
    return(output)


def get_street_address(soup_obj):
    try:
        street = soup_obj.find(
            "span", {"itemprop" : "streetAddress"}).get_text().strip()
    except (ValueError, AttributeError):
        street = "NA"
    if _is_empty(street):
        street = "NA"
    return(street)

def get_city(soup_obj):
    try:
        city = soup_obj.find(
            "span", {"itemprop" : "addressLocality"}).get_text().strip()
    except (ValueError, AttributeError):
        city = "NA"
    if _is_empty(city):
        city = "NA"
    return(city)

def get_zipcode(soup_obj):
    try:
        zipcode = soup_obj.find(
            "span", {"itemprop" : "postalCode"}).get_text().strip()
    except (ValueError, AttributeError):
        zipcode = "NA"
    if _is_empty(zipcode):
        zipcode = "NA"
    return(zipcode)

def get_price(soup_obj):
    try:
        price = soup_obj.find("span", {"itemprop": "price"}).get_text()
    except (ValueError, AttributeError):
        price = "NA"
    if _is_empty(price):
        price = "NA"
    price = price.replace(",", "").replace("+", "").replace("$", "")
    return(price)


def get_sqft(soup_obj):
    try:
        sqft = soup_obj.find("li", {"data-label": "property-meta-sqft"}).find("span", {"class":"data-value"}).get_text()
    except (ValueError, AttributeError):
        sqft = "NA"
    if _is_empty(sqft):
        sqft = "NA"
    sqft = sqft.replace(",", "")
    return(sqft)

def get_bedrooms(soup_obj):
    try:
        beds = soup_obj.find("li", {"data-label": "property-meta-beds"}).find("span", {"class":"data-value meta-beds"}).get_text()
    except (ValueError, AttributeError):
        beds = "NA"
    if _is_empty(beds):
        beds = "NA"
    return(beds)

def get_bathrooms(soup_obj):
    try:
        baths = soup_obj.find("li", {"data-label": "property-meta-baths"}).find("span", {"class":"data-value"}).get_text()
    except (ValueError, AttributeError):
        baths = "NA"
    if _is_empty(baths):
        baths = "NA"
    return(baths)


def get_coordinate(soup_obj, coordinate):
    try:
        coord = soup_obj.find("meta", {"itemprop": coordinate})["content"]
    except (ValueError, AttributeError):
        coord = "NA"
    if _is_empty(coord):
        coord = "NA"
    return(coord)

def get_broker(soup_obj):
    try:
        broker = soup_obj.find("span", {"data-label": "property-broker"}).get_text()
    except (ValueError, AttributeError):
        broker = "NA"
    if _is_empty(broker):
        broker = "NA"
    return(broker)

def get_property_type(soup_obj):
    try:
        prop_type = soup_obj.find("span", {"class": "srp-property-type"}).get_text()
    except (ValueError, AttributeError):
        prop_type = "NA"
    if _is_empty(prop_type):
        prop_type = "NA"
    return(prop_type)

def get_agent_name(soup_obj, proxy):
    try:
    
        link = soup_obj.find("div", {'data-label':'property-photo'}).find("a")["href"]
        url = "https://www.realtor.com" + link
        user_agent = UserAgent().random
        html = requests.get(url, 
            proxies={"http": proxy, "https": proxy}, 
            headers={'User-Agent': user_agent, 'referrer': 'https://google.com'},
            timeout=5)
        house_soup = BeautifulSoup(html.text, "lxml")
        agent_name = house_soup.find("span", {"data-label":"branding-agent-name"}).get_text()
    except (ValueError, AttributeError, TypeError) as err:
        print("Error: {}".format(err))
        open("raw_data/{}".format(link.split("/")[2]), "w").write(html.text)
        agent_name = "NA"
    except ProxyError:
        print("Proxy Error")
        agent_name = "NA"
    except Exception as e:
        print("Error: ", e)
        agent_name = "NA"
    # print("Getting agent name: {}\n".format(agent_name) + 
    #         "PROXY: {}\n".format(proxy) +
    #         "User-Agent: {}".format(user_agent))
    print("Getting agent name: {}".format(agent_name))
    return(agent_name)

def get_new_obs(soup, proxy):
    new_obs = []
    new_obs.append(get_street_address(soup))
    new_obs.append(get_zipcode(soup))
    new_obs.append(get_city(soup))
    new_obs.append(get_price(soup))
    new_obs.append(get_sqft(soup))
    new_obs.append(get_bedrooms(soup))
    new_obs.append(get_bathrooms(soup))
    new_obs.append(get_property_type(soup))
    new_obs.append(get_coordinate(soup, "latitude"))
    new_obs.append(get_coordinate(soup, "longitude"))
    new_obs.append(get_broker(soup))
    new_obs.append(get_agent_name(soup, proxy))
    return new_obs


def test_for_no_results(driver):
    no_results_1 = _is_element_displayed(driver, "no_properties_found", "id")
    no_results_2 = _is_element_displayed(driver, 
        "//*[contains(text(), 'There are no homes in this area')]", "xpath")
    no_results_3 = _is_element_displayed(driver, 
        "//*[contains(text(), 'No results found for your search.')]", "xpath")
    return(no_results_1 or no_results_2 or no_results_3)

def check_for_feedback(driver):
    if _is_element_displayed(driver, "div[id='acsMainInvite']", "css"):
        driver.wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="acsMainInvite"]/div/a[1]'))).click()
        time.sleep(5)

# Check to see if the page is currently stuck on a captcha page. If so, pause 
# the scraper until user has manually completed the captcha requirements.
def check_for_captcha(driver):
    if _is_element_displayed(driver, "captcha-container", "class"):
        print("\nCAPTCHA!\n"\
              "Manually complete the captcha requirements.\n"\
              "Once that's done, if the program was in the middle of scraping "\
              "(and is still running), it should resume scraping after ~30 seconds.")
        _pause_for_captcha(driver)

# If captcha page is displayed, this function will run indefinitely until the 
# captcha page is no longer displayed (checks for it every 30 seconds).
# Purpose of the function is to "pause" execution of the scraper until the 
# user has manually completed the captcha requirements.
def _pause_for_captcha(driver):
    while True:
        time.sleep(30)
        if not _is_element_displayed(driver, "captcha-container", "class"):
            break

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

# Helper function for testing if an object is "empty" or not.
def _is_empty(obj):
    if any([len(obj) == 0, obj == "null", obj.isspace()]):
        return(True)
    else:
        return(False)

def close_connection(driver):
    driver.quit()
