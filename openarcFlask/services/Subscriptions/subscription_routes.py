from flask import Blueprint, request, jsonify, make_response, Response
from services.Users.Enquirer.models import *
from services.Users.Member.models import *
from os import environ, path
from dotenv import load_dotenv
import sys, os
from . import login_manager
from flask_login import current_user, login_required, logout_user
from flask_jwt_extended import jwt_required , get_jwt_identity
import requests,json
import braintree
import json
from .models import SubscriptionPlans, Subscriptions, PaymentStatusEnum, Cards, CardsSchema
from services.push_notifications import send_notification
import stripe
import datetime

VAT = 20

basedir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..'))
load_dotenv(path.join(basedir, '.env'))

stripe.api_key = environ.get('STRIPE_SECRET_KEY')

connected_account_id = environ.get('STRIPE_CONNECTED_ACCOUNT')

# Blueprint Configuration
subscription_main_bp = Blueprint(
    'subscription_main_bp', __name__,
)


#GET ALL PLANS
@subscription_main_bp.route("/getPlans/", methods=['GET'])
@jwt_required
def getAllPlans():
    """Get ALL Plans"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        member_plans_list = []
        member_plans_dict = {}
        employer_plans_list = []
        employer_plans_dict = {}
        free_plans_list = []
        free_plans_dict = {}
        free_plans = SubscriptionPlans.query.filter(SubscriptionPlans.plan_type =='All')
        for plan in free_plans:
            free_plans_dict['plan_id']=plan.id
            free_plans_dict['description']=plan.description 
            free_plans_dict['discount']=plan.discount  
            free_plans_dict['name']=plan.plan_name
            free_plans_dict['monthly_price']=plan.monthly_price
            free_plans_dict['yearly_price']=plan.yearly_price
            free_plans_dict['created_at']=plan.created_at
            free_plans_dict['updated_at']=plan.updated_at
            free_plans_dict['plan_type']=plan.plan_type
            free_plans_list.append(free_plans_dict.copy())
        employer_plans = SubscriptionPlans.query.filter(SubscriptionPlans.plan_type =='Enquirer')
        for plan in employer_plans:
            employer_plans_dict['plan_id']=plan.id
            employer_plans_dict['description']=plan.description 
            employer_plans_dict['discount']=plan.discount  
            employer_plans_dict['name']=plan.plan_name
            employer_plans_dict['monthly_price']=plan.monthly_price
            employer_plans_dict['yearly_price']=plan.yearly_price
            employer_plans_dict['created_at']=plan.created_at
            employer_plans_dict['updated_at']=plan.updated_at
            employer_plans_dict['plan_type']=plan.plan_type
            employer_plans_list.append(employer_plans_dict.copy())
        member_plans = SubscriptionPlans.query.filter(SubscriptionPlans.plan_type =='Member')
        for plan in member_plans:
            member_plans_dict['plan_id']=plan.id
            member_plans_dict['description']=plan.description 
            member_plans_dict['discount']=plan.discount  
            member_plans_dict['name']=plan.plan_name
            member_plans_dict['monthly_price']=plan.monthly_price
            member_plans_dict['yearly_price']=plan.yearly_price
            member_plans_dict['created_at']=plan.created_at
            member_plans_dict['updated_at']=plan.updated_at
            member_plans_dict['plan_type']=plan.plan_type
            member_plans_list.append(member_plans_dict.copy())
        return make_response(jsonify({"free_plans": free_plans_list,"member_plans": member_plans_list,'employer_plans':employer_plans_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting plans at line',lNumber,'error is:',e)
        return make_response(jsonify({"error_message":str(e)}),400)


#GET Payment Screen
@subscription_main_bp.route("/getPaymentScreen/", methods=['GET'])
@jwt_required
def getPaymentScreen():
    """getPaymentScreen"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        cards_list = []
        card_dict = {}
        existing_cards = Cards.query.filter_by(user=current_user)
        for card in existing_cards:
            card_dict['id'] = card.id
            card_dict['card_number'] = card.card_number
            card_dict['name_on_card'] = card.name_on_card
            card_dict['expiry_date'] = card.expiry_date
            card_dict['cvv'] = card.cvv
            card_dict['card_'] = card.card_type
            card_dict['status'] = card.is_active
            cards_list.append(card_dict.copy())
        wallet_exists = bool(Wallet.query.filter_by(user_id=current_user).first())
        if wallet_exists:
            wallet_instance = Wallet.query.filter_by(user_id).first()
            wallet_balance = wallet_instance.balance
        else:
            wallet_balance = 0
        return make_response(jsonify({"cards": cards_list,"wallet_balance": wallet_balance}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting subscription payment details at line',lNumber,'error is:',e)
        return make_response(jsonify({"error_message":str(e)}),400)

#Subscription Payment from Wallet
@subscription_main_bp.route("/walletSubscription/", methods=['POST'])
@jwt_required
def walletSubscription():
    """Pay Form Wallet"""
    try:
        current_user = get_jwt_identity()
        post_data = request.get_json()
        plan_id = post_data['plan_id']
        billing_cycle = post_data['billing_cycle']
        plan_instance = SubscriptionPlans.query.get(plan_id)
        if (billing_cycle == '') or (billing_cycle == None):
            return make_response(jsonify({"error":'billing cycle is required'}),400)
        if billing_cycle == 'monthly':
            plan_price = plan_instance.monthly_payment
        if billing_cycle == 'yearly':
            plan_price = plan_instance.yearly_payment
        print('plan_price>>>>>>>',plan_price)
        if '£' in plan_price:
            price_string = plan_price.replace('£','')
            final_price = price_string
        if ',' in final_price:
            final_price_string = final_price.split(',')
            final_price = final_price_string[0]
        print('final>>>>>>>',final_price)
        ###Check if already subscribed with same plan 
        # try:
        #     existing_subscription = bool(Subscriptions.query.filter_by(user=current_user).filter_by(plan_id=plan_id).first())
        #     if existing_subscription :
        #         return make_response(jsonify({"error":"Already Subscribed"}),400)
        # except Exception as e:
        #     return make_response(jsonify({"error":"Already Subscribed"}),400)
        ####Check if wallet is funded
        wallet_exists = bool(Wallet.query.filter_by(user_id=current_user).first())
        if not wallet_exists:
            return make_response(jsonify({"error":"wallet balance is low"}),400)
        wallet_instance = Wallet.query.filter_by(user_id=current_user).first()
        print('wallet_instance',wallet_instance)
        balance = wallet_instance.balance
        print('amounts>>>>>>',balance,final_price, type(balance),type(final_price))
        if int(balance) < int(final_price):
            print('inside low>>>>>>>')
            return make_response(jsonify({"error":"wallet balance is low"}),400)
        #######Make Payment From Wallet######
        account_id = connected_account_id
        transfer_amount = (int(final_price)*100)
        print('transfer_amount',transfer_amount)
        if account_id:
            transfer = stripe.Transfer.create(
              amount=int(transfer_amount),
              currency='gbp',
              destination= account_id,
              transfer_group="Subscription Payment"
            )
        ############Update Wallet#################
        remaining_balance = float(balance)-float(final_price)
        wallet_instance.balance = remaining_balance
        ##Add Payment details
        payment_instance = UserPayments(
                reference = 'Subscription',
                medium = 'wallet',
                amount = final_price,
                user_id = current_user
            )
        try:
            local_object = db.session.merge(payment_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(payment_instance)
        try:
            local_object = db.session.merge(wallet_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(wallet_instance)
        ##########Add Subscription Details################
        ###Create/Update Subscription Plan
        subscription_exists = bool(Subscriptions.query.filter_by(user=current_user).first())
        if subscription_exists:
            subscription_instance = Subscriptions.query.filter_by(user=current_user).first()
            subscription_instance.plan_id = plan_id
            subscription_instance.billing_cycle = billing_cycle
            subscription_instance.user = current_user
            subscription_instance.is_active = True
            subscription_instance.payment_date = datetime.datetime.now()
            subscription_instance.payment_status = PaymentStatusEnum.approved
        else:
            subscription_instance = Subscriptions(
                    plan_id = plan_id,
                    billing_cycle = billing_cycle,
                    user = current_user,
                    is_active=True,
                    payment_date = datetime.datetime.now(),
                    payment_status = PaymentStatusEnum.approved
                )
        try:
            local_object = db.session.merge(subscription_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(subscription_instance)
        db.session.commit()
        ############return updated record########################
        existing_wallet = Wallet.query.filter_by(user_id=current_user)
        for record in existing_wallet:
            wallet_id = record.id
        record_instance = Wallet.query.get(wallet_id)
        record_schema = WalletSchema(many=False)
        record = record_schema.dump(record_instance)
        return make_response(jsonify({"status":"Subscription Activated","wallet":record}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in payment from wallet',lNumber,'error is:',e)
        return make_response(jsonify({"error_message":str(e)}),400)

#Subscription Payment from Card
@subscription_main_bp.route("/cardSubscription/", methods=['POST'])
@jwt_required
def cardSubscription():
    """Pay Form Card"""
    try:
        current_user = get_jwt_identity()
        post_data = request.form
        plan_id = post_data['plan_id']
        billing_cycle = post_data['billing_cycle']
        plan_instance = SubscriptionPlans.query.get(plan_id)
        if (billing_cycle == '') or (billing_cycle == None):
            return make_response(jsonify({"error":'billing cycle is required'}),400)
        card_number = post_data['card_number']
        exp_month = post_data['exp_month']
        exp_year = post_data['exp_year']
        cvv = post_data['cvv']
        if ((exp_month == '') or (card_number == '') or (exp_year == '') or (cvv == '')):
                return make_response(jsonify({"error":"Please pass all required parameters"}),400)
        token_data = stripe.Token.create(
                      card={
                        "number": card_number,
                        "exp_month": int(exp_month),
                        "exp_year": int(exp_year),
                        "cvc": cvv,
                      },
                    )
        token = token_data['id']
        print('token',token)
        if billing_cycle == 'monthly':
            plan_price = plan_instance.monthly_payment
        if billing_cycle == 'yearly':
            plan_price = plan_instance.yearly_payment
        print('plan_price>>>>>>>',plan_price)
        if '£' in plan_price:
            price_string = plan_price.replace('£','')
            final_price = price_string
        if ',' in final_price:
            final_price_string = final_price.split(',')
            final_price = final_price_string[0]
        print('final>>>>>>>',final_price)
        ###Check if already subscribed with same plan 
        # try:
        #     existing_subscription = bool(Subscriptions.query.filter_by(user=current_user).filter_by(plan_id=plan_id).first())
        #     if existing_subscription :
        #         return make_response(jsonify({"error":"Already Subscribed"}),400)
        # except Exception as e:
        #     return make_response(jsonify({"error":"Already Subscribed"}),400)
        #######Make Payment From Card######
        currency = 'GBP'
        token = token
        payable_amount = int(final_price)*100
        charge = stripe.Charge.create(
          amount=payable_amount,
          currency=currency,
          description='For Subscription',
          source=token,
        )
        account_id = connected_account_id
        transfer_amount = (int(final_price)*100)
        print('transfer_amount',transfer_amount)
        if account_id:
            transfer = stripe.Transfer.create(
              amount=int(transfer_amount),
              currency='gbp',
              destination= account_id,
              transfer_group="Subscription Payment"
            )
        ##Add Payment details
        payment_instance = UserPayments(
                reference = 'Subscription',
                medium = 'card',
                amount = final_price,
                user_id = current_user
            )
        try:
            local_object = db.session.merge(payment_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(payment_instance)
        ##########Add Subscription Details################
        ###Create/Update Subscription Plan
        subscription_exists = bool(Subscriptions.query.filter_by(user=current_user).first())
        if subscription_exists:
            subscription_instance = Subscriptions.query.filter_by(user=current_user).first()
            subscription_instance.plan_id = plan_id
            subscription_instance.billing_cycle = billing_cycle
            subscription_instance.user = current_user
            subscription_instance.is_active = True
            subscription_instance.payment_date = datetime.datetime.now()
            subscription_instance.payment_status = PaymentStatusEnum.approved
        else:
            subscription_instance = Subscriptions(
                    plan_id = plan_id,
                    billing_cycle = billing_cycle,
                    user = current_user,
                    is_active=True,
                    payment_date = datetime.datetime.now(),
                    payment_status = PaymentStatusEnum.approved
                )
        try:
            local_object = db.session.merge(subscription_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(subscription_instance)
        db.session.commit()
        ############return updated record########################
        try:
            existing_wallet = Wallet.query.filter_by(user_id=current_user)
            for record in existing_wallet:
                wallet_id = record.id
            record_instance = Wallet.query.get(wallet_id)
            record_schema = WalletSchema(many=False)
            record = record_schema.dump(record_instance)
        except Exception as e:
            record=''
        return make_response(jsonify({"status":"Subscription Activated","wallet":record}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in payment from card',lNumber,'error is:',e)
        return make_response(jsonify({"error_message":str(e)}),400)

#CANCEL SUBSCRIPTION BY USER ID
@subscription_main_bp.route("/cancelSubscription/", methods=['POST'])
@jwt_required
def cancelSubscription():
    """Cancel Subscription"""
    try:
        current_user = get_jwt_identity()
        try:
            subscription_details = Subscriptions.query.filter_by(user=current_user)
            for subscription in subscription_details:
                subscription_id = subscription.id
        except Exception as e:
            return make_response(jsonify({"error":"No Subscription found for this user"}),400)
        get_subscription = Subscriptions.query.get(subscription_id)
        get_subscription.is_cancelled = True
        get_subscription.is_active = False
        db.session.add(get_subscription)
        db.session.commit()  # Cancel Subscription
        return make_response(jsonify({"success":"Subscription Cancelled."}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in cancelling subscription at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":"Error cancelling a Subscribtion"}),400)


#GET SUBSCRIPTION BY USERID
@subscription_main_bp.route("/getActivePlan/", methods=['GET'])
@jwt_required
def getSubscriptionDetails():
    """Get A user subscription details"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        subscription_list = []
        subscription_dict = {}
        try:
            subscription_details = bool(Subscriptions.query.filter_by(user=current_user).first())
            if not subscription_details:
                plan_instance = SubscriptionPlans.query.filter_by(plan_name='Free').first()
                print('plan_instance',plan_instance)
                free_days = plan_instance.free_days
                start_date = user_instance.created_at
                end_date =  end_date = start_date + datetime.timedelta(days=int(free_days))
                print('end_date',end_date)
                today = datetime.datetime.now()
                if end_date > today:
                    status = 'active'
                else:
                    status = 'inactive' 
                if status == 'active':
                    is_active = True
                    is_cancelled = False
                else:
                    is_active = False
                    is_cancelled = True
                subscription_dict['user']=current_user
                subscription_dict['payment_status']='Free'
                subscription_dict['start_date']= start_date
                subscription_dict['end_date']= end_date
                subscription_dict['is_active']=is_active
                subscription_dict['is_cancelled']=is_cancelled
                subscription_list.append(subscription_dict.copy())
                return make_response(jsonify({"subscription": subscription_list}),200)
        except Exception as e:
            print('eror>>>>>>>>>>>>',e)
            return make_response(jsonify({"error": 'Subscription plan not found'}),400)
        subscription_details = Subscriptions.query.filter_by(user=current_user)
        for subscription in subscription_details:
            payment_status = subscription.payment_status
            if payment_status == PaymentStatusEnum.pending:
                payment_status_value = 'pending'
            if payment_status == PaymentStatusEnum.approved:
                payment_status_value = 'approved'
            if payment_status == PaymentStatusEnum.rejected:
                payment_status_value = 'rejected'
            print(payment_status_value)
            subscription_dict['subscription_id']=subscription.id
            subscription_dict['plan_id']=subscription.plan_id   
            subscription_dict['user']=subscription.user
            subscription_dict['payment_status']=payment_status_value
            subscription_dict['created_at']=subscription.created_at
            subscription_dict['updated_at']=subscription.updated_at
            subscription_dict['is_active']=subscription.is_active
            subscription_dict['is_cancelled']=subscription.is_cancelled
            subscription_list.append(subscription_dict.copy())
        return make_response(jsonify({"subscription": subscription_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting subscription at line',lNumber,'error is:',e)
        return make_response(jsonify({"error_message":str(e)}),400)

#################################################################################################

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



#Delete Connected Account
@subscription_main_bp.route("/deleteConnectedAccount/", methods=['POST'])
def deleteConnectedAccount():
    # print(request.POST)
    account_id = request.form.get('account_id')
    if account_id:
        try:
            stripe.Account.delete(account_id)
            return make_response(jsonify({"success": 'deleted successfully'}),200)
        except Exception as e:
            print('error in delete---',e)
            return make_response(jsonify({"error": 'No such account'}),400)
    else:
        return make_response(jsonify({"error": 'No such account'}),400)



@subscription_main_bp.route("/addMoneyToAccount/", methods=['POST'])
def addMoneyToAccount():
    try:
        ###############Card Token######################
        post_data = request.form
        card_number = post_data['card_number']
        exp_month = post_data['exp_month']
        exp_year = post_data['exp_year']
        cvv = post_data['cvv']
        token_data = stripe.Token.create(
                      card={
                        "number": card_number,
                        "exp_month": int(exp_month),
                        "exp_year": int(exp_year),
                        "cvc": cvv,
                      },
                    )
        token = token_data['id']
        print('token',token)
        currency = 'GBP'
        token = token
        payable_amount = 10000000
        charge = stripe.Charge.create(
          amount=payable_amount,
          currency=currency,
          description='added amount',
          source=token,
        )
        return make_response(jsonify({"payment_object": charge}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('line',lNumber,'error',e)
        return make_response(jsonify({"error in payment":str(e)}),400)
