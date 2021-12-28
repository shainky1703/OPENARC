"""Application entry point."""
from services import Users, Jobs, Stripe, Subscriptions
import threading
from flask_socketio import SocketIO


users_app = Users.create_app()
jobs_app = Jobs.create_app()
stripe_app = Stripe.create_app()
subscriptions_app = Subscriptions.create_app()



###For testing
def UsersMicroService():
    users_app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

def JobsMicroService():
    jobs_app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)

def StripeMicroService():
    stripe_app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)

def SubscriptionsMicroService():
    subscriptions_app.run(host='0.0.0.0', port=5003, debug=False, threaded=True)



if __name__ == '__main__':
    # Executing the Threads seperatly.
    t1 = threading.Thread(target=UsersMicroService)
    t1.start()
    t2 = threading.Thread(target=JobsMicroService)
    t2.start()
    t3 = threading.Thread(target=StripeMicroService)
    t3.start()
    t4 = threading.Thread(target=SubscriptionsMicroService)
    t4.start()

 
 
