"""Logged-in page routes."""
from flask import Blueprint, request, jsonify, make_response, render_template, json, redirect
from flask_login import current_user, login_required, logout_user, login_user
from flask import Response
from os import environ, path
from dotenv import load_dotenv
import sys, os
from flask_jwt_extended import jwt_required , get_jwt_identity, create_access_token
from services.Users.Member.models import *
from services.Users.Enquirer.models import *
import re
from services.Users import login_manager
import flask_login
from flask import Flask, flash
from services.Subscriptions.models import *
from sqlalchemy import func
import sqlalchemy as sa
import calendar
from services.Users import db
from services.Jobs.models import *

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

# Blueprint Configuration
admin_main_bp = Blueprint(
    'admin_main_bp', __name__,
)
  


#################################################ADMIN ROUTES#########################################
#LOGIN
@admin_main_bp.route('/adminLogin/', methods=['GET','POST'])
def adminlogin():
    """
    Admin Log-in
    POST requests validate and redirect user to dashboard.
    """
    # Bypass if user is logged in
    # if current_user.is_authenticated:
    #     return Response("{'success':'Enquirer is already loggedin'}", status=200)
    if request.method == 'POST':  
        try:
            post_data = request.get_json()
            email = post_data['admin_email']
            password = post_data['admin_password']
            user_instance = User.query.filter_by(email=email).first() 
            print('---',user_instance.user_type)
            if user_instance and user_instance.check_password(password=password):  
                if user_instance.user_type=='superuser':
                    print('---user logged in')
                    login_user(user_instance,remember=True)
                    #Identity can be any data that is json serializable
                    access_token = create_access_token(identity=user_instance.id)
                    get_user = User.query.get(user_instance.id)
                    user_schema = UserSchema(many=False)
                    profile = user_schema.dump(get_user)
                    return json.dumps({'status':'success','access_token':access_token,'user':profile});
                else:
                    return json.dumps({'status':'error','message':"not an admin user"});
            else:
                return json.dumps({'status':'error','message':"Invalid Credentials"});
        except Exception as e:
            print('error in login',e)
            return json.dumps({'status':'error','message':str(e)});
    else:
        return render_template('login.html')

#DASHBOARD
@admin_main_bp.route('/adminDashboard/', methods=['GET','POST'])
def adminDashboard():
    try:
        current_user = flask_login.current_user
        if current_user.is_anonymous == True:
            flash('Please login first')
            return render_template('login.html')
        if ((current_user == None) or (current_user.user_type != 'superuser')):
            flash('Please login as an admin')
            return render_template('login.html')
        users = User.query.all()
        employers = User.query.filter_by(user_type='enquirer').count()
        members = User.query.filter_by(user_type='member').count()
        return render_template('dashboard.html',users=users, employers=employers, members=members, current_user=current_user)
    except Exception as e:
        print('error',e)

#memberFee Page
@admin_main_bp.route('/memberFee', methods=['GET','POST'])
def memberFee():
    try:
        current_user = flask_login.current_user
        if current_user.is_anonymous == True:
            flash('Please login first')
            return render_template('login.html')
        if ((current_user == None) or (current_user.user_type != 'superuser')):
            flash('Please login as an admin')
            return render_template('login.html')
        member_fee = MemberFees.query.get(1)
        if request.method == 'GET':
            return render_template('member_fees.html',current_user=current_user,member_fee=member_fee)
        else:
            fee_details = MemberFees.query.get(1)
            post_data = request.form
            print('post_data',post_data)
            aos_standard_addition_per_hour = post_data['aos_standard_addition_per_hour']
            aos_arrears_payments = post_data['aos_arrears_payments']
            aos_one_off_deductions = post_data['aos_one_off_deductions']
            admin_charges_per_hour_pence = post_data['admin_charges_per_hour_pence']
            if ((aos_standard_addition_per_hour == '') or (aos_arrears_payments == '') or (aos_one_off_deductions == '')
            or (admin_charges_per_hour_pence == '')):
                flash('Please fill all the fields')
                return render_template('member_fees.html',current_user=current_user,member_fee=member_fee)
            fee_details.aos_standard_addition_per_hour = aos_standard_addition_per_hour
            fee_details.aos_arrears_payments = aos_arrears_payments
            fee_details.aos_one_off_deductions = aos_one_off_deductions
            fee_details.admin_charges_per_hour_pence = admin_charges_per_hour_pence
            db.session.add(fee_details)
            db.session.commit()
            flash('Update Successfull')
            return render_template('member_fees.html',current_user=current_user,member_fee=member_fee)
        # return json.dumps({'status':'success','message':'Plan updated Successfully'});
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error at line',lNumber,'error is',e)

#memberFee Page
@admin_main_bp.route('/employerFee', methods=['GET','POST'])
def employerFee():
    try:
        current_user = flask_login.current_user
        if current_user.is_anonymous == True:
            flash('Please login first')
            return render_template('login.html')
        if ((current_user == None) or (current_user.user_type != 'superuser')):
            flash('Please login as an admin')
            return render_template('login.html')
        employer_fee = EnquirerFees.query.get(1)
        if request.method == 'GET':
            return render_template('enquirer_fees.html',current_user=current_user,employer_fee=employer_fee)
        else:
            fee_details = EnquirerFees.query.get(1)
            post_data = request.form
            print('post_data',post_data)
            aos_standard_addition_per_hour = post_data['aos_standard_addition_per_hour']
            aos_one_off_misc_payment = post_data['aos_one_off_misc_payment']
            bidding_fees_per_hour_pence = post_data['bidding_fees_per_hour_pence']
            admin_charges_per_hour_pounds = post_data['admin_charges_per_hour_pounds']
            vat = post_data['vat']
            if ((aos_standard_addition_per_hour == '') or (aos_one_off_misc_payment == '') or (bidding_fees_per_hour_pence == '')
            or (admin_charges_per_hour_pounds == '') or (vat == '')):
                flash('Please fill all the fields')
                return render_template('enquirer_fees.html',current_user=current_user,employer_fee=employer_fee)
            fee_details.aos_standard_addition_per_hour = aos_standard_addition_per_hour
            fee_details.aos_one_off_misc_payment = aos_one_off_misc_payment
            fee_details.bidding_fees_per_hour_pence = bidding_fees_per_hour_pence
            fee_details.admin_charges_per_hour_pounds = admin_charges_per_hour_pounds
            fee_details.vat = vat
            db.session.add(fee_details)
            db.session.commit()
            flash('Update Successfull')
            return render_template('enquirer_fees.html',current_user=current_user,employer_fee=employer_fee)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error at line',lNumber,'error is',e)

#VIEW PLANS
@admin_main_bp.route('/plans', methods=['GET'])
def plans():
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            plans = SubscriptionPlans.query.all()
            return render_template('plans.html',plans=plans,current_user=current_user)
        except Exception as e:
            print('error',e)



#VIEW MEMBERS
@admin_main_bp.route('/membersView', methods=['GET'])
def members():
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            users = User.query.filter_by(user_type='member')
            users_list = []
            user_dict = {}
            for user in users:
                user_id = user.id
                user_instance = User.query.get(user_id)
                name = user_instance.name
                is_verified = user_instance.is_verified
                exists = bool(Profile.query.filter_by(user_id = user_id).first())
                if exists:
                    profile_instance = Profile.query.filter_by(user_id = user_id)
                    for profile in profile_instance:
                        phone = profile.contact
                        city = profile.city
                else:
                    phone = ''
                    city = ''
                user_dict['id'] = user_id
                user_dict['email'] = user.email
                user_dict['user_type'] = user.user_type
                user_dict['device_type'] = user.device_type
                user_dict['name'] = name
                user_dict['phone'] = phone
                user_dict['verified'] = is_verified
                user_dict['city'] = city
                user_dict['registered_date'] = user.created_at
                users_list.append(user_dict.copy())
            return render_template('members.html',users=users_list,current_user=current_user)
        except Exception as e:
            print('error',e)

#VIEW ENQUIRER
@admin_main_bp.route('/enquirersView', methods=['GET'])
def enquirers():
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            users = User.query.filter_by(user_type='enquirer')
            users_list = []
            user_dict = {'id':'','email':'','user_type':'','device_type':'',
            'company_name':'','phone':'', 'verified':'','city':'', 'registered_date':''}
            for user in users:
                user_id = user.id
                user_instance = User.query.get(user_id)
                name = user_instance.name
                is_verified = user_instance.is_verified
                exists = bool(EnquirerProfile.query.filter_by(enquirer_id = user_id).first())
                if exists:
                    profile_instance = EnquirerProfile.query.filter_by(enquirer_id = user_id)
                    for profile in profile_instance:
                        phone = profile.contact
                        city = profile.city
                else:
                    phone = ''
                    city = ''
                user_dict['id'] = user_id
                user_dict['email'] = user.email
                user_dict['user_type'] = user.user_type
                user_dict['device_type'] = user.device_type
                user_dict['registered_date'] = user.created_at
                user_dict['company_name'] = name
                user_dict['phone'] = phone
                user_dict['verified'] = is_verified
                user_dict['city'] = city
                users_list.append(user_dict.copy())
            return render_template('enquirers.html',users=users_list,current_user=current_user)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            lNumber = exc_tb.tb_lineno
            print('error at line', lNumber,'error is>>',e)

#GET USERS CHARTS DATA
@admin_main_bp.route('/getUsersChartData', methods=['GET'])
def getUsersChartData():
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            members_jan_count = 0
            members_feb_count = 0
            members_march_count = 0
            members_april_count = 0
            members_may_count = 0
            members_june_count = 0
            members_july_count = 0
            members_aug_count = 0
            members_sep_count = 0
            members_oct_count = 0
            members_nov_count = 0
            members_dec_count = 0
            #Enquirers
            enquirers_jan_count = 0
            enquirers_feb_count = 0
            enquirers_march_count = 0
            enquirers_april_count = 0
            enquirers_may_count = 0
            enquirers_june_count = 0
            enquirers_july_count = 0
            enquirers_aug_count = 0
            enquirers_sep_count = 0
            enquirers_oct_count = 0
            enquirers_nov_count = 0
            enquirers_dec_count = 0
            members_count_list = []
            enquirers_count_list = []
            today = datetime.datetime.now()
            current_month = today.month
            month_value = []
            for i in range(1,current_month+1):
                month_value.append(i)
            months_list = [calendar.month_name[i] for i in month_value]
            members_data = User.query.filter_by(user_type='member').with_entities(sa.func.month(User.created_at), func.count(User.id)).group_by(sa.func.month(User.created_at)).all()
            enquirers_data = User.query.filter_by(user_type='enquirer').with_entities(sa.func.month(User.created_at), func.count(User.id)).group_by(sa.func.month(User.created_at)).all()
            for record in members_data:
                month = record[0]
                count = record[1]
                if month == 1:
                    members_jan_count = count
                if month == 2:
                    members_feb_count = count
                if month == 3:
                    members_march_count = count
                if month == 4:
                    members_april_count = count
                if month == 5:
                    members_may_count = count
                if month == 6:
                    members_june_count = count
                if month == 7:
                    members_july_count = count
                if month == 8:
                    members_aug_count = count
                if month == 9:
                    members_sep_count = count
                if month == 10:
                    members_oct_count = count
                if month == 11:
                    members_nov_count = count
                if month == 12:
                    members_dec_count = count
                members_count_list = [members_jan_count, members_feb_count, members_march_count,
                members_april_count, members_may_count, members_june_count, members_july_count,
                members_aug_count, members_sep_count, members_oct_count, members_nov_count,
                members_dec_count]
            for record in enquirers_data:
                month = record[0]
                count = record[1]
                if month == 1:
                    enquirers_jan_count = count
                if month == 2:
                    enquirers_feb_count = count
                if month == 3:
                    enquirers_march_count = count
                if month == 4:
                    enquirers_april_count = count
                if month == 5:
                    enquirers_may_count = count
                if month == 6:
                    enquirers_june_count = count
                if month == 7:
                    enquirers_july_count = count
                if month == 8:
                    enquirers_aug_count = count
                if month == 9:
                    enquirers_sep_count = count
                if month == 10:
                    enquirers_oct_count = count
                if month == 11:
                    enquirers_nov_count = count
                if month == 12:
                    enquirers_dec_count = count
                enquirers_count_list = [enquirers_jan_count, enquirers_feb_count, enquirers_march_count,
                enquirers_april_count, enquirers_may_count, enquirers_june_count, enquirers_july_count,
                enquirers_aug_count, enquirers_sep_count, enquirers_oct_count, enquirers_nov_count,
                enquirers_dec_count]
            return json.dumps ({'months': months_list, 'enquirers': enquirers_count_list, 'members': members_count_list})
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            lNumber = exc_tb.tb_lineno
            print('error at line', lNumber,'error is', e)


#GET USERS CHARTS DATA
@admin_main_bp.route('/getSubscriptionsChartData', methods=['GET'])
def getSubscriptionsChartData():
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            jan_count = 0
            feb_count = 0
            march_count = 0
            april_count = 0
            may_count = 0
            june_count = 0
            july_count = 0
            aug_count = 0
            sep_count = 0
            oct_count = 0
            nov_count = 0
            dec_count = 0
            price_count_list = []
            today = datetime.datetime.now()
            current_month = today.month
            month_value = []
            for i in range(1,current_month+1):
                month_value.append(i)
            months_list = [calendar.month_name[i] for i in month_value]
            try:
                subscription_data = Subscriptions.query.filter_by(payment_status='approved').with_entities(sa.func.month(Subscriptions.payment_date), Subscriptions.plan).all()
                plans_count_list = [0,0,0,0,0,0,0,0,0,0,0,0]
                #print('---subscription_data',subscription_data)
                for record in subscription_data:
                    month = record[0]
                    plan_id = record[1]
                    plan = SubscriptionPlans.query.get(plan_id)
                    price = plan.price
                    if month == 1:
                        plans_count_list[0] += 1
                        jan_count = price
                    if month == 2:
                        plans_count_list[1] += 1
                        feb_count = price
                    if month == 3:
                        plans_count_list[2] += 1
                        march_count = price
                    if month == 4:
                        plans_count_list[3] += 1
                        april_count = price
                    if month == 5:
                        plans_count_list[4] += 1
                        may_count = price
                    if month == 6:
                        plans_count_list[5] += 1
                        june_count = price
                    if month == 7:
                        plans_count_list[6] += 1
                        july_count = price
                    if month == 8:
                        plans_count_list[7] += 1
                        aug_count = price
                    if month == 9:
                        plans_count_list[8] += 1
                        sep_count = price
                    if month == 10:
                        plans_count_list[9] += 1
                        oct_count = price
                    if month == 11:
                        plans_count_list[10] += 1
                        nov_count = price
                    if month == 12:
                        plans_count_list[11] += 1
                        dec_count = price
                #print('-plans_count_list-',plans_count_list)
                price_count_list = [jan_count, feb_count, march_count, april_count, may_count,
                june_count, july_count, aug_count, sep_count, oct_count, nov_count, dec_count]
                #print('---', price_count_list)
                res_list = [] 
                for i in range(0, len(price_count_list)):
                    if(plans_count_list[i] != 0): 
                        res_list.append(int(price_count_list[i]) * int(plans_count_list[i]))
                    else:
                        res_list.append(int(price_count_list[i]))
            except Exception as e:
                res_list = [0,0,0,0,0,0,0,0,0,0,0,0]
            #print(res_list) 
            return json.dumps ({'months': months_list, 'revenue': res_list})
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            lNumber = exc_tb.tb_lineno
            print('error at line', lNumber,'error is', e)


###########################################PLAN ROUTES###################################################


# Add NEW Plan
@admin_main_bp.route('/addNewPlan/', methods=['GET', 'POST'])
def addNewPlan():
    current_user = flask_login.current_user
    if current_user.is_anonymous == True:
        flash('Please login first')
        return render_template('login.html')
    if ((current_user == None) or (current_user.user_type != 'superuser')):
        flash('Please login as an admin')
        return render_template('login.html')
    if request.method == 'GET':
        return render_template('add_plan.html', mode='add')
    else:
        post_data = request.get_json()
        print('post_data',post_data)
        plan_type= post_data['plan_type']
        plan_name = post_data['plan_name']
        monthly_price = post_data['monthly_plan_price']
        description = post_data.get('description',None)
        print('description',description)
        yearly_price = post_data.get('yearly_plan_price',None)
        monthly_plan_payment = post_data.get('monthly_plan_payment',None)
        yearly_plan_payment = post_data.get('yearly_plan_payment',None)
        link_up_charges = post_data.get('link_up_charges',None)
        reconnection_fees = post_data.get('reconnection_fees',None)
        bidding_fees = post_data.get('bidding_fees',None)
        free_days = post_data.get('free_days',None)
        existing_plan = SubscriptionPlans.query.filter_by(plan_name=plan_name).first()
        print('existing_plan',existing_plan)
        if existing_plan is None:
            plan = SubscriptionPlans(
                plan_type=plan_type,
                plan_name=plan_name,
                description = description,
                monthly_price = monthly_price,
                yearly_price = yearly_price,
                monthly_payment = monthly_plan_payment,
                yearly_payment = yearly_plan_payment,
                reconnection_fees = reconnection_fees,
                link_up_charge = link_up_charges,
                bidding_fees = bidding_fees,
                free_days = free_days
            )
            db.session.add(plan)
            db.session.commit()  # Create new user
            return json.dumps({'status':'success','message':'Plan created Successfully'});
        else:
            return json.dumps({'status':'error','message':'plan with same name already exists'});


# Delete A Plan
@admin_main_bp.route('/deletePlan/', methods=['GET', 'POST'])
def deletePlan():
    current_user = flask_login.current_user
    if current_user.is_anonymous == True:
        flash('Please login first')
        return render_template('login.html')
    if ((current_user == None) or (current_user.user_type != 'superuser')):
        flash('Please login as an admin')
        return render_template('login.html')
    post_data = request.get_json()
    plan_id = post_data['plan_id']
    plan_instance = SubscriptionPlans.query.get(plan_id)
    if plan_instance == None:
        return json.dumps({'status':'error','message':'No such plan exists'});
    db.session.delete(plan_instance)
    db.session.commit()
    return json.dumps({'status':'success','message':'Plan deleted Successfully'});


# Update A Plan
@admin_main_bp.route('/updatePlan/<plan_id>', methods=['GET', 'POST'])
def updatePlan(plan_id):
    # plan_id = id
    plan_instance = SubscriptionPlans.query.get(plan_id)
    if request.method == 'POST':
        plan_instance = SubscriptionPlans.query.get(plan_id)
        post_data = request.get_json()
        plan_type= post_data['plan_type']
        name = post_data['plan_name']
        monthly_price = post_data['monthly_plan_price']
        description = post_data.get('description',None)
        yearly_price = post_data.get('yearly_plan_price',None)
        monthly_plan_payment = post_data.get('monthly_plan_payment',None)
        yearly_plan_payment = post_data.get('yearly_plan_payment',None)
        link_up_charges = post_data.get('link_up_charges',None)
        reconnection_fees = post_data.get('reconnection_fees',None)
        bidding_fees = post_data.get('bidding_fees',None)
        free_days = post_data.get('free_days',None)
        plan_instance.plan_name = name
        plan_instance.plan_type = plan_type
        plan_instance.description = description
        plan_instance.monthly_price = monthly_price
        plan_instance.monthly_payment = monthly_plan_payment
        plan_instance.yearly_price = yearly_price
        plan_instance.yearly_payment = yearly_plan_payment
        plan_instance.link_up_charge = link_up_charges
        plan_instance.reconnection_fees = reconnection_fees
        plan_instance.bidding_fees = bidding_fees
        plan_instance.free_days = free_days
        db.session.add(plan_instance)
        db.session.commit()
        return json.dumps({'status':'success','message':'Plan updated Successfully'});
    else:
        return render_template('add_plan.html', mode='edit',plan=plan_instance)

#######################################################################################################

##########################################Subscription Routes##########################################
#VIEW SUBSCRIPTIONS
@admin_main_bp.route('/subscriptions', methods=['GET','POST'])
def subscriptions():
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            subscriptions_list = []
            subscription_dict = {'id':'','plan':'', 'user':'', 'is_active':'', 'is_cancelled':'',
            'payment_status':'', 'created_on':''}
            # exists = bool(Subscriptions.query.filter_by(payment_status=='pending').filter_by(payment_status=='approved'))
            # print('------exists-',exists)
            subscriptions = Subscriptions.query.filter(Subscriptions.plan_id.isnot(None))
            if subscriptions:
                for data in subscriptions:
                    user_id = data.user
                    id_plan = data.plan_id
                    subscription_id = data.id
                    is_active = data.is_active
                    is_cancelled = data.is_cancelled
                    payment_status = data.payment_status
                    if(payment_status==PaymentStatusEnum.approved):
                        payment = 'approved'
                    if(payment_status==PaymentStatusEnum.pending):
                        payment = 'pending'
                    if(payment_status==PaymentStatusEnum.rejected):
                        payment = 'rejected'
                    created_on = data.created_at
                    user_instance = User.query.get(user_id)
                    user_email = user_instance.email
                    if id_plan != None:
                        plan_instance = SubscriptionPlans.query.get(id_plan)
                        plan_name = plan_instance.plan_name
                    else:
                        plan_name = None
                    subscription_dict['id'] = subscription_id
                    subscription_dict['plan'] = plan_name
                    subscription_dict['user'] = user_email
                    subscription_dict['is_active'] = is_active
                    subscription_dict['is_cancelled'] = is_cancelled
                    subscription_dict['payment_status'] = payment
                    subscription_dict['created_on'] = created_on
                    subscriptions_list.append(subscription_dict.copy())
            else:
                subscriptions_list=[]
            return render_template('subscriptions.html',subscriptions=subscriptions_list,current_user=current_user)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            lNumber = exc_tb.tb_lineno
            print('error at line',lNumber, 'error is',e)

# Add New Subscription
@admin_main_bp.route('/addNewSubscription/', methods=['GET', 'POST'])
def addNewSubscription():
    current_user = flask_login.current_user
    if current_user.is_anonymous == True:
        flash('Please login first')
        return render_template('login.html')
    if ((current_user == None) or (current_user.user_type != 'superuser')):
        flash('Please login as an admin')
        return render_template('login.html')
    if request.method == 'GET':
        members = User.query.filter_by(user_type='member')
        enquirers = User.query.filter_by(user_type='enquirer')
        plans = SubscriptionPlans.query.all()
        users_list = []
        user_dict = {}
        for user in members:
            user_dict['id'] = user.id
            user_dict['email'] = user.email
            users_list.append(user_dict.copy())
        for user in enquirers:
            user_dict['id'] = user.id
            user_dict['email'] = user.email
            users_list.append(user_dict.copy())
        print('--->>>>>>>',users_list) 
        return render_template('add_subscription.html', mode='add', users=users_list, plans=plans)
    else:
        post_data = request.get_json()
        print('--',post_data)
        plan = post_data['plan_name']
        user = post_data['plan_user']
        existing_subscription = Subscriptions.query.filter_by(plan_id=plan).filter_by(user=user).first()
        if existing_subscription is None:
            subscription = Subscriptions(
                plan_id=plan,
                user = user,
                payment_date='1000-01-01 01:01:01'
            )
            db.session.add(subscription)
            db.session.commit()  # Create new subscription
            return json.dumps({'status':'success','message':'Subscription added Successfully'});
        else:
            return json.dumps({'status':'error','message':'Subscription already exists'});


# Delete A Subscription
@admin_main_bp.route('/deleteSubscription/', methods=['GET', 'POST'])
def deleteSubscription():
    post_data = request.get_json()
    subscription_id = post_data['subscription_id']
    subscription_instance = Subscriptions.query.get(subscription_id)
    if subscription_instance == None:
        return json.dumps({'status':'error','message':'No such subscription exists'});
    db.session.delete(subscription_instance)
    db.session.commit()
    return json.dumps({'status':'success','message':'Subscriptions deleted Successfully'});

# Update A Subscription
@admin_main_bp.route('/updateSubscription/<id>', methods=['GET', 'POST'])
def updateSubscription(id):
    subscription_id = id
    get_subscription = Subscriptions.query.get(subscription_id)
    user_id = get_subscription.user
    plan_id = get_subscription.plan_id
    plan_instance = SubscriptionPlans.query.get(plan_id)
    user_instance = User.query.get(user_id)
    user_email = user_instance.email
    plan_name = plan_instance.plan_name
    members = User.query.filter_by(user_type='member')
    enquirers = User.query.filter_by(user_type='enquirer')
    plans = SubscriptionPlans.query.all()
    users_list = []
    user_dict = {}
    for user in members:
        user_dict['id'] = user.id
        user_dict['email'] = user.email
        users_list.append(user_dict.copy())
    for user in enquirers:
        user_dict['id'] = user.id
        user_dict['email'] = user.email
        users_list.append(user_dict.copy())
    if request.method == 'GET':
        return render_template('add_subscription.html', mode='edit',subscription=get_subscription, users=users_list, email=user_email, user_id=user_id, plan_name=plan_name, plan_id=plan_id, plans=plans)
    else:
        post_data = request.get_json()
        plan = post_data['plan_name']
        user = post_data['plan_user']
        get_subscription.plan_id = plan
        get_subscription.user = user
        db.session.add(get_subscription)
        db.session.commit()
        return json.dumps({'status':'success','message':'Subscription updated Successfully'});


#Payments received 
@admin_main_bp.route('/receivedPayments', methods=['POST','GET'])
def received():
    current_user = flask_login.current_user
    if current_user.is_anonymous == True:
        flash('Please login first')
        return render_template('login.html')
    if ((current_user == None) or (current_user.user_type != 'superuser')):
        flash('Please login as an admin')
        return render_template('login.html')
    if request.method == 'GET':
        payments_list = []
        payments_dict = {}
        amount_list = []
        payments = UserPayments.query.all()
        for payment in payments:
            amount = payment.amount
            amount_list.append(int(amount))
            try:
                job_id = payment.job_id
                job_details = Jobs.query.get(job_id)
                payments_dict['business_name'] = job_details.business_name
            except Exception as e:
                pass
            user_id = payment.user_id
            user_instance = User.query.get(user_id)
            payments_dict['amount'] = '£'+str(payment.amount)
            payments_dict['payment_date'] = payment.created_at
            payments_dict['medium'] = payment.medium
            payments_dict['reference'] = payment.reference
            payments_dict['user'] = user_instance.name
            payments_list.append(payments_dict.copy())
        total_amount = '£'+str(sum(amount_list))
        return render_template('payments_received.html',payments_list=payments_list,total_amount=total_amount)

#Payments sent 
@admin_main_bp.route('/jobPayments', methods=['POST','GET'])
def jobPayments():
    current_user = flask_login.current_user
    if current_user.is_anonymous == True:
        flash('Please login first')
        return render_template('login.html')
    if ((current_user == None) or (current_user.user_type != 'superuser')):
        flash('Please login as an admin')
        return render_template('login.html')
    if request.method == 'GET':
        amount_list = []
        payments_list = []
        payments_dict = {}
        job_payments = JobPayments.query.all()
        for instance in job_payments:
            amount = instance.total_amount
            amount_list.append(float(amount))
            status = instance.payment_status
            application_id = instance.application_id
            application = AppliedJobs.query.get(application_id)
            member_id = application.applied_by
            member_instance = User.query.get(member_id)
            job_id = application.job_id
            job_instance = Jobs.query.get(job_id)
            employer_id = job_instance.posted_by
            employer_instance = User.query.get(employer_id)
            business_name = job_instance.business_name 
            payments_dict['amount'] = '£'+str(amount)
            payments_dict['status'] = status
            payments_dict['business_name'] = business_name
            payments_dict['paid_to'] = member_instance.name
            payments_dict['paid_by'] = employer_instance.name
            payments_list.append(payments_dict.copy())
        total_amount = '£'+str(sum(amount_list))
        return render_template('payments_sent.html',payments_list=payments_list,total_amount=total_amount)


#Revenue Generated 
@admin_main_bp.route('/revenue', methods=['POST','GET'])
def revenue():
    current_user = flask_login.current_user
    if current_user.is_anonymous == True:
        flash('Please login first')
        return render_template('login.html')
    if ((current_user == None) or (current_user.user_type != 'superuser')):
        flash('Please login as an admin')
        return render_template('login.html')
    if request.method == 'GET':
        revenue_list = []
        revenue_dict = {}
        amount_list = []
        payments = UserPayments.query.all()
        for payment in payments:
            user_id = payment.user_id
            user_instance = User.query.get(user_id)
            try:
                job_id = payment.job_id
                job_details = Jobs.query.get(job_id)
                revenue_dict['business_name'] = job_details.business_name
                applications_exists = bool(AppliedJobs.query.filter_by(is_funded=True).filter_by(job_id=job_id).first())
                if applications_exists:
                    applications = AppliedJobs.query.filter_by(is_funded=True).filter_by(job_id=job_id)
                    for application in applications:
                        amount = application.brokerage
                        amount_list.append(float(amount))
                        payment_date = str(application.funded_on)
                        payment_date_split = payment_date.split('-')
                        revenue_dict['month'] = payment_date_split[1]
                        revenue_dict['amount'] = '£'+str(application.brokerage)
                        revenue_dict['payment_date'] = str(application.funded_on)
                        revenue_dict['reference'] = 'job funding fees'
            except Exception as e:
                print('in except error',e,payment.id)
                amount = payment.amount
                amount_list.append(int(amount))
                payment_date = str(payment.created_at)
                payment_date_split = payment_date.split('-')
                revenue_dict['month'] = payment_date_split[1]
                revenue_dict['amount'] = '£'+str(payment.amount)
                revenue_dict['payment_date'] = str(payment.created_at)
                revenue_dict['reference'] = payment.reference
            revenue_dict['user'] = user_instance.name
            revenue_dict['user_type'] = user_instance.user_type
            revenue_list.append(revenue_dict.copy())
        # print('amount_list',amount_list)
        total_amount = round(sum(amount_list),2)
        final_amount = '£'+str(total_amount)
        return render_template('revenue.html',revenue_list=revenue_list,total_amount=final_amount)

#Revenue Generated 
@admin_main_bp.route('/filterRevenue/', methods=['POST','GET'])
def filterRevenue():
    revenue_list = []
    revenue_dict = {}
    amount_list = []
    payments = UserPayments.query.all()
    post_data = request.form
    print('post_data',post_data)
    filter_month = post_data['month']
    for payment in payments:
        user_id = payment.user_id
        user_instance = User.query.get(user_id)
        try:
            job_id = payment.job_id
            job_details = Jobs.query.get(job_id)
            revenue_dict['business_name'] = job_details.business_name
            applications_exists = bool(AppliedJobs.query.filter_by(is_funded=True).filter_by(job_id=job_id).first())
            if applications_exists:
                applications = AppliedJobs.query.filter_by(is_funded=True).filter_by(job_id=job_id)
                for application in applications:
                    amount = application.brokerage
                    amount_list.append(float(amount))
                    payment_date = str(application.funded_on)
                    payment_date_split = payment_date.split('-')
                    revenue_dict['month'] = payment_date_split[1]
                    revenue_dict['amount'] = '£'+str(application.brokerage)
                    revenue_dict['payment_date'] = str(application.funded_on)
                    revenue_dict['reference'] = 'job funding fees'
        except Exception as e:
            print('in except error',e,payment.id)
            amount = payment.amount
            amount_list.append(int(amount))
            payment_date = str(payment.created_at)
            payment_date_split = payment_date.split('-')
            revenue_dict['month'] = payment_date_split[1]
            revenue_dict['amount'] = '£'+str(payment.amount)
            revenue_dict['payment_date'] = str(payment.created_at)
            revenue_dict['reference'] = payment.reference
        revenue_dict['user'] = user_instance.name
        revenue_list.append(revenue_dict.copy())
    final_list = []
    final_amount_list = []
    for i in revenue_list:
        if int(i['month']) == int(filter_month):
            amt = i['amount']
            amt = amt.replace('£','')
            final_amount_list.append(float(amt))
            final_list.append(i)
    total_amount = round(sum(final_amount_list),2)
    final_amount = '£'+str(total_amount)
    html = render_template('revenue_table.html',records_list=final_list,total_amount=final_amount)
    return jsonify({'html':html})
################################EMPLOYER DISPUTES#####################################################

#VIEW Employer Disputes
@admin_main_bp.route('/employerDisputes', methods=['GET'])
def employerDisputes():
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            disputes = []
            dispute_dict ={}
            employerDisputes = Disputes.query.all()
            for d in employerDisputes:
                member_id = d.member_id
                member_instance = User.query.get(member_id)
                employer_id = d.submitted_by
                employer_instance = User.query.get(employer_id)
                job_id = d.job_id
                job_instance = Jobs.query.get(job_id)
                business_name = job_instance.business_name
                dispute_dict['id'] = d.id
                dispute_dict['amount'] = d.amount
                dispute_dict['description'] = d.description
                dispute_dict['dispute_type'] = d.dispute_type
                dispute_dict['status'] = d.status
                dispute_dict['created_at'] = d.created_at
                dispute_dict['employer'] = employer_instance.name
                dispute_dict['member'] = member_instance.name
                dispute_dict['job'] = business_name
                disputes.append(dispute_dict.copy())
            return render_template('employer_disputes.html',disputes=disputes,current_user=current_user)
        except Exception as e:
            print('error',e)



#VIEW Wmployer Disputes
@admin_main_bp.route('/viewDispute/<dispute_id>', methods=['GET'])
def viewDispute(dispute_id):
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            dispute_dict ={}
            d = Disputes.query.get(dispute_id)
            member_id = d.member_id
            member_instance = User.query.get(member_id)
            employer_id = d.submitted_by
            employer_instance = User.query.get(employer_id)
            job_id = d.job_id
            job_instance = Jobs.query.get(job_id)
            business_name = job_instance.business_name
            dispute_id = d.id
            dispute_amount = d.amount
            dispute_description = d.description
            dispute_type = d.dispute_type
            dispute_status = d.status
            dispute_created_at = d.created_at
            dispute_employer = employer_instance.name
            dispute_member = member_instance.name
            dispute_job = business_name
            return render_template('view_dispute_details.html',dispute_id=dispute_id,current_user=current_user,
                amount = dispute_amount,description=dispute_description,dispute_type=dispute_type,
                status=dispute_status,created_at=dispute_created_at,employer=dispute_employer,
                member = dispute_member,job=dispute_job)
        except Exception as e:
            print('error',e)

#VIEW Wmployer Disputes
@admin_main_bp.route('/changeStatus/<dispute_id>', methods=['GET','POST'])
def changeStatus(dispute_id):
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            d = Disputes.query.get(dispute_id)
            member_id = d.member_id
            member_instance = User.query.get(member_id)
            employer_id = d.submitted_by
            employer_instance = User.query.get(employer_id)
            job_id = d.job_id
            job_instance = Jobs.query.get(job_id)
            business_name = job_instance.business_name
            dispute_id = d.id
            dispute_amount = d.amount
            dispute_description = d.description
            dispute_type = d.dispute_type
            dispute_status = d.status
            dispute_created_at = d.created_at
            dispute_employer = employer_instance.name
            dispute_member = member_instance.name
            dispute_job = business_name
            return render_template('change_status.html',dispute_id=dispute_id,current_user=current_user,
                amount = dispute_amount,description=dispute_description,dispute_type=dispute_type,
                status=dispute_status,created_at=dispute_created_at,employer=dispute_employer,
                member = dispute_member,job=dispute_job)
        except Exception as e:
            print('error',e)
    else:
        post_data = request.form
        print('post_data',post_data)
        status = post_data['dispute_status']
        dispute_instance = Disputes.query.get(dispute_id)
        dispute_instance.status = status
        db.session.add(dispute_instance)
        db.session.commit()
        flash('Status Updated')
        # url = '/viewDispute/'+str(dispute_id)
        return redirect('/employerDisputes')


# Delete A Dispute
@admin_main_bp.route('/deleteDispute/<dispute_id>', methods=['GET', 'POST'])
def deleteDispute(dispute_id):
    current_user = flask_login.current_user
    if current_user.is_anonymous == True:
        flash('Please login first')
        return render_template('login.html')
    if ((current_user == None) or (current_user.user_type != 'superuser')):
        flash('Please login as an admin')
        return render_template('login.html')
    dispute_instance = Disputes.query.get(dispute_id)
    db.session.delete(dispute_instance)
    db.session.commit()
    return redirect('/employerDisputes')


########################################################################################################


########################################Members Disputes################################################

#VIEW Members Disputes
@admin_main_bp.route('/membersDisputes', methods=['GET'])
def membersDisputes():
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            disputes = []
            dispute_dict ={}
            membersDisputes = MemberDisputes.query.all()
            for d in membersDisputes:
                member_id = d.submitted_by
                member_instance = User.query.get(member_id)
                job_id = d.job_id
                job_instance = Jobs.query.get(job_id)
                business_name = job_instance.business_name
                dispute_dict['id'] = d.id
                dispute_dict['title'] = d.title
                dispute_dict['details'] = d.details
                dispute_dict['images'] = d.images
                dispute_dict['status'] = d.status
                dispute_dict['created_at'] = d.created_at
                dispute_dict['documents'] = d.documents
                dispute_dict['job'] = business_name
                dispute_dict['member'] = member_instance.name
                disputes.append(dispute_dict.copy())
            return render_template('member_disputes.html',disputes=disputes,current_user=current_user)
        except Exception as e:
            print('error',e)

#VIEW Disputes Details
@admin_main_bp.route('/viewMemberDispute/<dispute_id>', methods=['GET'])
def viewMemberDispute(dispute_id):
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            dispute_dict ={}
            d = MemberDisputes.query.get(dispute_id)
            member_id = d.submitted_by
            member_instance = User.query.get(member_id)
            job_id = d.job_id
            job_instance = Jobs.query.get(job_id)
            business_name = job_instance.business_name
            dispute_id = d.id
            dispute_title = d.title
            dispute_details = d.details
            dispute_images = d.images
            dispute_status = d.status
            dispute_created_at = d.created_at
            dispute_member = member_instance.name
            dispute_job = business_name
            return render_template('member_dispute_details.html',dispute_id=dispute_id,current_user=current_user,
                dispute_title = dispute_title,dispute_details=dispute_details,dispute_images=dispute_images,
                status=dispute_status,created_at=dispute_created_at,dispute_member = dispute_member,job=dispute_job)
        except Exception as e:
            print('error',e)


#VIEW Disputes Details
@admin_main_bp.route('/changeDisputeStatus/<dispute_id>', methods=['GET','POST'])
def changeDisputeStatus(dispute_id):
    if request.method == 'GET':
        try:
            current_user = flask_login.current_user
            if current_user.is_anonymous == True:
                flash('Please login first')
                return render_template('login.html')
            if ((current_user == None) or (current_user.user_type != 'superuser')):
                flash('Please login as an admin')
                return render_template('login.html')
            dispute_dict ={}
            d = MemberDisputes.query.get(dispute_id)
            member_id = d.submitted_by
            member_instance = User.query.get(member_id)
            job_id = d.job_id
            job_instance = Jobs.query.get(job_id)
            business_name = job_instance.business_name
            dispute_id = d.id
            dispute_title = d.title
            dispute_details = d.details
            dispute_images = d.images
            dispute_status = d.status
            dispute_created_at = d.created_at
            dispute_member = member_instance.name
            dispute_job = business_name
            return render_template('change_dispute_status.html',dispute_id=dispute_id,current_user=current_user,
                dispute_title = dispute_title,dispute_details=dispute_details,dispute_images=dispute_images,
                status=dispute_status,created_at=dispute_created_at,dispute_member = dispute_member,job=dispute_job)
        except Exception as e:
            print('error',e)
    else:
        post_data = request.form
        print('post_data',post_data)
        status = post_data['dispute_status']
        dispute_instance = MemberDisputes.query.get(dispute_id)
        dispute_instance.status = status
        db.session.add(dispute_instance)
        db.session.commit()
        flash('Status Updated')
        # url = '/viewDispute/'+str(dispute_id)
        return redirect('/membersDisputes')

# Delete A Member Dispute
@admin_main_bp.route('/deleteMemberDispute/<dispute_id>', methods=['GET', 'POST'])
def deleteMemberDispute(dispute_id):
    current_user = flask_login.current_user
    if current_user.is_anonymous == True:
        flash('Please login first')
        return render_template('login.html')
    if ((current_user == None) or (current_user.user_type != 'superuser')):
        flash('Please login as an admin')
        return render_template('login.html')
    dispute_instance = MemberDisputes.query.get(dispute_id)
    db.session.delete(dispute_instance)
    db.session.commit()
    return redirect('/membersDisputes')

#######################################################################################################

@admin_main_bp.route("/logoutAdmin")
def logout():
    logout_user()
    return redirect('/adminLogin')

######################################################################################################

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