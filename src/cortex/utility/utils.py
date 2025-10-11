import datetime

def get_utc_now():
    return datetime.datetime.now(datetime.timezone.utc)