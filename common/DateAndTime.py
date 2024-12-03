from datetime import datetime, timedelta
import pytz
from common.singleton_decorator import singleton
import config


@singleton
class DateAndTime:
    def __init__(self):
        self.__tz = pytz.timezone(config.current_timezone)

    @property
    def time_to_next_update(self):
        current_time = datetime.now(self.__tz)
        minutes_to_next_10 = (10 - current_time.minute % 10) % 10
        next_10_time = (current_time + timedelta(minutes=minutes_to_next_10)).strftime("%H:%M")
        seconds_to_next_10 = (10 - current_time.minute % 10) * 60 - current_time.second
        return seconds_to_next_10, next_10_time

    @property
    def current_time(self):
        return datetime.now(self.__tz)


if __name__ == '__main__':
    dt = DateAndTime()
    print(dt.time_to_next_update)
    print(dt.current_time)
