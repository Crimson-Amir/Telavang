import datetime
import logging

logging.getLogger("application")
bakery_token = {}

def get_expiry(minutes=10):
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)
