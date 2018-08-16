import re
import time
import requests
import random
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
    proxy = random.sample(proxies, 1)[0]
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
    url_base = "https://www.realtor.com/realestateagents/"
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

def get_agents_urls(list_obj):
    prefix = "https://www.realtor.com/"
    urls = []
    for soup in list_obj:
        urls += [prefix + item["data-url"] for item in soup.find_all('div', {'class' : 'agent-list-card clearfix'})]
    return urls

def get_agent_name(soup):
    try:
        name = soup.find("span", {"class":"agent-name"}).get_text().split(",")[0].strip()
    except (ValueError, AttributeError, TypeError):
        name = "NA"
    return name.replace("\"", "").strip()

def get_phone(soup):
    try:
        phone = soup.find("span", {"itemprop":"telephone"}).get_text()
    except (ValueError, AttributeError):
        phone = "NA"
    return phone.replace("\"", "").strip()

def get_agency(soup):
    try:
        agency = soup.find("span", {"class": "brokerage-title"})["content"]
    except (ValueError, AttributeError, TypeError):
        agency = "NA"
    return agency.replace("\"", "").strip()

def get_houses(soup):
    houses = []
    house_soups = soup.find_all(attrs={"data-prop-full-address":True})
    for house_soup in house_soups:
        house = []
        house.append(house_soup["data-prop-full-address"])
        house.append(house_soup["data-prop-lat"])
        house.append(house_soup["data-prop-long"])
        house.append(house_soup["data-prop-date"])
        house.append(house_soup["data-prop-stats-text"])
        house.append(house_soup["data-prop-bed-bath"])
        house.append(house_soup["data-prop-price"].replace(",", "").replace("$", ""))
        # If the house is still on sale this field does not exist.
        try:
            house.append(house_soup["data-prop-presented"].split("Worked with ")[1])
        except:
            house.append("NA")
        houses.append(house)
    return houses

def get_new_obs(url, proxies):
    new_obs = []
    try:
        html = get_html(url, proxies)
    except RequestException:
        return new_obs
    soup = BeautifulSoup(html, "lxml")
    agent_name = get_agent_name(soup)
    phone = get_phone(soup)
    houses = get_houses(soup)
    agency = get_agency(soup)
    for house in houses:
        new_obs.append([agent_name, phone, agency] + house)
    return new_obs

def flatten(list_obj):
    f = lambda z: [x for y in z for x in y]
    return f(list_obj)

