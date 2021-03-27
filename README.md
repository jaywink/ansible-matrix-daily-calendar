# Ansible Matrix Daily Calendar

Runs and configures a Matrix Daily Calendar bot.

https://gitlab.com/uhoreg/matrix_daily_calendar

This repository is also mirrored on GitHub at https://github.com/jaywink/ansible-matrix-daily-calendar

## Installing

`ansible-galaxy install jaywink.ansible_matrix_daily_calendar`

## Usage

Before running the role, you'll need to create a Matrix user for it, invite it
to a room and also ensure it joins the room. The bot does not currently join
rooms when invited automatically.

## Configuration

```yaml
# Required, no defaults
#matrix_daily_calendar_homeserver: https://matrix.domain.tld
#matrix_daily_calendar_access_token: secret_token
#matrix_daily_calendar_room: !foobar:domain.tld
#matrix_daily_calendar_calendars:
#  # Array of calendars, one at minimum required
#  - name: My Calendar
#    username: username
#    password: password
#    # URL to calendar
#    url: https://domain.tld/caldav
#    # OPTIONAL list of calendars, defaults to all
#    #calendars:
#    #  - https://domain.tld/caldar/cal1
#    #  - https://domain.tld/caldar/cal2

# Optional, defaults here
matrix_daily_calendar_start: '0'

# Optional, defaults to system default
#matrix_daily_calendar_timezone:
```

## TODO

* Make bot attempt a join to the room when running the role

## License

Apache 2.0
