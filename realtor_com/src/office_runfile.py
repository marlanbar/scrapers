import time
import argparse
import pandas as pd
import office_functions as ol
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

columns = ["office", "phone"]

# Start the scraping.
for idx, term in enumerate(zipcodes):
    time_start = time.time()
    proxies = ol.get_proxies()

    print("Entering search term %s of %s: %s" % 
              (str(idx + args.resume), str(zipcodes_count - 1), term))
    
    raw_data = ol.get_pages(term, proxies)
    print("%s pages of offices found" % str(len(raw_data)))

    # Take the extracted HTML and split it up by individual agent links.
    offices = ol.get_offices(raw_data)

    output_data = []
    for office in offices:
        output_data.append(ol.get_new_obs(office))

    pd.DataFrame(output_data, columns=columns).to_csv(
        args.output + "/{}.csv".format(term), sep="|", header = True,
        index = False, encoding = "UTF-8"
    )

    print("%s offices scraped\n***" % (str(len(output_data))))
    print("--- %s seconds ---" % (time.time() - time_start))