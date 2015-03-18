# Needed to use Google API webpanel to make an API Access account 
# with Application type: Device.
#
# How to call from CLI:
# python uploadYouTube.py --file ~/Movies/Timelapse/Hamilton/20150212.mov --title "Timelapse February 12th, 2015" --keywords "timelapse,san francisco,skyline,tenderloin"
#
# Tagged w/ 'timelapse' playlist: https://www.youtube.com/playlist?list=PLfZMIIdLd0glnzad2XHgP6fOq-AOfy_88
#
#!/usr/bin/python

# TODO: progress bar: http://stackoverflow.com/questions/13200607/progress-bar-for-upload-browser-base

import httplib
import httplib2
import os
import random
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Developers Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
"""% os.path.abspath(os.path.join( os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE) )

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def get_authenticated_service(args):
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
    scope=YOUTUBE_UPLOAD_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))

def initialize_upload(youtube, options):
  tags = None
  if options.keywords:
    tags = options.keywords.split(",")

  body=dict(
    snippet=dict(
      title=options.title,
      description=options.description,
      tags=tags,
      categoryId=options.category
    ),
    status=dict(
      privacyStatus=options.privacyStatus
    ),
    recordingDetails=dict(
      locationDescription=options.location,
      recordingDate=options.date
    )
  )

  # Call the API's videos.insert method to create and upload the video.
  insert_request = youtube.videos().insert(
    part=",".join(body.keys()),
    body=body,
    # The chunksize parameter specifies the size of each chunk of data, in
    # bytes, that will be uploaded at a time. Set a higher value for
    # reliable connections as fewer chunks lead to faster uploads. Set a lower
    # value for better recovery on less reliable connections.
    #
    # Setting "chunksize" equal to -1 in the code below means that the entire
    # file will be uploaded in a single HTTP request. (If the upload fails,
    # it will still be retried where it left off.) This is usually a best
    # practice, but if you're using Python older than 2.6 or if you're
    # running on App Engine, you should set the chunksize to something like
    # 1024 * 1024 (1 megabyte).
    media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
  )

  return resumable_upload(insert_request)

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print "Uploading file..."
      status, response = insert_request.next_chunk()
      if 'id' in response:
        print "Video id '%s' was successfully uploaded." % response['id']
        print "url: https://www.youtube.com/watch?v={0}".format(response['id'])
        return response['id']
      else:
        exit("The upload failed with an unexpected response: %s" % response)
        return 0
    except HttpError, e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                             e.content)
      else:
        raise
    except RETRIABLE_EXCEPTIONS, e:
      error = "A retriable error occurred: %s" % e

    if error is not None:
      print error
      retry += 1
      if retry > MAX_RETRIES:
        exit("No longer attempting to retry.")
        return 0

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print "Sleeping %f seconds and then retrying..." % sleep_seconds
      time.sleep(sleep_seconds)

if __name__ == '__main__':
  argparser.add_argument("--file", required=True, help="Video file to upload")
  argparser.add_argument("--title", help="Video title", default="Test Title")
  argparser.add_argument("--description", help="Video description",
    default="Test Description")
  argparser.add_argument("--category", default="19",  # 19 is Travel & Events
    help="Numeric video category. " +
      "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
  argparser.add_argument("--keywords", help="Video keywords, comma separated",
    default="")
  argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES,
    default=VALID_PRIVACY_STATUSES[0], help="Video privacy status.")
  argparser.add_argument("--location", default="test", help="Name of recording location")
  argparser.add_argument("--date", default="", help="Date video originally recorded")
  args = argparser.parse_args()

  if not os.path.exists(args.file):
    exit("Please specify a valid file using the --file= parameter.")

  youtube = get_authenticated_service(args)
  try:
    youtube_id = initialize_upload(youtube, args)

    # change local video name
    root, ext = os.path.splitext(args.file)
    newName = root + "_" + youtube_id + ext
    print("adding Youtube ID to video filename: {0}".format(newName))
    os.rename(args.file, newName);
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)

# response: {u'snippet': {u'thumbnails': {u'default': {u'url': u'https://i.ytimg.com/vi/0Hn4a5L_PBg/default.jpg', u'width': 120, u'height': 90}, u'high': {u'url': u'https://i.ytimg.com/vi/0Hn4a5L_PBg/hqdefault.jpg', u'width': 480, u'height': 360}, u'medium': {u'url': u'https://i.ytimg.com/vi/0Hn4a5L_PBg/mqdefault.jpg', u'width': 320, u'height': 180}}, u'title': u'Timelapse Tuesday March 10, 2015', u'localized': {u'description': u'Test Description', u'title': u'Timelapse Tuesday March 10, 2015'}, u'channelId': u'UCShSYFmBZt99fG0xfzBf7zw', u'publishedAt': u'2015-03-11T10:35:16.000Z', u'liveBroadcastContent': u'none', u'channelTitle': u'Todd Anderson', u'categoryId': u'22', u'tags': [u'timelapse', u'san francisco', u'skyline', u'tenderloin'], u'description': u'Test Description'}, u'status': {u'publicStatsViewable': True, u'privacyStatus': u'public', u'uploadStatus': u'uploaded', u'license': u'youtube', u'embeddable': True}, u'kind': u'youtube#video', u'etag': u'"43qFkeEQBKio26KDSq1ZQMzjhSo/bjgC7YQ9xZ0CGqRClcjTZxTy-JU"', u'id': u'0Hn4a5L_PBg'}
