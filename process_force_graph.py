import argparse
from collections import defaultdict
import datetime
import json
import os


# If I do a lot more of these, should create a class to allow
# should_show_edge and user_to_group to be subclassed.

def should_show_edge(review_request, review):
    # last year, relevent to baz
    return (is_review_in_date_range(review_request, review,
                                    (datetime.datetime.now() - datetime.timedelta(days=540),
                                     None))
            and is_baz(review_request, review))

def is_baz(review_request, review):
    distinctive_phrases = ['baz']
    for phrase in distinctive_phrases:
        if any(phrase in review_request[property] for property in ['summary', 'description', 'testing_done', 'branch']):
            return True

    return False
    
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


def username_to_group(username, user_to_team):
    if not user_to_team:
        return 1

    if not user_to_team.get(username):
        return 1

    if user_to_team[username] == 'Consumer':
        return 2
    else:
        return 1

def make_undirected_graph(edges):
    new_edges = defaultdict(lambda:defaultdict(int))
    for src, dest_count in edges.iteritems():
        for dest, count in dest_count.iteritems():
            if src < dest:
                new_edges[src][dest] += count
            else:
                new_edges[dest][src] += count
    return new_edges
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Grab some reviewboard info.')
    parser.add_argument('--inputfile', type=str, default="reviews.json",
                   help='reviews input file, one review per line')
    parser.add_argument('--teamfile', type=str, default=None,
                   help='team file, maps team name to usernames')
    parser.add_argument('--outputfile', type=str, default="static/reviews.json",
                   help='output file to write to')
    params = parser.parse_args()

    params.inputfile


    people = set()
    edges = defaultdict(lambda: defaultdict(int))

    relevant_review_requests = []
    relevant_review_ids = set()

    user_to_team = {}
    if params.teamfile:
        with open(params.teamfile, 'r') as f:
            teams = json.loads(f.readline())
        for team_name, members in teams.iteritems():
            for member in members:
                user_to_team[member] = team_name
    
    with open(params.inputfile, 'r') as f:
        lines = f.readlines()
        for line in lines:
            review_request = json.loads(line)

            for review in review_request['reviews']:
                if should_show_edge(review_request, review):
                    if review_request['review_id'] not in relevant_review_ids:
                        relevant_review_requests.append(review_request)
                        relevant_review_ids.add(review_request['review_id'])
                    
                    requestor = review_request['username']
                    reviewer = review['username']
                    people.add(requestor)
                    people.add(reviewer)
                    edges[reviewer][requestor] += 1


    edges = make_undirected_graph(edges)
                    
    output = {}

    sorted_people = sorted(list(people))
    people_to_id = dict((person, i) for i, person in enumerate(sorted_people))

    output['nodes'] = [{"name": person, "group": username_to_group(person, user_to_team), "reviews": len(edges[person])} for person in sorted_people]
    output['links'] = []
    for reviewer, requestor_count in edges.iteritems():
        for requestor, count in requestor_count.iteritems():
            output['links'].append({
                "source": people_to_id[reviewer],
                "target": people_to_id[requestor],
                "value": count,
            })

    # summary
    print len(relevant_review_requests), ' reviews matched'
    for review in relevant_review_requests:
        print review['review_id'], review['summary']

    with open(params.outputfile, 'w') as f:
        print >>f, json.dumps(output)
