import time
import argparse
import pandas as pd
import listings_functions
import random
from itertools import repeat
from multiprocessing.dummy import Pool

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-z", "--zipcode", required=True, help="zipcodes file")
ap.add_argument("-o", "--output", required=True, help="output folder")
ap.add_argument("-r", "--resume", required=False, default=0, type=int, help="start line of zipcode table")
args = ap.parse_args()

zipcodes = pd.read_csv(args.zipcode, dtype={"zipcode": object})
zipcodes_count = zipcodes.shape[0]
zipcodes = zipcodes.iloc[args.resume:].zipcode.values.tolist()

columns = ["address", "city", "zip", "price", "sqft", "bedrooms", 
           "bathrooms", "property_type", "latitude", "longitude", "broker", "agent_name"]

# Start the scraping.
for idx, term in enumerate(zipcodes):
    time_start = time.time()
    proxies = listings_functions.get_proxies()

    print("Entering search term %s of %s: %s" % 
              (str(idx + args.resume), str(zipcodes_count - 1), term))
    
    raw_data = listings_functions.get_pages(term, proxies)
    print("%s pages of listings found" % str(len(raw_data)))

    # Take the extracted HTML and split it up by individual home listings.
    listings = listings_functions.get_listings(raw_data)

    with Pool(8) as p:
        output_data = p.starmap(listings_functions.get_new_obs, 
            list(zip(listings, repeat(proxies))))

    pd.DataFrame(output_data, columns = columns).to_csv(
        args.output + "/{}.csv".format(term), sep="|", header = True,
        index = False, encoding = "UTF-8"
    )

    print("%s home listings scraped\n***" % str(len(output_data)))
    print("--- %s seconds ---" % (time.time() - time_start))