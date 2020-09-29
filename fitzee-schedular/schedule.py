import pycron
import time
import requests


while True:
    if pycron.is_now('* * * * *'):   # True Every Sunday at 02:00
        print('running yoga gif')
        payload={'gif_name':'yoga'}
        requests.get("https://fitzee-python-app.azurewebsites.net/api/notify",params=payload)
        time.sleep(60)               # The process should take at least 60 sec
                                     # to avoid running twice in one minute
    elif pycron.is_now('51 16 * * *'):   # True Every Sunday at 02:00
        print('running water gif')
        payload={'gif_name':'water'}
        requests.get("https://fitzee-python-app.azurewebsites.net/api/notify",params=payload)
        time.sleep(60) 
    else:
        time.sleep(60)               # Check again in 15 seconds