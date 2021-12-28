from flask import Blueprint, request, jsonify, make_response, Response
from services.Users.Enquirer.models import *
from services.Users.Member.models import *
from services.Jobs.models import *
from os import environ, path
from dotenv import load_dotenv
import sys, os
from . import login_manager
from flask_login import current_user, login_required, logout_user
from flask_jwt_extended import jwt_required , get_jwt_identity
import requests,json
from flask_mail import Mail, Message
from . import mail
from datetime import datetime
import stripe
import time

basedir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..'))
load_dotenv(path.join(basedir, '.env'))



# Blueprint Configuration
stripe_main_bp = Blueprint(
    'stripe_main_bp', __name__,
)

stripe.api_key = environ.get('STRIPE_SECRET_KEY')

#################################################Make Payment to OpenaArc#########################################

#CREATE CONNECTED ACCOUNT
@stripe_main_bp.route("/addConnectedAccount/", methods=['POST'])
@jwt_required
def createConnectedAccount():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Member"}),400)
        acc_exists = StripeDetails.query.filter_by(user_id=current_user).first()
        if acc_exists:
            connected_account = acc_exists.connected_account
            if connected_account:
                return make_response(jsonify({"error": "Connecting Account already exists"}),400)
        post_data = request.form
        email = user_instance.email
        first_name = post_data['first_name']
        last_name = post_data['last_name']
        dob_day = post_data['dob_day']
        dob_month = post_data['dob_month']
        dob_year = post_data['dob_year']
        city = post_data['city']
        phone = post_data['phone']
        address_line1 = post_data['address_line1']
        address_line2 = post_data['address_line2']
        postal_code = post_data['postal_code']
        state = post_data['state']
        sort_number = post_data['sort_code']
        account_number = post_data['account_number']
        if((first_name == '') or (last_name == '') or (dob_day == '') or (dob_month == '') or (dob_year == '') or 
        (city == '') or (phone == '') or (address_line1 == '') or (address_line2 == '') or (postal_code == '') or
        (state == '') or (sort_number == '') or (account_number == '')):
            return make_response(jsonify({"error":'All parameters are required'}),400)
        account = stripe.Account.create(
            country='GB',
            type='custom',
            email = email,
            capabilities={
                'transfers': {
                  'requested': True,
                }
            },
            business_type="individual",
            individual = {
                "address":{
                    "city":city,
                    "country":"GB",
                    "line1":address_line1,
                    "line2":address_line2,
                    "postal_code":postal_code,
                    "state":state,
                },
                "dob":{
                    "day":dob_day,
                    "month":dob_month,
                    "year":dob_year
                },
                "verification" : {
                    "additional_document":{
                        "back":"file_identity_document_success",
                        "front":"file_identity_document_failure"
                    },
                    "document":{
                        "back":"file_identity_document_success",
                        "front":"file_identity_document_failure"
                    }
                },
                "phone":phone,
                "email":email,
                "first_name":first_name,
                "last_name":last_name
            },
            business_profile={
                'mcc': '5734',
                'support_url':'https://www.openarc.com',
                'url':'https://www.openarc.com' 
            },
            tos_acceptance={
                'service_agreement': 'recipient',
            },
            )
        print('account',account.id)
        account_id = account.id
        ####Accept Terms & Conditions#########
        stripe.Account.modify(
          account_id,
          tos_acceptance={
            'date': int(time.time()),
            'ip': '8.8.8.8', # Depends on what web framework you're using
          }
        )
        ##########Add Bank Account###########
        acc = stripe.Account.create_external_account(
          account_id,
          external_account={
              "object": "bank_account",
              "account_holder_name": user_instance.name,
              "account_holder_type": "individual",
              "country": "GB",
              "currency": "gbp",
              "metadata": {},
              "routing_number": sort_number,
              "account_number": account_number
          }
        )
        ##############Add details to our db################################
        stripe_instance = StripeDetails(
                routing_number = sort_number,
                account_number = account_number,
                first_name = first_name,
                last_name = last_name,
                phone = phone,
                dob_day = dob_day,
                dob_month = dob_month,
                dob_year = dob_year,
                address_line_1 = address_line1,
                address_line_2 = address_line2,
                city = city,
                state = state,
                zip_code = postal_code,
                account_id = account_id,
                connected_account = True,
                user_id = current_user
            )
        db.session.add(stripe_instance)
        db.session.commit()  # Create Stripe Details
        return make_response(jsonify({"message":"success","account": account}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('line',lNumber,'error',e)
        return make_response(jsonify({"error in addings account":str(e)}),400)


#Create Session
@stripe_main_bp.route("/createSession/", methods=['POST'])
@jwt_required
def createSession():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer"}),400)
        ###############Sent Data######################
        post_data = request.form
        success_url = post_data['success_url']
        cancel_url = post_data['cancel_url']
        ###Make Stripe Session##########
        price = stripe.Price.create(
          unit_amount=4401,
          currency="gbp",
          product_data={'name':'payment'}
        )
        price_id = price['id']
        print('price',price_id)
        session_obj = stripe.checkout.Session.create(
              success_url=success_url,
              cancel_url=cancel_url,
              payment_method_types=["card"],
              line_items=[
                {
                  "price": price_id,
                  "quantity": 1,
                },
              ],
              mode="payment"
        )
        return make_response(jsonify({"session":session_obj}),200)  
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error creating session at line',lNumber,'error',e)
        return make_response(jsonify({"error in session":str(e)}),400)


#Make Payment To Employee
@stripe_main_bp.route("/payEmployee/", methods=['POST'])
@jwt_required
def payEmployee():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer"}),400)
        ###############Sent Data######################
        post_data = request.form
        amount = post_data['amount']
        employee_id = post_data['employee_id']
        job_id = post_data['job_id']
        if((amount == '') or (employee_id=='') or (job_id=='')):
            return make_response(jsonify({"error":'All parameters are required'}),400)
        #####Calculations#########
        
        ###Make Stripe Payment##########
        stripe_details_exists = bool(StripeDetails.query.filter_by(user_id=employee_id).first())
        if stripe_details_exists:
            stripe_details = StripeDetails.query.filter_by(user_id=employee_id).first()
            account_id = stripe_details.account_id
            transfer_amount = (int(amount)*100)
            print('transfer_amount',transfer_amount)
            if account_id:
                transfer = stripe.Transfer.create(
                  amount=int(transfer_amount),
                  currency='gbp',
                  destination= account_id,
                  transfer_group="ORDER_95"
                )
            else:
                return make_response(jsonify({"error":'Stripe Connected AccountId not found'}),400)
        else:
            return make_response(jsonify({"error":'Stripe Details not found'}),400)
        ##############Save TO OpenArc DB#################
        application_details = AppliedJobs.query.filter_by(job_id = job_id).filter_by(applied_by=employee_id).first()
        application_id = application_details.id
        total_payment = application_details.total_payment
        application_details.payment_done = amount
        try:
            local_object = db.session.merge(application_details)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(application_details)
        db.session.commit()
        job_logs = StartedJobLogs.query.filter_by(application_id=application_id)
        for log in job_logs:
            if ((log.end_time != '00:00:00') or (log.end_time != '')):
                log.amount_paid = True
                try:
                    local_object = db.session.merge(log)
                    db.session.add(local_object)
                except Exception as e:
                    print('error in commit',e)
                    db.session.add(log)
                db.session.commit() 
        ############Add Payment To OpenARC#################
        payment_instance = Payments(
                amount_paid = amount,
                user_id = employee_id,
                application_id = application_id,
            )
        db.session.add(payment_instance)
        db.session.commit()
        return make_response(jsonify({"success":'payment_successfull'}),200)  
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error paying employee at line',lNumber,'error',e)
        return make_response(jsonify({"error in payment":str(e)}),400)

#########################################################################################################
def convert24(str1): 
      
    # Checking if last two elements of time 
    # is AM and first two elements are 12 
    if str1[-2:] == "AM" and str1[:2] == "12": 
        return "00" + str1[2:-2] 
          
    # remove the AM     
    elif str1[-2:] == "AM": 
        return str1[:-2] 
      
    # Checking if last two elements of time 
    # is PM and first two elements are 12    
    elif str1[-2:] == "PM" and str1[:2] == "12": 
        return str1[:-2] 

    # # remove the PM     
    # elif str1[-2:] == "PM": 
    #     return str1[:-2]
          
    else: 
          
        # add 12 to hours and remove PM 
        return str(int(str1[:2]) + 12) + str1[2:8] 

####################################################LOGIN MANAGER#####################################
@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in on every page load."""
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    return Response("{'error':'Please login first'}", status=400)

######################################################################################################


###Get Account Balance
@stripe_main_bp.route("/getAccountBalance/", methods=['POST'])
def getAccountBalance():
    try:
        post_data = request.form
        account_id = post_data['account_id']
        balance = stripe.Balance.retrieve(
          stripe_account= account_id
        )
        return make_response(jsonify({"balance":balance}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in retreiving balance',lNumber,'error',e)
        return make_response(jsonify({"error in payment":str(e)}),400)