OPEN ARC PROJECT
#######################################################################################
Basic steps to follow for local Setup Linux:

1) Clone the repo/download zip

2) Create virtual environment
	virtualenv -p python 3 venv_name

3) Activate virtual environment
	sourve venv_name/bin/activate

4) install the requirements
	pip install -r requirements.txt

5) Create two mysql databases:
	(i) openarc_db
	(ii) openarc_jobs_db
	(iii) openarc_subscriptions_db
	(iv) openarc_chats_db

6) Create .env file at root folder of project with following configuration:

FLASK_APP = app.py

FLASK_ENV = development

SQLALCHEMY_DATABASE_URI = mysql+pymysql://root:root@localhost/openarc_db

COMPRESSOR_DEBUG = True

LESS_BIN = /usr/local/bin/lessc

ASSETS_DEBUG = False

LESS_RUN_IN_DEBUG = False

MEMBER_UPLOADS = {{Root folder of project}}/media/uploads/member

MEMBER_UPLOADS = {{Root folder of project}}/media/uploads/enquirer


JWT_SECRET_KEY = ''

JWT_TOKEN_LOCATION = 'headers'

ESCROW_URL = "https://api.escrow-sandbox.com/2017-09-01/"

ESCROW_APPROVE_PAYMENT_URL = "https://integrationhelper.escrow-sandbox.com/v1/transaction/"

ESCROW_BROKER_API_KEY =""

ESCROW_BUYER_API_KEY =""

ESCROW_SELLER_API_KEY =""

ESCROW_EMAIL = 

ESCROW_PASSWORD = 


BRAINTREE_ENVIRONMENT = sandbox

BRAINTREE_MERCHANT_ID = 

BRAINTREE_PUBLIC_KEY = 

BRAINTREE_PRIVATE_KEY = 


FCM_SERVER_TOKEN = 

*Note:THIS WILL CREATE ALL TABLES IN RESPECTIVE DATABASES*

7) run application : 
	python app.py  

8)create tables for socket app
python -m flask shell
>>> from app import db
>>> from app.main import models
>>> db.create_all()

8) run the socket:
	python chat.py



Localhost :
{{ base_url }} : 127.0.0.1:

########################################################################################

APPLICATION API'S:
base_url : http://ec2-3-15-1-100.us-east-2.compute.amazonaws.com  
Users API : {{ base_url }}5000/swagger/

Jobs API : {{ base_url }}5001/swagger/

Escrow API : {{ base_url }}5002/swagger/

Subscription API : {{ base_url }}5003/swagger/

Socket URL : {{ base_url }}:5004/chat

EVENTS:
1) joined
	data: {"user" : "logged_in user id", "room_id" : "logged_in user id"}

2) text
	data: {"user" : "logged_in user id", "send_to" : "user id to whom message needs to ne sent", "msg":"text"}

3) Retrieve All chats
	{{ base_url }}:5004/allUserChats
	type: GET



4) Retrieve Chat messages 
{{ base_url }}:5004/chatMessages/user_id 
	type: POST
	 body:
	 {
	 	"sent_to" : user_id whose messages needs to be retrieved
	 }


########################################################################################


FOR EMAIL SENDING:
Add following values to  services/Users/__init__.py file:

MAIL_USERNAME = '',

MAIL_PASSWORD = ''