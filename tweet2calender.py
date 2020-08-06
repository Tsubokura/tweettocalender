import os.path
import urllib.request
import json
import env
import sys
import pickle
import time

from requests_oauthlib import OAuth1Session
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pytz import timezone
from dateutil import parser

user_id = env.USER_ID
CONSUMER_KEY = env.CONSUMER_KEY
CONSUMER_SECRET = env.CONSUMER_SECRET
ACCESS_TOKEN = env.ACCESS_TOKEN
ACCESS_TOKEN_SECRET = env.ACCESS_TOKEN_SECRET
twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_tweets_contents(id):
    url = "https://api.twitter.com/1.1/statuses/show.json"
    res = twitter.get(url, params={'id': id})
    rimit_tweet = res.headers['X-Rate-Limit-Remaining']
    rimitime_tweet = res.headers['X-Rate-Limit-Reset']
    print("tweet_limit %s" %rimit_tweet)

    if rimit_tweet == "0":
        reset_seconds = float(rimitime_tweet) - time.mktime(datetime.now().timetuple())
        reset_seconds = max(reset_seconds, 0)
        print("gettweets sleep in %s seconds" %reset_seconds)
        time.sleep(reset_seconds + 10)

    if res.status_code == 200:
        r = json.loads(res.text)
        contents = r['text']
        date = r['created_at']
        return contents, date
    return False, False #2 returns or 1 returns ???

def isexist_tweetids(id):
    path = '/Users/sota/programing/python/tweettocalender/tweetids.txt'
    with open(path, mode = 'r') as f:
        exsist_ids_str = [s.strip() for s in f.readlines()]
        exsist_ids = [int(i) for i in exsist_ids_str]
        if id in exsist_ids:
            return False
        else:
            with open(path, mode = 'a') as g:
                g.write(str(id) + "\n")
                return True

def make_events(contents, date, creds):
    if contents != False and date != False:
        date_jst = parser.parse(date).astimezone(timezone('Asia/Tokyo'))
        date_year, date_month, date_day = date_jst.year, date_jst.month, date_jst.day

        body = {
            'summary': contents,
            'start': {
                'dateTime': datetime(date_year, date_month, date_day, 10, 00).isoformat(),
                'timeZone': 'Japan'
            },
            'end': {
                'dateTime': datetime(date_year, date_month, date_day, 12, 00).isoformat(),
                'timeZone': 'Japan'
            },
        }

        service = build('calendar', 'v3', credentials=creds)
        event = service.events().insert(calendarId='nekodaisuki169@gmail.com',body=body).execute()
        return True

    return False

def get_mytweet_list(maxid):
    url = "https://api.twitter.com/1.1/statuses/user_timeline.json"

    if maxid == None:
        params = {'screen_name': user_id, 'count': 200, 'include_rts': False}#not incliude RTs
    else:
        params = {'screen_name': user_id, 'count': 200, 'include_rts': False, "max_id":maxid}

    res = twitter.get(url, params=params)
    rimit_tweetlist = res.headers['X-Rate-Limit-Remaining']
    rimitime_tweetlist = res.headers['X-Rate-Limit-Reset']
    print("tweet_limitlist %s" %rimit_tweetlist)

    if rimit_tweetlist == "0":
        reset_seconds = float(rimitime_tweetlist) - time.mktime(datetime.now().timetuple())
        reset_seconds = max(reset_seconds, 0)
        print("gettweetlist sleep in %s seconds" %reset_seconds)
        time.sleep(reset_seconds + 10)

    if res.status_code == 200:
        r = json.loads(res.text)#json 型 to dictionary 型
        return [tweet["id"] for tweet in r ]

def main():
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)#解読したい

    old_id = None
    while True:
        ids = get_mytweet_list(old_id)
        old_id = ids[-1]
        print(old_id)

        if ids :
            for id in ids:
                if isexist_tweetids(id):
                    contents, date = get_tweets_contents(id)
                    make_events(contents, date, creds)
                    print("%s id tweet to calender" %id)
                else:
                    print("%s id exist in calender " + %id)
                    print("tweet to calender process end")
                    sys.exit(0)

if __name__ == "__main__":
    main()
