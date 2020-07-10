# -*- encoding:utf8 -*-
import time
import datetime

def n_days_ago_milli_time(n):
    return int(round((time.time()-n*24*60*60) * 1000))

def three_days_ago_milli_time():
    return int(round((time.time()-5*24*60*60) * 1000))

def current_milli_time():
    return int(round(time.time() * 1000))

def timestamp_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp / 1000)

def time_to_str(time_value=None, format_style='%Y%m%d'):
    if time_value is None:
        time_value = datetime.datetime.now()
    return datetime.datetime.strftime(time_value, format_style)

def timestamp_to_date(timestamp):
    timeArray = time.localtime(timestamp/1000)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime
    
if __name__ == '__main__':
    print(current_milli_time())
    print(time_to_str())
    print(timestamp_to_datetime(current_milli_time()))
