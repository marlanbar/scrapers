import time
import argparse
import pickle
import pandas as pd
import realtor_functions as rl
from itertools import cycle
import random
from multiprocessing import Pool

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
proxies = rl.get_proxies()
proxy_pool = cycle(proxies)

proxy = random.sample(proxies, 1)[0]
print("Using PROXY: {}".format(proxy))
driver = rl.init_driver("/Users/mlangberg/venv3/bin/chromedriver", proxy)
rl.navigate_to_website(driver, "http://www.realtor.com")

columns = ["address", "city", "zip", "price", "sqft", "bedrooms", 
           "bathrooms", "property_type", "latitude", "longitude", "broker", "agent_name"]

# Start the scraping.
for idx, term in enumerate(st):
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

    with Pool(10) as p:
        output_data = p.starmap(rl.get_new_obs, 
            [(soup, next(proxy_pool)) for soup in listings])    

    pd.DataFrame(output_data, columns = columns).to_csv(
        args.output + "/{}.csv".format(term), sep="|", header = True,
        index = False, encoding = "UTF-8"
    )

# Close the webdriver connection.
rl.close_connection(driver)