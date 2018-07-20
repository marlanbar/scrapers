import time
import argparse
import pickle
import pandas as pd
from bs4 import BeautifulSoup
import realtor_functions as rl

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-z", "--zipcode", required=True, help="zipcodes file")
ap.add_argument("-o", "--output", required=True, help="output folder")
ap.add_argument("-r", "--resume", required=False, default=0, type=int, help="start line of zipcode table")
args = ap.parse_args()

zipcodes = pd.read_csv(args.zipcode, dtype={"zipcode": object})
zipcodes_count = zipcodes.shape[0]

zipcodes = zipcodes.iloc[args.resume:]
st = zipcodes.zipcode.values.tolist()
num_search_terms = len(st)

driver = rl.init_driver("/Users/mlangberg/venv3/bin/chromedriver")
rl.navigate_to_website(driver, "http://www.realtor.com")

columns = ["address", "city", "zip", "price", "sqft", "bedrooms", 
           "bathrooms", "property_type", "latitude", "longitude", "broker"]

# Start the scraping.
for idx, term in enumerate(st):
    # Initialize list obj that will house all scraped data.
    output_data = []

    # Enter search term and execute search.
    if rl.enter_search_term(driver, term):
        print("Entering search term %s of %s: %s" % 
              (str(idx + args.resume), str(zipcodes_count - 1), term))
    else:
        print("Search term %s failed, moving on to next search term\n***" % 
              str(idx + args.resume))
        continue

    # Check to see if any results were returned from the search.
    # If there were none, move onto the next search.
    if rl.test_for_no_results(driver):
        print("Search %s returned zero results. Moving on to next search\n***" %
              str(term))
        continue

    raw_data = rl.get_html(driver)
    # for e, html in enumerate(raw_data, 1):
    #     with open("raw_data/{}_{}.html".format(term,e), "w") as f:
    #         f.write(html)

    print("%s pages of listings found" % str(len(raw_data)))


    # Take the extracted HTML and split it up by individual home listings.
    listings = rl.get_listings(raw_data)
    print("%s home listings scraped\n***" % str(len(listings)))

    for soup in listings:
        new_obs = []
        new_obs.append(rl.get_street_address(soup))
        new_obs.append(rl.get_city(soup))
        new_obs.append(rl.get_zipcode(soup))
        new_obs.append(rl.get_price(soup))
        new_obs.append(rl.get_sqft(soup))
        new_obs.append(rl.get_bedrooms(soup))
        new_obs.append(rl.get_bathrooms(soup))
        new_obs.append(rl.get_property_type(soup))
        new_obs.append(rl.get_coordinate(soup, "latitude"))
        new_obs.append(rl.get_coordinate(soup, "longitude"))
        new_obs.append(rl.get_broker(soup))

        # Append new_obs to list output_data.
        output_data.append(new_obs)

    pd.DataFrame(output_data, columns = columns).to_csv(
        args.output + "/{}.csv".format(term), sep="|", header = True,
        index = False, encoding = "UTF-8"
    )

# Close the webdriver connection.
rl.close_connection(driver)