import argparse
from collections import defaultdict
import json
import os


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Grab some reviewboard info.')
    parser.add_argument('--input', type=str, default="data",
                   help='input directory to read from')
    params = parser.parse_args()

    directory = params.input


    people = set()
    edges = defaultdict(lambda: defaultdict(int))

    for filename in os.listdir(directory):
        with open(os.path.join(directory, filename), 'r') as f:
            line = f.readline()
            review_request = json.loads(line)
            requestor = review_request['username']
            people.add(requestor)
            for review in review_request['reviews']:
                reviewer = review['username']
                people.add(reviewer)
                edges[reviewer][requestor] += 1


    output = {}

    sorted_people = sorted(list(people))
    people_to_id = dict((person, i) for i, person in enumerate(sorted_people))

    output['nodes'] = [{"name": person, "group": 1} for person in sorted_people]
    output['links'] = []
    for reviewer, requestor_count in edges.iteritems():
        for requestor, count in requestor_count.iteritems():
            output['links'].append({
                "source": people_to_id[reviewer],
                "target": people_to_id[requestor],
                "value": count,
            })

    print json.dumps(output)
