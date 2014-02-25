import datetime
import json
import pprint
import time

from rbtools.api.client import RBClient

import rb_util
            
def summarize_review_info(review_info):
    first_diff = request_info['diffs'][0]
    first_diff_datetime = datetime.datetime.strptime(first_diff['timestamp'], rb_util.DATETIME_FORMAT)
    last_diff = request_info['diffs'][-1]
    last_diff_datetime = datetime.datetime.strptime(last_diff['timestamp'], rb_util.DATETIME_FORMAT)

    review_summary = {
        'id': review_info['review_id'],
        'days_since_request': rb_util.total_days(datetime.datetime.now() - first_diff_datetime),
        'to': request_info['target_people'],
        'to_groups': request_info['target_groups'],
        'from': request_info['username'],
        'summary': request_info['summary'],
        'num_reviews': len(request_info['reviews']),
        'num_diffs': len(request_info['diffs']),
        'max_comments': max([review['comment_count'] for review in request_info['reviews']]) if request_info['reviews'] else 0,
        'max_files': max([len(diff['files']) if diff['files'] else 0 for diff in request_info['diffs']]),
        'shipped': any([review['ship_it'] for review in request_info['reviews']]) if request_info['reviews'] else False,
    }

    days_since_response = None
    if not request_info['reviews']:
        days_since_response = rb_util.total_days(datetime.datetime.now() - last_diff_datetime)
        waiting_for_review = True
    else:
        last_review = request_info['reviews'][-1]
        last_review_datetime = datetime.datetime.strptime(last_review['timestamp'], rb_util.DATETIME_FORMAT)
        if last_diff_datetime > last_review_datetime:
            days_since_response = rb_util.total_days(datetime.datetime.now() - last_diff_datetime)
            waiting_for_review = True
        else:
            days_since_response = rb_util.total_days(datetime.datetime.now() - last_review_datetime)
            waiting_for_review = False

    review_summary['days_since_response'] = days_since_response
    review_summary['waiting_for_review'] = waiting_for_review
    return review_summary


if __name__ == '__main__':
    root = RBClient('https://reviewboard.yelpcorp.com', cookie_file='cookie.txt').get_root()
    request_to_days_elapsed = {}
    long_request = {}

    requests = rb_util._get_paged_data(root.get_review_requests, ship_it=False, status='pending')
    request_summaries = []
    print len(requests)
    
    for i, request in enumerate(requests):
        print "getting request %d" % request['id']
        request_info = rb_util.get_review_data(root, request['id'])
        if not request_info:
            continue
        
        if not request_info['diffs']:
            continue

        request_summary = summarize_review_info(request_info)
        request_summaries.append(request_summary)
        time.sleep(1)

        if i % 10 == 0:
            pprint.pprint(sorted(request_summaries, key=lambda item: item['days_since_request'], reverse=True))
            pprint.pprint(sorted(request_summaries, key=lambda item: item['days_since_response'], reverse=True))


    pprint.pprint(sorted(request_summaries, key=lambda item: item['days_since_request'], reverse=True))
    pprint.pprint(sorted(request_summaries, key=lambda item: item['days_since_response'], reverse=True))

    with open('pending_reviews.json', 'w') as f:
        print >>f, json.dumps(request_summaries)
