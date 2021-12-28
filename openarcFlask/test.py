import requests
import json

serverToken = 'AAAAqDswnXk:APA91bECCSobVyMPiz-8Dzrrhl-TI8LUvcnSxUtyDZGUQmp1e8HNJlE7oRDX5jG00NixIx__K3G7f380ZKxEqu2Wyg1XHYkjTSI7SxIu3sm14Swv4QMoH21NM4wGSbUOW53ETwuqe5Fl'
deviceToken = 'device token here'

headers = {
        'Content-Type': 'application/json',
        'Authorization': 'key=' + serverToken,
      }

body = {
          'notification': {'title': 'Sending push form python script',
                            'body': 'New Message'
                            },
          'to':
              deviceToken,
          'priority': 'high',
        #   'data': dataPayLoad,
        }
response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body))
print(response.status_code)

print(response.json())