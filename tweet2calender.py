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
    if res.status_code == 200:
        r = json.loads(res.text)
        contents = r['text']
        date = r['created_at']
        return contents, date
    return False, False #2 returns or 1 returns ???

def make_events(contents, date, creds):
    if contents != False and date != False:
        date_jst = parser.parse(date).astimezone(timezone('Asia/Tokyo'))
        date_year, date_month, date_day = date_jst.year, date_jst.month, date_jst.day

        body = {
            # 予定のタイトル
            'summary': contents,
            # 予定の開始時刻
            'start': {
                'dateTime': datetime(date_year, date_month, date_day, 10, 00).isoformat(),
                'timeZone': 'Japan'
            },
            # 予定の終了時刻
            'end': {
                'dateTime': datetime(date_year, date_month, date_day, 12, 00).isoformat(),
                'timeZone': 'Japan'
            },
        }
        service = build('calendar', 'v3', credentials=creds)

        event = service.events().insert(calendarId='nekodaisuki169@gmail.com',body=body).execute()

        print("success")

        return True
    return False

def get_mytweet_list():
    url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
    params = {'screen_name': user_id, 'count': 4000, 'include_rts': False}#not incliude RTs
    res = twitter.get(url, params=params)
    if res.status_code == 200:
        r = json.loads(res.text)#json 型 to dictionary 型
        return [tweet["id"] for tweet in r ]

def isexist_tweetids(id):
    path = '/Users/sota/programing/python/tweetids.txt'
    with open(path, mode = 'r') as f:
        exsist_ids_str = [s.strip() for s in f.readlines()]
        exsist_ids = [int(i) for i in exsist_ids_str]
        if id in exsist_ids:
            return False
        else:
            with open(path, mode = 'a') as g:
                g.write(str(id) + "\n")
                return True

def checkLimit():
        url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        params = {'screen_name': user_id, 'count': 1}
        res = twitter.get(url, params = params)

        if res.status_code != 200:
            raise Exception('Twitter API error %d' % res.status_code)

        remaining, reset = res.headers['X-Rate-Limit-Remaining'], res.headers['X-Rate-Limit-Reset']
        print(remaining)
        print(reset)
        if (remaining == 0) or (res.status_code == 429):
            print("sleep for regettting tweet")
            waitUntilReset(reset)
        else:
            pass

def waitUntilReset(reset):
    '''
    reset 時刻まで sleep
    '''
    seconds = int(reset) - time.mktime(datetime.now().timetuple())
    seconds = max(seconds, 0)
    print ('\n     =====================', flush = True)
    print ('     == waiting %d sec ==' % seconds, flush = True)
    print ('     =====================', flush = True)

    time.sleep(seconds + 10)

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)


    while True:
        ids = get_mytweet_list()
        if ids :
            for id in ids:
                checkLimit()
                if isexist_tweetids(id):
                    print(id)
                    contents, date = get_tweets_contents(id)
                    make_events(contents, date, creds)
                else:
                    print("exist" + str(id))
        print("end")
        time.sleep(300)

if __name__ == "__main__":
    main()
