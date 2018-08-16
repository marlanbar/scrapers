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
    url_base = "https://www.realtor.com/realestateandhomes-search/"
    while True:
        try:
            html = get_html(url_base + term + "/pg-{}".format(page_number), proxies)
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
        except RequestException as err:
            break
    return pages


def has_next_button(soup):
    button = soup.find("span", {"class", "next"})
    if not button:
        return False
    else:
        return button.find("a")

def no_results(soup):
    return soup.find("h3", {"class": "no-result-subtitle"})

# Split the raw page source into segments, one for each home listing.
def get_listings(list_obj):
    output = []
    for soup in list_obj:
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
        prop_type = soup_obj.find("div", {"class": "property-type"}).get_text()
    except (ValueError, AttributeError):
        prop_type = "NA"
    if _is_empty(prop_type):
        prop_type = "NA"
    return(prop_type)

def get_agent_name(soup_obj, proxies):
    try:
        link = soup_obj.find("div", {"data-label":"property-photo"}).find("a")["href"]
        url = "https://www.realtor.com" + link
        house = get_html(url, proxies, timeout=5, tries=5)
        house_soup = BeautifulSoup(house, "lxml")
        agent_name = house_soup.find("span", {"data-label":"branding-agent-name"}).get_text()
    except (ValueError, AttributeError, TypeError) as err:
        agent_name = "NA"
    except RequestException:
        agent_name = "NA"
        print("Proxy Error")
    except Exception as e:
        agent_name = "NA"
    return(agent_name)

def get_new_obs(soup, proxies):
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
    new_obs.append(get_agent_name(soup, proxies))
    return new_obs

# Helper function for testing if an object is "empty" or not.
def _is_empty(obj):
    if any([len(obj) == 0, obj == "null", obj.isspace()]):
        return(True)
    else:
        return(False)
