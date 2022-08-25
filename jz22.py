from icalendar import Calendar, Event as CalEvent, vText
from tzlocal import get_localzone
from dateutil import parser
from pytz import timezone
import requests
import inquirer
import json
import os

tz_name = get_localzone()

class Event:

    def __init__(self, uuid, title, start_time, length, end_time, room, event_type):
        self.uuid = uuid
        self.title = title
        self.start_time = start_time
        self.length = length
        self.end_time = end_time
        self.room = room
        self.event_type = event_type

    def __str__(self):
        return '{}->{} ({}, {}m): {} '.format(
                self.start_time.astimezone(tz_name).strftime('%H:%M'),
                self.end_time.astimezone(tz_name).strftime('%H:%M'),
                self.event_type,
                self.length,
                self.title
                )


def parse_event(json):
    return Event(
            json['id'],
            json['title'],
            parser.isoparse(json['startTimeZulu']),
            json['length'],
            parser.isoparse(json['endTimeZulu']),
            json['room'],
            json['format']
   )

def create_prompt(talk):
    return inquirer.List(talk.uuid, message='{}\nInclude?'.format(str(talk.title)), choices=['yes', 'no'])

def create_calendar_event(event_obj):
    cal_event = CalEvent()
    cal_event['summary'] =  event_obj.title
    cal_event['dtstart'] =  event_obj.start_time
    cal_event['dtend'] =  event_obj.end_time
    cal_event['location'] = event_obj.room
    return cal_event

if __name__ == '__main__':

    payload = json.loads(requests.get('https://sleepingpill.javazone.no/public/allSessions/javazone_2022').text)['sessions']

    all_events = list(map(parse_event, payload))

    sorted_by_start_time = sorted(all_events, key=lambda event: event.start_time)

    talks = list(filter(lambda event: event.event_type in ['lightning-talk', 'presentation'], sorted_by_start_time))

    prompt = inquirer.Checkbox(
                'include',
                'Select talks you want to include',
                talks
            )

    print('start times displayed in {} tz'.format(tz_name))

    answer = inquirer.prompt([prompt])

    cal = Calendar()
    cal['summary'] = 'javazone talks 2022'
    cal_events = list(map(create_calendar_event, answer['include']))

    [cal.add_component(ev) for ev in cal_events]
    with open(os.path.join('/tmp', 'jz_cal.ics'), 'wb') as file:
        file.write(cal.to_ical())
        file.close
        print('wrote calendar to {}'.format(file.name))
