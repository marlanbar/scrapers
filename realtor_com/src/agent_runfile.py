import time
import argparse
import pandas as pd
import agent_functions as al
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

columns = ["agent", "phone", "address", "latitude", "longitude", 
    "date", "text", "beds_baths", "price"]

# Start the scraping.
for idx, term in enumerate(zipcodes):
    time_start = time.time()
    proxies = al.get_proxies()

    print("Entering search term %s of %s: %s" % 
              (str(idx + args.resume), str(zipcodes_count - 1), term))
    
    raw_data = al.get_pages(term, proxies)
    print("%s pages of agents found" % str(len(raw_data)))

    # Take the extracted HTML and split it up by individual agent links.
    agents_urls = al.get_agents_urls(raw_data)

    with Pool(8) as p:
        output_data = p.starmap(al.get_new_obs, 
            list(zip(agents_urls, repeat(proxies))))

    agents = pd.DataFrame(al.flatten(output_data), columns = columns).drop_duplicates()

    agents.to_csv(
        args.output + "/{}.csv".format(term), sep="|", header = True,
        index = False, encoding = "UTF-8"
    )

    total_agents = agents.select("agent").drop_duplicates().shape[0]

    print("%s agents scraped\n***" % str(total_agents))
    print("--- %s seconds ---" % (time.time() - time_start))