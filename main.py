import requests
import re
import logging
import time
import pickle
import os.path
import sys

from datetime import date, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

evolve_url = 'https://evolvegenius.com:8090'
booking_endpoint = '/booking/book-class'
member_id = 'YOUR-MEMBER-ID'

classes_id = {
    # Muay Thai monday 9:30
    'Monday': ['f910001f-53a9-4455-a6b2-b981c9d48bef'],
    'Tuesday': [],
    'Wednesday': [],
    'Thursday': [],
    'Friday': [],
    'Saturday': [],
    'Sunday': [],
}


def authenticate():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:79.0) Gecko/20100101 Firefox/79.0'
    }

    r1 = requests.post(evolve_url + '/booking/sessions', data={
        'login': 'test@test.test', 'password': '123456789'}, headers=headers)

    time.sleep(15)
    code = get_otp()
    if code != 0:
        r2 = requests.post(evolve_url + '/booking/sessions', data={'login': 'test@test.test',
                                                                   'password': '123456789', 'verificationCode': code}, headers=headers)
    else:
        print('Interrupting the auth')
        sys.exit()

    return r2.json()


def get_otp():
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
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(
        userId='me', labelIds='Label_6713778025320872363', q='subject:EVOLVE Booking Verification Code. after:'+str(1598177151)).execute()

    if 'messages' in results:
        message = service.users().messages().get(
            userId='me', id=results['messages'][0]['id']).execute()
        code = re.findall('[0-9]+', message['snippet'])[0]
    else:
        print('Couldnt get the OTP message')
        code = 0

    return code


def send_bookings(headers, classes_id, day, date, td=2):
    for event in classes_id[day]:
        print('Attempting to book ' + event)
        data = {
            'eventId': event,
            'eventDate': date + timedelta(days=td),
            'memberId': member_id
        }

        r = requests.post(evolve_url + booking_endpoint,
                          data=data, headers=headers)

        print(r.json())


def main():
    token = authenticate()

    key = 'token'
    if key in token:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:79.0) Gecko/20100101 Firefox/79.0',
            'Authorization': 'Bearer ' + token[key]
        }
    else:
        print('No token found')
        return None

    today = time.strftime('%A')
    today_date = date.today()

    if today == 'Monday':
        send_bookings(headers, classes_id, 'Wednesday', today_date)
    if today == 'Tuesday':
        send_bookings(headers, classes_id, 'Thursday', today_date)
    if today == 'Wednesday':
        send_bookings(headers, classes_id, 'Friday', today_date)
    if today == 'Thursday':
        send_bookings(headers, classes_id, 'Saturday', today_date)
    if today == 'Friday':
        send_bookings(headers, classes_id, 'Sunday', today_date)
    if today == 'Saturday':
        send_bookings(headers, classes_id, 'Monday', today_date)
    if today == 'Sunday':
        send_bookings(headers, classes_id, 'Tuesday', today_date)


if __name__ == '__main__':
    main()
