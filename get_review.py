import argparse
import json
import os
import os.path
import pprint
import sys
import time

from rbtools.api.errors import APIError
from rbtools.api.client import RBClient

REVIEW_REQUEST_SIMPLE_KEYS = [
    'status',
    'last_updated',
    'description',
    'testing_done',
    'branch',
    'time_added',
    'summary'
]

REVIEW_REQUEST_LIST_KEYS = [
    ('target_people', lambda item: item.title),
    ('target_groups', lambda item: item.title),
    ('bugs_closed', lambda item: item)
]

def get_review_data(root, review_id):
    review_request = root.get_review_request(review_request_id=review_id)
        
    data = {
        'review_id': review_id,
    }
    for key in REVIEW_REQUEST_SIMPLE_KEYS:
        data[key] = review_request[key]
    for key, f in REVIEW_REQUEST_LIST_KEYS:
        data[key] = [f(item) for item in review_request[key]]

    username = review_request.get_submitter()['username']
    data['username'] = username
        
    # get changes
    changes = list(review_request.get_changes())
    change_data = []
    for change in changes:
        change_data.append({
            'text': change['text'],
            'id': change['id'],
            'timestamp': change['timestamp'],
        })
    data['changes'] = change_data
        
    # get diffs
    diffs = list(review_request.get_diffs())
    all_diff_data = []
    for diff in diffs:
        diff_data = {
            'id': diff['id'],
            'timestamp': diff['timestamp'],
        }

        files = diff.get_files()
        file_data = []
        for file in files:
            file_data.append({
                'source_file': file['source_file'],
                'dest_file': file['dest_file'],
                'id': file['id']
            })
        diff_data['files'] = file_data
        
        all_diff_data.append(diff_data)

    data['diffs'] = all_diff_data
        
    # get reviews
    reviews = list(review_request.get_reviews())
    review_data = []
    for review in reviews:
        comment_count = review.get_diff_comments(counts_only=True)['count']
        username = review.get_user()['username']
        review_data.append({
            'comment_count': comment_count,
            'ship_it': review['ship_it'],
            'public': review['public'],
            'timestamp': review['timestamp'],
            'id': review['id'],
            'username': username,
        })
    data['reviews'] = review_data
    return data


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
    root = RBClient('https://reviewboard.yelpcorp.com', cookie_file='cookie.txt').get_root()
    errors = []
    for _ in xrange(params.limit):
        print "getting review %s" % review_id

        try:
            review_request = get_review_data(root, review_id)
            with open(os.path.join(params.output, "%s.json" % review_id), 'w') as f:
                print >>f, json.dumps(review_request)
        except APIError, e:
            print "%d: %s" % (review_id, e.rsp)
            errors.append((review_id, e.rsp))
            
        time.sleep(params.sleepms / 1000.)
        review_id -= 1
    pprint.pprint(errors)