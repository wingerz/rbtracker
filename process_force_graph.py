import argparse
from collections import defaultdict
import datetime
import json
import os


def should_show_edge(review_request, review):
    return (is_review_in_date_range(review_request, review,
                                    (datetime.datetime.now() - datetime.timedelta(days=60),
                                     None))
            and is_shipit(review_request, review))

def is_user_involved(review_request, review, username):
    return review_request['username'] == username or review['username'] == username
    

def is_shipit(review_request, review):
    return review['ship_it']
    
def is_review_in_date_range(review_request, review, date_range):
    fmt = '%Y-%m-%d %H:%M:%S'

    review_request_create_time_str = review_request['time_added']
    review_datetime = datetime.datetime.strptime(review_request['time_added'], fmt)

    start_datetime, end_datetime = date_range
    if start_datetime:
        if review_datetime < start_datetime:
            return False
    if end_datetime:
        if review_datetime > end_datetime:
            return False
    return True


def username_to_group(username):
    return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Grab some reviewboard info.')
    parser.add_argument('--inputfile', type=str, default="data.json",
                   help='input directory to read from')
    params = parser.parse_args()

    filename = params.inputfile


    people = set()
    edges = defaultdict(lambda: defaultdict(int))

    with open(filename, 'r') as f:
        
        lines = f.readlines()
        for line in lines:
            review_request = json.loads(line)

            for review in review_request['reviews']:
                if should_show_edge(review_request, review):
                    requestor = review_request['username']
                    reviewer = review['username']
                    people.add(requestor)
                    people.add(reviewer)
                    edges[reviewer][requestor] += 1

                
    output = {}

    sorted_people = sorted(list(people))
    people_to_id = dict((person, i) for i, person in enumerate(sorted_people))

    output['nodes'] = [{"name": person, "group": username_to_group(person), "reviews": len(edges[person])} for person in sorted_people]
    output['links'] = []
    for reviewer, requestor_count in edges.iteritems():
        for requestor, count in requestor_count.iteritems():
            output['links'].append({
                "source": people_to_id[reviewer],
                "target": people_to_id[requestor],
                "value": count,
            })

    print json.dumps(output)
