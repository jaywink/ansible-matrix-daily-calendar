#!/usr/bin/env python3
#      DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#                    Version 2, December 2004
#
# Copyright (C) 2021 Hubert Chathi <hubert@uhoreg.ca>
#
# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.
#
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#
#  0. You just DO WHAT THE FUCK YOU WANT TO.
#
# [ansible-matrix-daily-calendar note] Copied from:
# https://gitlab.com/uhoreg/matrix_daily_calendar/-/blob/4c8571e9c2f85b90e6e434935a8b175573d8c68d/daily_calendar

import caldav
import configparser
from datetime import date, datetime, timedelta
from dateutil.tz import gettz
from html import escape
from optparse import OptionParser
from os import getpid
import json
from time import time
from urllib.request import urlopen, Request


def process_calendar(cal, today, tz, days, start):
    events = []
    for ev in cal.date_search(
            start=today + timedelta(days=start),
            end=today + timedelta(days=days + start)
    ):
        instance = ev.icalendar_instance
        for item in instance.subcomponents:
            # FIXME: distinguish between confirmed/unconfirmed events
            try:
                dtstart = item.decoded("dtstart")
                if isinstance(dtstart, datetime):
                    dtstart = item.decoded("dtstart").astimezone(tz)
                    if "duration" in item:
                        startstr = dtstart.strftime("%H:%M") if dtstart.date() == today \
                            else dtstart.strftime("%Y-%m-%d %H:%M")
                        dtend = dtstart + item.decoded("duration")
                        endstr = dtend.strftime("%H:%M") if dtend.date() == dtend.date() \
                            else dtend.strftime("%Y-%m-%d %H:%M")
                        item_time = "{start} - {end}".format(
                            start=startstr,
                            end=endstr
                        )
                    elif "dtend" in item:
                        startstr = dtstart.strftime("%H:%M") if dtstart.date() == today \
                            else dtstart.strftime("%Y-%m-%d %H:%M")
                        dtend = item.decoded("dtend").astimezone(tz)
                        endstr = dtend.strftime("%H:%M") if dtend.date() == dtend.date() \
                            else dtend.strftime("%Y-%m-%d %H:%M")
                        item_time = "{start} - {end}".format(
                            start=startstr,
                            end=endstr
                        )
                    else:
                        item_time = dtstart.strftime("%H:%M") if dtstart.date() == today \
                            else dtstart.strftime("%Y-%m-%d %H:%M")
                    events.append((item["summary"], item_time, dtstart))
                else:
                    dtend = dtstart
                    if "duration" in item:
                        dtend = dtstart + item.decoded("duration") - timedelta(days=1)
                    elif "dtend" in item:
                        dtend = item.decoded("dtend") - timedelta(days=1)
                    if dtend != dtstart:
                        item_time = "all day {start} to {end}".format(
                            start="today" if dtstart == today else dtstart.strftime("%Y-%m-%d"),
                            end="today" if dtend == today else dtend.strftime("%Y-%m-%d"),
                        )
                    else:
                        item_time = "all day today" if dtstart == today \
                            else dtstart.strftime("all day %Y-%m-%d")
                    events.append((
                        item["summary"], item_time,
                        datetime(dtstart.year, dtstart.month, dtstart.day, tzinfo=tz)
                    ))
            except:
                pass
    events.sort(key=lambda desc: desc[2])
    return events


parser = OptionParser(
    description="send a list of the day's events to a Matrix room"
)
parser.add_option(
    "-c", "--config",
    dest="config",
    help="configuration file to use [default: %default]",
    metavar="FILE",
    default="calendar.cfg"
)

(options, args) = parser.parse_args()

if args:
    parser.error("Unexpected arguments")

config = configparser.ConfigParser(interpolation=None)
config.read(options.config)

matrix_cfg = config["DEFAULT"]

today = date.today()
timezone = matrix_cfg.get("timezone", None)
tz = gettz(timezone)
start = int(matrix_cfg.get("start", 0))
startdate = today + timedelta(days=start)

calendar_events = []

calendar_names = config.sections()
for calendar_name in config.sections():
    calendar_cfg = config[calendar_name]

    username = calendar_cfg["username"]
    password = calendar_cfg["password"]
    url = calendar_cfg["url"]
    my_cals = calendar_cfg.get("calendars", "").split("\n")
    days = int(calendar_cfg.get("days", 1))

    client = caldav.DAVClient(url=url, username=username, password=password)
    principal = client.principal()

    if my_cals == [""]:
        for cal in principal.calendars():
            events = process_calendar(cal, today, tz, days, start)
            calendar_events.append((cal.name, events))
    else:
        calendars = [cal for cal in principal.calendars() if cal.url in my_cals]

        events_by_cal = {}

        for cal in calendars:
            events = process_calendar(cal, today, tz, days, start)
            events_by_cal[str(cal.url)] = (cal.name, events)

        for url in my_cals:
            if url in events_by_cal:
                calendar_events.append(events_by_cal[url])


plaintext = "# Events for {0:%Y-%m-%d}".format(startdate)
html = "<h3>Events for {0:%Y-%m-%d}</h3>\n".format(startdate)

has_events = False

for (name, events) in calendar_events:
    if events:
        has_events = True
        plaintext += "\n\n## " + name + "\n"
        html += "<h4>{0}</h4>\n<ul>\n".format(escape(name))
        for (name, item_time, dtstart) in events:
            plaintext += "\n* {name} ({time})".format(name=name, time=item_time)
            html += "<li>{name} ({time})</li>\n".format(name=escape(name), time=item_time)
        html += "</ul>\n"

if not has_events:
    plaintext += "\n\nNo events"
    html += "No events"

txnid = "{timestamp}-{pid}".format(timestamp=time(), pid=getpid())

urlopen(Request(
    "{homeserver}/_matrix/client/r0/rooms/{room}/send/m.room.message/{txnid}".format(
        homeserver=matrix_cfg["homeserver"], room=matrix_cfg["room"], txnid=txnid
    ),
    json.dumps({
        "body": plaintext,
        "formatted_body": html,
        "format": "org.matrix.custom.html",
        "msgtype": "m.notice"
    }).encode("utf-8"),
    {
        "Content-type": "application/json",
        "Authorization": "Bearer {token}".format(token=matrix_cfg["access_token"])
    },
    method="PUT"
))
