import argparse
import datetime
import json
import pprint

fmt = '%Y-%m-%d %H:%M:%S'

def total_days(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 / 86400.

SIMPLE_KEYS = ('branch', 'bugs_closed', 'review_id', 'status', 'target_groups', 'target_people', 'time_added', 'last_updated')

def extract_review_properties(review_request):
    data = {}
    for key in SIMPLE_KEYS:
        data[key] = review_request[key]

    data['max_files_touched'] = 0
    if review_request['diffs']:
        data['max_files_touched'] = max(len(diff['files']) for diff in review_request['diffs'])
    data['num_diffs'] = len(review_request['diffs'])
    data['num_reviews'] = len(review_request['reviews'])

    data['max_comments'] = 0
    if review_request['reviews']:
        data['max_comments'] = max(review['comment_count'] for review in review_request['reviews'])

    data['days_until_first_review'] = 0
    data['days_until_first_shipit'] = 0
    data['days_until_last_shipit'] = 0

    if review_request['diffs'] and review_request['reviews']:
        first_review = datetime.datetime.strptime(review_request['reviews'][0]['timestamp'], fmt)
        first_diff_posted = datetime.datetime.strptime(review_request['diffs'][0]['timestamp'], fmt)

        data['days_until_first_review'] = total_days(first_review - first_diff_posted)
        
        shipits = filter(lambda review: review['ship_it'], review_request['reviews'])
        if shipits:
            first_shipit = datetime.datetime.strptime(shipits[0]['timestamp'], fmt)
            data['days_until_first_shipit'] = total_days(first_shipit - first_diff_posted)
            last_shipit = datetime.datetime.strptime(shipits[-1]['timestamp'], fmt)
            data['days_until_last_shipit'] = total_days(last_shipit - first_diff_posted)
    return data

def summarize(review_summaries, limit=25):
    interesting_keys = ('days_until_first_review', 'days_until_first_shipit', 'days_until_last_shipit', 'max_comments', 'num_diffs', 'num_reviews', 'max_files_touched')

    summary = {}
    for key in interesting_keys:
        summary[key] = sorted(review_summaries, key=lambda item: item[key], reverse=True)[:limit]
    return summary
    
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
        lines = f.readlines()

    review_summaries = []
        
    for i, line in enumerate(lines):
        if limit and i >= limit:
            break
        review = json.loads(line)
        review_data = extract_review_properties(review)
        review_summaries.append(review_data)

    summary = summarize(review_summaries)
    pprint.pprint(summary)
