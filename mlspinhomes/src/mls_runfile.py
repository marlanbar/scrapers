import time
import argparse
import pickle
import pandas as pd
from bs4 import BeautifulSoup
import mls_functions as ml

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-z", "--zipcode", required=True, help="zipcodes file")
ap.add_argument("-t", "--type", required=True, help="agent/office")
ap.add_argument("-o", "--output", required=True, help="output folder")
ap.add_argument("-r", "--resume", required=False, default=0, type=int, help="start line of zipcode table")
args = ap.parse_args()

zipcodes = pd.read_csv(args.zipcode, dtype={"zipcode": object})
zipcodes_count = zipcodes.shape[0]

zipcodes = zipcodes.iloc[args.resume:]
st = zipcodes.zipcode.values.tolist()
num_search_terms = len(st)

driver = ml.init_driver("/Users/mlangberg/venv3/bin/chromedriver")
ml.navigate_to_website(driver, "http://www.mlspinhomes.com")


if args.type == "agent":
    ml.click_find_agent(driver)
elif args.type == "office":
    ml.click_find_office(driver)
else:
    print("Error: Wrong type specified. Options: agent/office")
    exit()

columns = ["name", "address", "phone", "broker"]

# Start the scraping.
for idx, term in enumerate(st):
    # Initialize list obj that will house all scraped data.
    output_data = []

    # Enter search term and execute search.
    if ml.enter_search_term(driver, term):
        print("Entering search term %s of %s: %s" % 
              (str(idx + args.resume), str(zipcodes_count - 1), term))
    else:
        print("Search term %s failed, moving on to next search term\n***" % 
              str(idx + args.resume))
        continue


    # Check to see if any results were returned from the search.
    # If there were none, move onto the next search.
    if ml.test_for_no_results(driver):
        print("Search %s returned zero results. Moving on to next search\n***" %
              str(term))
        ml.click_edit_search(driver)
        continue


    raw_data = ml.get_html(driver)
    for e, html in enumerate(raw_data, 1):
        with open("raw_data/{}_{}.html".format(term,e), "w") as f:
            f.write(html)

    print("%s pages of listings found" % str(len(raw_data)))


    # Take the extracted HTML and split it up by individual home listings.
    realtors = ml.get_realtors(raw_data)
    print("%s realtors scraped\n***" % str(len(realtors)))

    for soup in realtors:
        new_obs = []
        new_obs.append(ml.get_info(soup, "a",  "ao_results_icon_text A detail-page"))
        new_obs.append(ml.get_info(soup, "div", "ao-address"))
        new_obs.append(ml.get_info(soup, "div", "ao-phone"))
        new_obs.append(ml.get_info(soup, "div", "ao-office"))

        # Append new_obs to list output_data.
        output_data.append(new_obs)

    pd.DataFrame(output_data, columns = columns).to_csv(
        args.output + "/{}.csv".format(term), sep="|", header = True,
        index = False, encoding = "UTF-8"
    )
    ml.click_edit_search(driver)

# Close the webdriver connection.
ml.close_connection(driver)