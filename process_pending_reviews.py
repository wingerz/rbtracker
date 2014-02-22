import argparse
import json
import pprint

def summary_to(review):
    review_to = []
    review_to.extend(review['to'])
    review_to.extend(review['to_groups'])
    return ', '.join(review_to)

def transform_review(review, username_to_group):
    new_review = review.copy()
    new_review['to'] = summary_to(review)
    team = username_to_group.get(new_review['from'], '')
    new_review['team'] = team
    return new_review
    
def summary_line(review):
    return u"{id}: {days:.1f} ({days_since_review:.1f}) {num_diffs} diffs ({files} files) / {num_reviews} ({comments} comments)  reviews: {dev} -> {to}: {summary}".format(
        id=review['id'],
        dev=review['from'],
        to=summary_to(review),
        days=review['days_since_request'],
        days_since_review=review['days_since_response'],
        num_diffs=review['num_diffs'],
        num_reviews=review['num_reviews'],
        summary=review['summary'],
        files=review['max_files'],
        comments=review['max_comments'],
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Summarize pending reviews.')
    parser.add_argument('--inputfile', type=str, default="pending_reviews.json",
                   help='pending review data file')
    parser.add_argument('--teamfile', type=str, default="teams.json",
                   help='team data file')
    parser.add_argument('--outjson', type=str, default="static/pending_reviews_datatable.json",
                   help='json file to output')

    params = parser.parse_args()

    with open(params.inputfile) as f:
        line = f.readline()
    review_summaries = json.loads(line)
    review_summaries_since_response = sorted(review_summaries, key=lambda item: item['days_since_response'], reverse=True)

    with open(params.teamfile) as f:
        line = f.readline()
    groups = json.loads(line)
    username_to_group = {}

    for name, group in groups.iteritems():
        for person in group:
            username_to_group[person] = name
    
    for name, group in groups.iteritems():
        group_reviews = []
        for review in review_summaries:
            if (any([person == review['from'] or person in review['to'] for person in group])):
                group_reviews.append(review)
        print '***', name, ' REVIEWS (%d) (%d devs) ***' % (len(group_reviews), len(group))
        for review in sorted(group_reviews, key=lambda x: x['days_since_request'], reverse=True):
            print summary_line(review).encode('utf-8')

    updated_review_summaries = []
    for review in review_summaries:
        new_summary = transform_review(review, username_to_group)
        updated_review_summaries.append(new_summary)
            
    with open(params.outjson, 'w') as f:
        print >>f, json.dumps({
            'aaData': updated_review_summaries
        })

            