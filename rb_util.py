import time 
from rbtools.api.errors import APIError

SLEEP_TIME = 1
PAGE_LIMIT = 10
MAX_RESULTS = 200

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

COMMENT_SIMPLE_KEYS = [
    'issue_opened',
    'num_lines',
    'timestamp',
    'text',
    'first_line',
    'issue_status',
]

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
# python2.6 doesn't have this
def total_days(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6 / 86400.


def _get_paged_data(func, page_size=MAX_RESULTS, sleep_time=SLEEP_TIME, **kwargs):
    all_kwargs = kwargs.copy()
    all_kwargs['max_results'] = page_size

    all_results = []

    try:
        results = list(func(*[], **all_kwargs))
    except APIError:
        # Let's just keep going, maybe there weren't any results
        return all_results
        
    all_results.extend(results)
    page = 0
    while len(results) == page_size:
        page += 1

        # don't want to blow up rb
        if page > PAGE_LIMIT:
            break 

        time.sleep(sleep_time)
        all_kwargs['start'] = page * page_size

        results = list(func(*[], **all_kwargs))
        all_results.extend(results)

    return all_results

def get_review_data(root, review_id, sleep_time=SLEEP_TIME):
    try:
        review_request = root.get_review_request(review_request_id=review_id)
    except APIError:
        return None
        
    data = {
        'review_id': review_id,
    }
    for key in REVIEW_REQUEST_SIMPLE_KEYS:
        data[key] = review_request[key]
    for key, f in REVIEW_REQUEST_LIST_KEYS:
        data[key] = [f(item) for item in review_request[key]]

    try:
        username = review_request.get_submitter()['username']
    except:
        username = ''
    data['username'] = username
        
    # get changes
    changes = _get_paged_data(review_request.get_changes, sleep_time=sleep_time)
    change_data = []
    for change in changes:
        change_data.append({
            'text': change['text'],
            'id': change['id'],
            'timestamp': change['timestamp'],
        })
    data['changes'] = change_data
        
    # get diffs
    diffs = _get_paged_data(review_request.get_diffs, sleep_time=sleep_time)
    all_diff_data = []
    for diff in diffs:
        diff_data = {
            'id': diff['id'],
            'timestamp': diff['timestamp'],
        }

        files = _get_paged_data(diff.get_files, sleep_time=sleep_time)
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
    reviews = _get_paged_data(review_request.get_reviews, sleep_time=sleep_time)
    review_data = []
    for review in reviews:
        comment_count = review.get_diff_comments(counts_only=True)['count']

        raw_comments = _get_paged_data(review.get_diff_comments, sleep_time=sleep_time)
        comments = []
        for raw_comment in raw_comments:
            comment = {}
            for key in COMMENT_SIMPLE_KEYS:
                comment[key] = raw_comment[key]

            filediff = raw_comment.get_filediff()
            comment['filediff'] = {
                'source_file': filediff['source_file'],
            }
            comments.append(comment)
        
        try:
            username = review.get_user()['username']
        except APIError:
            username = ''
            
        review_data.append({
            'comment_count': comment_count,
            'ship_it': review['ship_it'],
            'public': review['public'],
            'timestamp': review['timestamp'],
            'id': review['id'],
            'username': username,
            'comments': comments,
        })
    data['reviews'] = review_data

    return data

