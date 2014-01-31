rbtracker
=========

reviewboard tracker

To generate a cookie.txt file:

from rbtools.api.client import RBClient
root = RBClient('https://reviewboard.example.com', cookie_file='cookie.txt', username="...", password="...").get_root()
