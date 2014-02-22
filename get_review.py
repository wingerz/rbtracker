import argparse
import json
import os
import os.path
import pprint
import sys
import time

from rbtools.api.errors import APIError
from rbtools.api.client import RBClient

import rb_util

if __name__ == "__main__":
    review_id = sys.argv[1]

    parser = argparse.ArgumentParser(description='Grab some reviewboard info.')
    parser.add_argument('--start', type=int,
                   help='review id to start with')
    parser.add_argument('--limit', type=int, default=10,
                   help='number of reviews to pull')
    parser.add_argument('--output', type=str, default="data",
                   help='output directory to write to')
    parser.add_argument('--sleepms', type=int, default=500,
                   help='ms to sleep between pulling each review')

    params = parser.parse_args()

    if not os.path.isdir(params.output):
        os.mkdir(params.output)

    review_id = params.start
    sleep_time = params.sleepms / 1000.
    root = RBClient('https://reviewboard.yelpcorp.com', cookie_file='cookie.txt').get_root()
    errors = []
    for _ in xrange(params.limit):
        if review_id <= 0:
            break
        
        print "getting review %s" % review_id

        review_request = rb_util.get_review_data(root, review_id, sleep_time=sleep_time)
        if not review_request:
            errors.append(review_id)
        else:    
            with open(os.path.join(params.output, "%s.json" % review_id), 'w') as f:
                print >>f, json.dumps(review_request)
            
        time.sleep(sleep_time)
        review_id -= 1
    pprint.pprint(errors)
