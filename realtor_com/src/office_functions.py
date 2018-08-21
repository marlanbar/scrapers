import re
import time
import requests
import random
import sys
from requests.exceptions import RequestException, HTTPError
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

def random_proxy(proxies):
    if proxies:
        proxy = random.sample(proxies, 1)[0]
    else:
        tries = 10
        while tries != 0:
            proxies = get_proxies()
            if proxies:
                random_proxy(proxies)
            else:
                tries -= 1
                time.sleep(10)
        if tries == 0:
            sys.exit("NO PROXIES FOUND")
    return proxy

def get_html(url, proxies, timeout=5, tries=5):
    while tries != 0:
        proxy = random_proxy(proxies)
        try:
            html = requests.get(url, 
            proxies={"http": proxy, "https": proxy}, 
            headers={'User-Agent': UserAgent().random, 'referrer': 'https://google.com'},
            timeout=timeout)
            html.raise_for_status()
            break
        except HTTPError as err:
            raise
        except RequestException as err:
            tries -= 1
            continue
    if tries == 0: raise RequestException
    return html.text

def get_pages(term, proxies):
    pages = []
    page_number = 1
    url_base = "https://www.realtor.com/realestateagency/"
    while True:
        try:
            html = get_html(url_base + term + "/pg-{}".format(page_number), proxies, tries=10)
            soup = BeautifulSoup(html, "lxml")
            pages.append(soup)
            if no_results(soup):
                print("No results found")
                break
            if has_next_button(soup):
                page_number += 1
                continue
            else:
                break 
        except HTTPError:
            print("Page does not exist")
            break
        except RequestException:
            print("Proxy Error")
            break
    return pages

def no_results(soup):
    return soup.find("h3", {"class": "no-result-subtitle"})

def has_next_button(soup):
    button = soup.find("span", {"class", "next"})
    if not button:
        return False
    else:
        return button.find("a")

# Split the raw page source into segments, one for each home listing.
def get_offices(list_obj):
    output = []
    for soup in list_obj:
        htmlSplit = soup.find_all('div', {'class' : "agent-list-card clearfix"})
        output += htmlSplit
    return(output)

def get_office_name(soup):
    try:
        name = soup.find("div", {"class":"agent-name text-bold"}).get_text()
    except (ValueError, AttributeError, TypeError):
        name = "NA"
    return name.replace("\"", "").strip()

def get_phone(soup):
    try:
        name = soup.find("div", {"itemprop":"telephone"}).get_text()
    except (ValueError, AttributeError, TypeError):
        name = "NA"
    return name.replace("\"", "").strip()

def get_new_obs(soup):
    new_obs = []
    new_obs.append(get_office_name(soup))
    new_obs.append(get_phone(soup))
    return new_obs



