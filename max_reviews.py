import argparse
from collections import defaultdict
import json
import pprint

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Grab some reviewboard info.')
    parser.add_argument('--inputfile', type=str, default="data.json",
                   help='input directory to read from')
    parser.add_argument('--limit', type=int, default=None,
                   help='number of lines to read')
    params = parser.parse_args()

    filename = params.inputfile
    limit = params.limit

    with open(filename) as f:
        lines = reversed(f.readlines())

    summary = {}

    review_counts = defaultdict(list)
    shipits = defaultdict(list)
    review_request_counts = defaultdict(list)
    
    for i, line in enumerate(lines):
        if limit and i >= limit:
            break
        review_request = json.loads(line)

        review_request_counts[review_request['username']].append(review_request['time_added'])
        people = review_request['target_people']
        for person in people:
            review_counts[person].append(review_request['time_added'])

        people_who_shipped = set()
        for review in review_request['reviews']:
            
            if review['ship_it'] and review['username'] not in people_who_shipped:
                shipits[review['username']].append(review['timestamp'])
                people_who_shipped.add(review['username'])
        

    shipits_sorted = sorted(shipits.items(), key=lambda item: len(item[1]), reverse=True)
    pprint.pprint([(i[0], len(i[1])) for i in shipits_sorted[:50]])

    reviews_sorted = sorted(review_counts.items(), key=lambda item: len(item[1]), reverse=True)
    pprint.pprint([(i[0], len(i[1])) for i in reviews_sorted[:50]])

    requests_sorted = sorted(review_request_counts.items(), key=lambda item: len(item[1]), reverse=True)
    pprint.pprint([(i[0], len(i[1])) for i in requests_sorted[:50]])
