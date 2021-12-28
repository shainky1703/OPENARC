from pyfcm import FCMNotification
from flask import make_response,jsonify
import os, sys
from dotenv import load_dotenv
from os import environ, path

basedir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))
load_dotenv(path.join(basedir, '.env'))


serverToken =environ.get('FCM_SERVER_TOKEN')

push_service = FCMNotification(api_key=serverToken)

def send_notification(device_token, message_title, message_body, purpose):
  try:
    result = push_service.notify_single_device(registration_id=device_token, message_title=message_title, message_body=message_body)
    print ('result',result)
    return make_response(jsonify({"purpose":purpose}),200)
  except Exception as e:
    #catch error and print line number where error occurs
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    lNumber = exc_tb.tb_lineno
    print('Error occurs in sending notification',lNumber,'error is:',e)
    return make_response(jsonify({"error_message":str(e)}),400)
