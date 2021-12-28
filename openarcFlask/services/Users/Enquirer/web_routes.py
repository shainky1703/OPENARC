"""Routes for user authentication."""
from flask import session, redirect, render_template, flash, Blueprint, request, url_for, jsonify, make_response
from flask_login import current_user, login_user, logout_user
from .models import db, EnquirerProfile, EnquirerProfileSchema, EnquirerNotification
from services.Users import login_manager
from flask import Response
from .token import generate_confirmation_token, confirm_token
from .email import *
import sys,os
from flask_login import login_required
from os import environ, path
from dotenv import load_dotenv
from flask_jwt_extended import create_access_token,create_refresh_token
import re
from services.Users.Enquirer.models import *
from services.Users.Member.models import *
from services.Jobs.models import *
from services.Subscriptions.models import *
from app.main.models import *
from sqlalchemy import desc
from werkzeug.utils import secure_filename
from datetime import date
from dateutil.relativedelta import relativedelta
import stripe
from geopy.geocoders import Nominatim

from xhtml2pdf import pisa 
import jinja2
templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
EMPLOYER_TEMPLATE_FILE = "/templates/invoice.html"
MEMBER_TEMPLATE_FILE = "/templates/member_invoice.html"
employer_template = templateEnv.get_template(EMPLOYER_TEMPLATE_FILE)



basedir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..'))
load_dotenv(path.join(basedir, '.env'))


stripe.api_key = environ.get('STRIPE_SECRET_KEY')

connected_account_id = environ.get('STRIPE_CONNECTED_ACCOUNT')


# Blueprint Configuration
web_routes_bp = Blueprint(
    'web_routes_bp', __name__,
)
server_url='https://arcopen.space/files/uploads/employer/'
members_url='https://arcopen.space/files/uploads/member/'
chats_uploads_url = 'https://arcopen.space/files/uploads/chats/'
local_contracts_uploads = '/var/www/Projects/OpenArc/Push/openarc-flask/media/uploads/Contracts/'
server_contracts_uploads = '/var/www/html/uploads/contracts/'
from_email = environ.get('FROM_EMAIL')
sendgrid_api_key = environ.get('SENDGRID_API_KEY')

def check_email(email):
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'   
    if(re.search(regex,email)):  
        return True  
    else:  
        return False 


def send_email(to, subject, full_name, confirm_url, job_title, mode):
    if mode == 'activation':
        html_content=render_template('Email/account_activation.html',email=to, username=full_name, confirm_url=confirm_url, subject=subject)
    else:
        html_content = render_template('Email/job_invited.html', job_title=job_title, username=to, subject=subject)
    message = Mail(
        from_email=from_email,
        to_emails=[to],
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        code, body, headers = response.status_code, response.body, response.headers
        print(f"Response Code: {code} ")
        print(f"Response Body: {body} ")
        print(f"Response Headers: {headers} ")
        print("Message Sent!")
    except Exception as e:
        print("Error sending jobs email: {0}".format(e))
    return str(response.status_code)

def send_dispute_email(subject, member, employer, job_title):
    html_content = render_template('Email/employer_dispute.html', to="Dispute submission email admin (support@arcopenspace.com)", job_title=job_title, member=member, employer=employer, subject=subject)
    message = Mail(
        from_email=from_email,
        to_emails=['support@arcopenspace.com'],
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        code, body, headers = response.status_code, response.body, response.headers
        print(f"Response Code: {code} ")
        print(f"Response Body: {body} ")
        print(f"Response Headers: {headers} ")
        print("Message Sent!")
    except Exception as e:
        print("Error sending jobs email: {0}".format(e))
    return str(response.status_code)

#SIGNUP
@web_routes_bp.route('/signupEnquirer/', methods=['POST','GET'])
def enquirerSignup():
    try:
        if request.method == 'GET':
            return render_template('Employer/sign-up.html')
        else:
            post_data = request.form
            print('post_data',post_data)
            accept_terms = post_data.get('accept_terms')
            subscribe_check = post_data.get('subscribe_check')
            if accept_terms == 'on':
                pass
            else:
                flash('Please accept the terms and conditions')
                return redirect('/signupEnquirer/')
            full_name = post_data['full_name']
            email = post_data['email']
            password = post_data['password']
            confirm_password = post_data['confirm_password']
            if (password != confirm_password):
                flash('Passwords do not match')
                return redirect('/signupEnquirer/')
            existing_user = User.query.filter_by(email=email).first()
            print('existing_user',existing_user)
            if existing_user:
                flash('User with same email already exists')
                return redirect('/signupEnquirer/')
            if existing_user is None:
                user = User(
                    name=full_name,
                    email=email,
                    user_type = 'enquirer',
                    is_verified = False,
                    device_type="web",
                    device_id="registeredfromweb",
                )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()  # Create new user
            token = generate_confirmation_token(email)
            confirm_url = url_for('web_routes_bp.verify_account', token=token, _external=True)
            subject = "Account Activation email"
            send_email(email, subject, full_name, confirm_url,'','activation')
            login_user(user)
            flash('Employer registration successfull. An email is sent to you for account verification.')
            return redirect('/signupEnquirer/')
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in signup',e, 'at line',lNumber)
        flash(str(e))
        return redirect('/signupEnquirer/')


#CONFIRM EMAIL
@web_routes_bp.route('/confirmAccount/<token>', methods=['GET','POST'])
def verify_account(token):
    try:
        email = confirm_token(token)
    except:
        flash("The confirmation link is invalid or has expired")
        return redirect('/signupEnquirer/')
    user_data = User.query.filter_by(email=email).first_or_404()
    if user_data:
        if user_data.is_verified:
            flash('Account is already verified')
            return redirect('/loginEnquirer/')
        else:
            user_data.is_verified = True
            try:
                local_object = db.session.merge(user_data)
                db.session.add(local_object)
            except Exception as e:
                print('error in commit',e)
                db.session.add(user_data)
            # db.session.add(user_data)
            db.session.commit()
            flash('You have confirmed your account. Thanks!.Please login')
            return redirect('/loginEnquirer/')    

#LOGIN
@web_routes_bp.route('/loginEnquirer/', methods=['POST','GET'])
def enquirerlogin():
    try:
        if request.method == 'GET':
            return render_template('Employer/login.html')
        else:
            post_data = request.form
            print('post_data',post_data)
            email = post_data['user_email']
            password = post_data['password']
            remember_me = post_data.get('remember_me')
            if remember_me:
                remember = True
            else:
                remember = False
            print('remember',remember)
            user_instance = User.query.filter_by(email=email).first()
            if user_instance and user_instance.check_password(password=password):
                if user_instance.is_verified:
                    if user_instance.user_type=='enquirer':
                        login_user(user_instance,remember=remember)
                        return redirect('/dashboard/')
                    else:
                        flash('Not an enquirer account')
                        return redirect('/loginEnquirer/')

                else:
                    flash('Please activate your account first')
                    return redirect('/loginEnquirer/')
            else:
                flash('Invalid Credentials')
                return redirect('/loginEnquirer/')
    except Exception as e:
        print('error in login',e)
        flash(str(e))
        return redirect('/loginEnquirer/')

########################################################FORGOT PASSWORD#########################################
#Forgot Password
@web_routes_bp.route('/forgotPassword/', methods=['POST','GET'])
def forgotPassword():
    try:
        if request.method == 'GET':
            return render_template('Employer/forgot_password.html')
        else:
            post_data = request.form
            email = post_data['email']
            if (email == ''):
                flash("please pass email")
                return redirect('/forgotPassword/')
            is_valid = check_email(email)
            if not is_valid:
                flash("please pass valid email")
                return redirect('/forgotPassword/')
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                name = existing_user.name
                token = generate_confirmation_token(email)
                confirm_url = url_for('web_routes_bp.reset_token_web', token=token, _external=True)
                subject = "Reset password email"
                send_password_reset_email(email, name, subject, confirm_url)
                existing_user.hashcode = token
                try:
                    local_object = db.session.merge(existing_user)
                    db.session.add(local_object)
                except Exception as e:
                    print('error in commit',e)
                    db.session.add(existing_user)
                db.session.commit()
                flash("An email is sent to you for password reset.Please check your email")
                return redirect('/forgotPassword/')
            else:
                flash("No user registered with this email")
    except Exception as e:
        print('error in login',e)
        flash(str(e))
        return redirect('/forgotPassword/')

#RESET TOKEN CONFIRM
@web_routes_bp.route('/passwordReset/<token>', methods=['GET','POST'])
def reset_token_web(token):
    if request.method == 'POST':
        try:
            email = confirm_token(token)
        except:
            flash("The confirmation link is invalid or has expired")
            return redirect(request.url)
        try:
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            if ((password == '') or (confirm_password == '')):
                flash("Please fill both the fields")
                return redirect(request.url)
            if ((password != confirm_password )):
                flash("Passwords do not match")
                return render_template('Employer/reset_password.html')
            user_exists = User.query.filter_by(hashcode=token).first()
            if user_exists:
                #valid token
                password = request.form.get('password')
                user_exists.set_password(password)
                user_exists.hashcode = ''
                try:
                    local_object = db.session.merge(user_exists)
                    db.session.add(local_object)
                except Exception as e:
                    print('error in commit',e)
                    db.session.add(user_exists)
                # db.session.add(user_exists)
                db.session.commit()
                flash('Password reset successfull')
                return redirect('/loginEnquirer/') 
            else:
                flash("no such user")
                return redirect(request.url)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            lNumber = exc_tb.tb_lineno
            print('error at line',lNumber,'error is',e)
            flash("error",str(e))
            return redirect(request.url)
    else:
        return render_template('Employer/reset_password.html')

##################################################################################################################
#Dashboard
@web_routes_bp.route('/dashboard/', methods=['POST','GET'])
def dashboard():
    try:
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    jobs_exists = bool(Jobs.query.filter_by(posted_by=current_user.id).filter_by(is_draft=False).first())
    applications_list = []
    accepted_count_list =  []
    rejected_count_list =  []
    pending_count_list =  []
    jobs_list = []
    job_dict = {}
    if jobs_exists:
        #Applications Count
        jobs = Jobs.query.filter_by(posted_by=current_user.id).filter_by(is_draft=False)
        for job in jobs:
            job_id = job.id
            job_instance = Jobs.query.get(job_id)
            job_dict['id'] = job_id
            job_dict['business_name'] = job_instance.business_name
            job_dict['budget'] = job_instance.budget
            today_date = date.today()
            if job.shift_start_date > today_date:
                status = 'Posted'
            elif (job.shift_start_date <= today_date) and (job.shift_end_date > today_date):
                status = 'Active'
            elif (job.shift_end_date < today_date):
                status = 'Completed'
            else:
                status = 'Posted'
            job_dict['status'] = status
            applications_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).first())
            if applications_exists:
                mem_list=[]
                mem_dict = {}
                applications = AppliedJobs.query.filter_by(job_id=job_id)
                for app in applications:
                    member_id = app.applied_by
                    member_instance = User.query.get(member_id)
                    mem_dict['name'] = member_instance.name
                    profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                    if profile_exists:
                        profile_instance = Profile.query.filter_by(user_id=member_id).first()
                        city = profile_instance.city
                        profile_pic = members_url+profile_instance.profile_pic
                    else:
                        city = ''
                        profile_pic = ''
                    mem_dict['profile_pic'] = profile_pic
                    mem_dict['member_id'] = member_id
                    mem_list.append(mem_dict.copy())
                job_dict['members'] = mem_list
                jobs_list.append(job_dict.copy())
            else:
                jobs_list.append(job_dict.copy())
            applications_count = AppliedJobs.query.filter_by(job_id=job_id).count()
            applications_list.append(applications_count)
            accepted_applications_count = AppliedJobs.query.filter_by(job_id=job_id).filter_by(application_status='approved').count()
            accepted_count_list.append(accepted_applications_count)
            rejected_applications_count = AppliedJobs.query.filter_by(job_id=job_id).filter_by(application_status='rejected').count()
            rejected_count_list.append(rejected_applications_count)
            pending_applications_count = AppliedJobs.query.filter_by(job_id=job_id).filter_by(application_status='pending').count()
            pending_count_list.append(pending_applications_count)
        total_applications = sum(applications_list)
        accepted_applications = sum(accepted_count_list)
        pending_applications = sum(pending_count_list)
        rejected_applications = sum(rejected_count_list)
        #Jobs Counts
        jobs_count = Jobs.query.filter_by(posted_by=current_user.id).count()
        total_jobs = jobs_count
        completed_jobs_exist = bool(JobPayments.query.filter_by(work_status='completed').first())
        if completed_jobs_exist:
            completed_jobs = JobPayments.query.filter_by(work_status='completed')
            completed_jobs_list = []
            for job in completed_jobs:
                application_id = job.application_id
                application_instance = AppliedJobs.query.get(application_id)
                job_id = application_instance.job_id
                job_instance = Jobs.query.get(job_id)
                if ((job_instance.posted_by == current_user.id) and (job_id not in completed_jobs_list)):
                    completed_jobs_list.append(job_id)
            completed_jobs = len(completed_jobs_list)
        else:
            completed_jobs = 0
    else:
        total_jobs = 0
        completed_jobs = 0
        total_applications = 0
        accepted_applications = 0
        rejected_applications = 0
        pending_applications = 0
    if total_jobs != 0 and completed_jobs != 0:
        jobs_percent = (completed_jobs/total_jobs)*100
    else:
        jobs_percent = 0
    if total_applications != 0 and accepted_applications != 0:
        app_percent = (accepted_applications/total_applications)*100
    else:
        app_percent = 0
    if total_applications != 0 and rejected_applications != 0:
        reject_percent = (rejected_applications/total_applications)*100
    else:
        reject_percent = 0
    if total_applications != 0 and pending_applications != 0:
        pending_percent = (pending_applications/total_applications)*100
    else:
        pending_percent = 0
    enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first())
    members = User.query.filter_by(user_type='member')
    members_list = []
    member_dict = {}
    for member in members:
        member_id = member.id
        member_dict['member_id'] = member_id
        member_dict['name'] = member.name
        profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
        if profile_exists:
            profile_instance = Profile.query.filter_by(user_id=member_id).first()
            city = profile_instance.city
            profile_pic = members_url+profile_instance.profile_pic
        else:
            city = ''
            profile_pic = ''
        member_dict['city'] = city
        member_dict['profile_pic'] = profile_pic
        members_list.append(member_dict.copy())
    if enquirer_profile_exists:
        profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
        profile_pic = server_url+str(profile.company_logo)
    else:
        profile_pic = ''
    notifications_list = []
    notification_dict ={}
    notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
    if notifications_exists:
        unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
        total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
        notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
        for n in notifications:
            notification_dict['body'] = n.body
            notification_dict['status'] = n.status
            notification_dict['time'] = n.created_at
            notifications_list.append(notification_dict.copy())
    else:
        unread_count = 0
        total_count = 0
    print('unread',unread_count)
    print('total_count',total_count)
    return render_template('Employer/dashboard.html',profile_pic=profile_pic,total_jobs=total_jobs,
        completed_jobs=completed_jobs,total_applications=total_applications,
        accepted_applications=accepted_applications,jobs_percent=jobs_percent,app_percent=app_percent,
        pending_percent=pending_percent,reject_percent=reject_percent,
        members=members_list,jobs=jobs_list,unread_count=unread_count,
        notifications=notifications_list,total_count=total_count)


#makeRead
@web_routes_bp.route('/makeRead/', methods=['GET'])
def makeRead():
    try:
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').first())
    if notifications_exists:
        notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread')
        for n in notifications:
            n.status='read'
            try:
                local_object = db.session.merge(n)
                db.session.add(local_object)
            except Exception as e:
                print('error in commit',e)
                db.session.add(n)
    db.session.commit()
    return jsonify({'message':'success'})

#getDashboardChartData
@web_routes_bp.route('/getDashboardChartData/', methods=['GET'])
def getDashboardChartData():
    from sqlalchemy import extract
    jobs_count_list = []
    jan_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 1).count()
    feb_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 2).count()
    mar_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 3).count()
    apr_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 4).count()
    may_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 5).count()
    jun_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 6).count()
    jul_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 7).count()
    aug_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 8).count()
    sep_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 9).count()
    oct_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 10).count()
    nov_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 11).count()
    dec_count = Jobs.query.filter_by(posted_by=current_user.id).filter(extract('month', Jobs.shift_start_date) == 12).count()
    jobs_count_list = [jan_count,feb_count,mar_count,apr_count,may_count,jun_count,jul_count,aug_count,sep_count,
    oct_count,nov_count,dec_count]
    return jsonify({'counts':jobs_count_list})


#get Map Data
@web_routes_bp.route('/getMapData/', methods=['GET','POST'])
def getMapData():
    city_list = []
    user_instance = User.query.get(current_user.id)
    jobs_exist = bool(Jobs.query.filter_by(posted_by=current_user.id).filter(Jobs.shift_start_date<=date.today()).filter(Jobs.shift_end_date>=date.today()).filter_by(is_draft=False).first())
    if jobs_exist:
        active_jobs = Jobs.query.filter_by(posted_by=current_user.id).filter(Jobs.shift_start_date<=date.today()).filter(Jobs.shift_end_date>=date.today()).filter_by(is_draft=False)
        for job_instance in active_jobs:
            initial_list = []
            job_id = job_instance.id
            city = job_instance.city
            print('--------------->',city,type(city))
            try:
                city_split = city.split('(')
                city_name = city_split[0]
            except Exception as e:
                city_name = city
            print('city_name',city_name)
            geolocator = Nominatim(user_agent="openarc")
            location = geolocator.geocode(city_name)
            latitude = location.latitude
            longitude = location.longitude
            initial_list.append(city_name)
            initial_list.append(latitude)
            initial_list.append(longitude)
            city_list.append(initial_list)
    return jsonify({'city_list':city_list})

#Explore
@web_routes_bp.route('/explore/', methods=['POST','GET'])
def explore():
    try:
        if request.method == 'GET':
            try:
                print('current_user',current_user.id)
            except Exception as e:
                flash('Please Login Again')
                return redirect('/loginEnquirer/')
            member_dict = {}
            members_list = []
            all_members = User.query.filter_by(user_type='member')
            #All Members
            if all_members:
                for member in all_members:
                    member_id = member.id
                    member_dict['member_id'] = member.id
                    profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                    if profile_exists:
                        profile_instance = Profile.query.filter_by(user_id=member_id).first()
                        per_hour_rate = profile_instance.hourly_rate
                        if '£' in per_hour_rate:
                            per_hour_rate = per_hour_rate
                        else:
                            per_hour_rate = '£'+str(per_hour_rate)
                        city = profile_instance.city
                        profile_pic = members_url+profile_instance.profile_pic
                    else:
                        per_hour_rate = '£10'
                        city = ''
                        profile_pic = ''
                    #Rating
                    stars_list = []
                    reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).first())
                    if reviews_exist:
                        reviews = Reviews.query.filter_by(member_id=member_id)
                        for review in reviews:
                                stars = review.employer_stars
                                stars_list.append(int(stars))
                                total = sum(stars_list)
                                count = len(stars_list)
                                avg = total/count
                    else:
                        avg = 0
                    saved = bool(SavedMembers.query.filter_by(member_id=member_id).filter_by(saved_by=current_user.id).first())
                    member_dict['saved'] = saved
                    member_dict['member_id'] = member_id
                    member_dict['member_name'] = member.name
                    member_dict['rating'] = int(avg)
                    member_dict['per_hour_rate'] = per_hour_rate
                    member_dict['city'] = city
                    member_dict['profile_pic'] = profile_pic
                    members_list.append(member_dict.copy())
            ###High Rated
            high_rated_list = sorted(members_list, key = lambda i: i['rating'],reverse=True)
            # print('lennn',len(high_rated_list))
            enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
            if enquirer_profile_exists:
                profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
                profile_pic = server_url+str(profile.company_logo)
            else:
                profile_pic = ''
            notifications_list = []
            notification_dict ={}
            notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
            if notifications_exists:
                unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
                total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
                notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
                for n in notifications:
                    notification_dict['body'] = n.body
                    notification_dict['status'] = n.status
                    notification_dict['time'] = n.created_at
                    notifications_list.append(notification_dict.copy())
            else:
                unread_count = 0
                total_count = 0
            return render_template('Employer/explore.html',profile_pic=profile_pic, all_members=members_list,
                high_rated=high_rated_list,unread_count=unread_count,total_count=total_count,
                notifications=notifications_list)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in dashboard at line', lNumber,'error is',e)
        flash(str(e))
        return redirect('/loginEnquirer/')

#Get Memebr Details
@web_routes_bp.route('/getMemberProfile/', methods=['POST'])
def getMemberProfile():
    if request.method == 'POST':
        member_dict = {}
        member_id = request.form['member_id']
        member_details = User.query.get(member_id)
        member_dict['name'] = member_details.name
        member_dict['member_id'] = member_details.id
        member_dict['badge_number'] = member_details.badge_number
        #Rating
        stars_list = []
        reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).first())
        if reviews_exist:
            reviews = Reviews.query.filter_by(member_id=member_id)
            for review in reviews:
                    stars = review.employer_stars
                    stars_list.append(int(stars))
                    total = sum(stars_list)
                    count = len(stars_list)
                    avg = total/count
        else:
            avg = 0
        member_dict['rating'] = int(avg)
        member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
        if member_profile_exists:
            member_profile = Profile.query.filter_by(user_id=member_id).first()
            member_profile_pic = members_url+member_profile.profile_pic
            city = member_profile.city
            about = member_profile.about
            hourly_rate = member_profile.hourly_rate
            document = members_url+member_profile.documents
        else:
            member_profile_pic = ''
            city = ''
            about = ''
            hourly_rate = '£10'
            document = ''
        jobs_count = 0
        completed_jobs_exist = bool(JobPayments.query.filter_by(work_status='completed').first())
        if completed_jobs_exist:
            completed_jobs = JobPayments.query.filter_by(work_status='completed')
            for j in completed_jobs:
                application_id = j.application_id
                application_instance = AppliedJobs.query.get(application_id)
                if application_instance.applied_by == member_id:
                    jobs_count += 1 
        print('jobs_count',jobs_count)
        member_dict['profile_pic'] = member_profile_pic
        member_dict['city'] = city
        member_dict['about'] = about
        member_dict['hourly_rate'] = hourly_rate
        member_dict['document'] = document
        member_dict['jobs_count'] = jobs_count
        html = render_template('Employer/resume_modal.html',member_dict=member_dict,jobs_count=jobs_count)
        return jsonify({'html':html})


#Get Filtered Details
@web_routes_bp.route('/getFilteredData/', methods=['POST'])
def getFilteredData():
    if request.method == 'POST':
        print(request.form)
        city_list = request.form.getlist("city_array[]")
        new_city_list = []
        for city in city_list:
            city_name = city.split(' ')[0]
            new_city_list.append(city_name)
        rating = request.form.get('rating')
        price = request.form.get('price')
        members_list = []
        member_dict = {}
        all_members = User.query.filter_by(user_type='member')
        for member in all_members:
            member_id = member.id
            member_dict['name'] = member.name
            member_dict['member_id'] = member.id
            member_dict['badge_number'] = member.badge_number
            #Rating
            stars_list = []
            reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).first())
            if reviews_exist:
                reviews = Reviews.query.filter_by(member_id=member_id)
                for review in reviews:
                        stars = review.employer_stars
                        stars_list.append(int(stars))
                        total = sum(stars_list)
                        count = len(stars_list)
                        avg = round(total/count,1)
            else:
                avg = 0
            member_dict['rating'] = int(avg)
            member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
            if member_profile_exists:
                member_profile = Profile.query.filter_by(user_id=member_id).first()
                member_profile_pic = members_url+member_profile.profile_pic
                city = member_profile.city
                about = member_profile.about
                hourly_rate = member_profile.hourly_rate
                document = members_url+member_profile.documents
            else:
                member_profile_pic = ''
                city = ''
                about = ''
                hourly_rate = '10'
                document = ''
            member_dict['profile_pic'] = member_profile_pic
            member_dict['city'] = city
            member_dict['about'] = about
            member_dict['hourly_rate'] = hourly_rate
            member_dict['document'] = document
            # member_dict['jobs_count'] = jobs_count
            members_list.append(member_dict.copy())
        filtered_list = []
        try:
            if len(new_city_list)>0:
                for d in members_list:
                    for c in new_city_list:
                        # print('c',c)
                        member_city = d['city']
                        if c in member_city:
                            filtered_list.append(d)
            else:
                filtered_list = members_list
        except Exception as e:
            filtered_list = members_list
            print('no city')
        res_filtered_list = list(filtered_list)
        try:
            if price:
                print('price',price)
                if price == 'Less than £10':
                    for i in range (0,len(filtered_list)):
                        member_price = filtered_list[i]['hourly_rate']
                        member_price = member_price.replace('£','')
                        if int(member_price) > 10:
                            res_filtered_list.remove(filtered_list[i])
                if price == '£10 - £20':
                    for i in range (0,len(filtered_list)):
                        member_price = filtered_list[i]['hourly_rate']
                        member_price = member_price.replace('£','')
                        if int(member_price) < 10 or int(member_price) >= 20:
                            res_filtered_list.remove(filtered_list[i])
                if price == '£20 - £30':
                    for  i in range (0,len(filtered_list)):
                        member_price = filtered_list[i]['hourly_rate']
                        member_price = member_price.replace('£','')
                        if int(member_price) < 20 or int(member_price) > 30:
                            res_filtered_list.remove(filtered_list[i])
                if price == 'More than £30':
                    for i in range (0,len(filtered_list)):
                        member_price = filtered_list[i]['hourly_rate']
                        member_price = member_price.replace('£','')
                        if int(member_price) < 30:
                            res_filtered_list.remove(filtered_list[i])
        except Exception as e:
            filtered_list = members_list
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            lNumber = exc_tb.tb_lineno
            print('error in price at line', lNumber,'error is',e)
        try:
            if rating == '1':
                print('1')
                for i in range (0,len(filtered_list)):
                    member_rating = filtered_list[i]['rating']
                    if int(member_rating) > 1:
                        res_filtered_list.remove(filtered_list[i])
            if rating == '2':
                print('2')
                for i in range (0,len(filtered_list)):
                    member_rating = filtered_list[i]['rating']
                    if int(member_rating) > 2 or int(member_rating) < 2:
                        res_filtered_list.remove(filtered_list[i])
            if rating == '3':
                print('3')
                for i in range (0,len(filtered_list)):
                    member_rating = filtered_list[i]['rating']
                    if int(member_rating) > 3 or int(member_rating) < 3:
                        res_filtered_list.remove(filtered_list[i])
            if rating == '4':
                print('4')
                for i in range (0,len(filtered_list)):
                    member_rating = filtered_list[i]['rating']
                    if int(member_rating) > 4 or int(member_rating) < 4:
                        res_filtered_list.remove(filtered_list[i])
            if rating == '5':
                print('5')
                for i in range (0,len(filtered_list)):
                    member_rating = filtered_list[i]['rating']
                    if int(member_rating) < 5:
                        res_filtered_list.remove(filtered_list[i])
        except Exception as e:
            filtered_list = members_list
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            lNumber = exc_tb.tb_lineno
            print('error in rating at line', lNumber,'error is',e)
        # print('final',filtered_list)
        html = render_template('Employer/filtered_members.html',filtered_members=res_filtered_list)
        return jsonify({'html':html})


#Save Member
@web_routes_bp.route('/saveMember/<member_id>/', methods=['GET','POST'])
def saveMember(member_id):
    try:
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    saved_instance = SavedMembers(
            member_id = member_id,
            saved_by = current_user.id,
        )
    try:
        local_object = db.session.merge(saved_instance)
        db.session.add(local_object)
    except Exception as e:
        print('error in commit',e)
        db.session.add(saved_instance)
    db.session.commit()
    return redirect ('/explore/')


#Chats Page
@web_routes_bp.route('/chats/', methods=['POST','GET'])
def chats():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        messages_list = []
        message_dict = {}
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
                profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
                profile_pic = server_url+str(profile.company_logo)
        else:
            profile_pic = ''
        sent_messages = ChatHistory.query.filter_by(sent_by=current_user.id)
        received_messages = ChatHistory.query.filter_by(sent_to=current_user.id)
        q3 = sent_messages.union(received_messages)
        for message in q3:
            print('q3',message.message)
            if str(message.sent_by) == str(current_user.id):
                message_direction = 'sent'
                member_id = message.sent_to
            else:
                message_direction = 'received'
                member_id = message.sent_by
            member_instance = User.query.get(member_id)
            try:
                member_name = member_instance.name
                member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                if member_profile_exists:
                    member_profile = Profile.query.filter_by(user_id=member_id).first()
                    member_profile_pic = members_url+member_profile.profile_pic
                else:
                    member_profile_pic = ''
                can_send = True 
                msg = message.message
                time = message.created_at
                try:
                    if message.document == '':
                        document_sent = ''
                    else:
                        document_sent = chats_uploads_url+message.document
                except Exception as e:
                    document_sent = ''
                message_dict['document_name'] = document_sent
                message_dict['document_string'] = document_sent
                message_dict['message'] = msg
                message_dict['time'] = time
                message_dict['employer'] = current_user.id
                message_dict['member_name'] = member_name
                message_dict['member_id'] = member_id
                message_dict['member_profile_pic'] = member_profile_pic
                message_dict['sent_or_received'] = message_direction
                messages_list.append(message_dict.copy())
                messages_list.sort(key = lambda x:x['time'])
            except Exception as e:
                pass
        # print('messages_list',messages_list)
        last_messages = list({v['member_id']:v for v in messages_list}.values())
        # print('test---------',last_messages)
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/chat.html',profile_pic=profile_pic,
            messages=last_messages,all_messages=messages_list,notifications=notifications_list,
            total_count=total_count,unread_count=unread_count)


#Chats Page
@web_routes_bp.route('/chats/<guard_id>/', methods=['POST','GET'])
def chatMessages(guard_id):
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        messages_list = []
        message_dict = {}
        selected_guard_dict = {}
        selected_member = User.query.get(guard_id)
        member_name = selected_member.name
        member_profile_exists = bool(Profile.query.filter_by(user_id=guard_id).first())
        if member_profile_exists:
            member_profile = Profile.query.filter_by(user_id=guard_id).first()
            member_profile_pic = members_url+member_profile.profile_pic
        else:
            member_profile_pic = ''
        selected_guard_dict['document_name'] = ''
        selected_guard_dict['document_string'] = ''
        selected_guard_dict['message'] = ''
        selected_guard_dict['time'] = ''
        selected_guard_dict['employer'] = current_user.id
        selected_guard_dict['member_name'] = member_name
        selected_guard_dict['member_id'] = guard_id
        selected_guard_dict['member_profile_pic'] = member_profile_pic
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
                profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
                profile_pic = server_url+str(profile.company_logo)
        else:
            profile_pic = ''
        sent_messages = ChatHistory.query.filter_by(sent_by=current_user.id)
        received_messages = ChatHistory.query.filter_by(sent_to=current_user.id)
        q3 = sent_messages.union(received_messages)
        for message in q3:
            print('q3',message.message)
            if str(message.sent_by) == str(current_user.id):
                message_direction = 'sent'
                member_id = message.sent_to
            else:
                message_direction = 'received'
                member_id = message.sent_by
            member_instance = User.query.get(member_id)
            try:
                member_name = member_instance.name
                member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                if member_profile_exists:
                    member_profile = Profile.query.filter_by(user_id=member_id).first()
                    member_profile_pic = members_url+member_profile.profile_pic
                else:
                    member_profile_pic = ''
                can_send = True 
                msg = message.message
                time = message.created_at
                try:
                    if message.document == '':
                        document_sent = ''
                    else:
                        document_sent = chats_uploads_url+message.document
                except Exception as e:
                    document_sent = ''
                message_dict['document_name'] = document_sent
                message_dict['document_string'] = document_sent
                message_dict['message'] = msg
                message_dict['time'] = time
                message_dict['employer'] = current_user.id
                message_dict['member_name'] = member_name
                message_dict['member_id'] = member_id
                message_dict['member_profile_pic'] = member_profile_pic
                message_dict['sent_or_received'] = message_direction
                messages_list.append(message_dict.copy())
                messages_list.sort(key = lambda x:x['time'])
            except Exception as e:
                pass
        selected_sent_messages = bool(ChatHistory.query.filter_by(sent_by=guard_id).filter_by(sent_to=current_user.id).first())
        selected_received_messages = bool(ChatHistory.query.filter_by(sent_to=guard_id).filter_by(sent_by=current_user.id).first())
        if selected_sent_messages or selected_received_messages:
            pass
            for i in range(0,len(messages_list)):
                if int(messages_list[i]['member_id']) == int(guard_id):
                    messages_list.insert(0,messages_list.pop(i))
                    break
        else:
            messages_list.insert(0,selected_guard_dict)
        # print('messages_list-->',messages_list)
        last_messages = list({v['member_id']:v for v in messages_list}.values())
        # print('test---------',last_messages)
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/chat.html',profile_pic=profile_pic,messages=last_messages,
            all_messages=messages_list,notifications=notifications_list,
            total_count=total_count,unread_count=unread_count)

#Get User Messages
@web_routes_bp.route('/getUserMessages/', methods=['POST'])
def getUserMessages():
    if request.method == 'POST':
        print('here---------',request.form)
        messages_list = []
        message_dict = {}
        member_id = request.form['member_id']
        print('---member_id',member_id)
        sent_messages = ChatHistory.query.filter_by(sent_by=member_id).filter_by(sent_to=current_user.id).order_by(desc(ChatHistory.created_at))
        received_messages = ChatHistory.query.filter_by(sent_to=member_id).filter_by(sent_by=current_user.id).order_by(desc(ChatHistory.created_at))
        q3 = sent_messages.union(received_messages)
        for message in q3:
            print('message>>>',message)
            if message:
                print('q3',message.message)
                if str(message.sent_by) == str(member_id):
                    message_direction = 'sent'
                else:
                    message_direction = 'received'
                member_instance = User.query.get(member_id)
                member_name = member_instance.name
                member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                if member_profile_exists:
                    member_profile = Profile.query.filter_by(user_id=member_id).first()
                    member_profile_pic = members_url+member_profile.profile_pic
                else:
                    member_profile_pic = ''
                can_send = True 
                msg = message.message
                time = message.created_at
                try:
                    if message.document == '':
                        document_sent = ''
                    else:
                        document_sent = chats_uploads_url+message.document
                except Exception as e:
                    document_sent = ''
                message_dict['document_name'] = document_sent
                message_dict['document_string'] = document_sent
                message_dict['message'] = msg
                message_dict['time'] = time
                # message_dict['employer'] = current_user.id
                message_dict['member_name'] = member_name
                message_dict['member_id'] = member_id
                message_dict['member_profile_pic'] = member_profile_pic
                message_dict['sent_or_received'] = message_direction
                messages_list.append(message_dict.copy())
                messages_list.sort(key = lambda x:x['time'])
        # else:
        #     member_instance = User.query.get(member_id)
        #     member_name = member_instance.name
        #     member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
        #     if member_profile_exists:
        #         member_profile = Profile.query.filter_by(user_id=member_id).first()
        #         member_profile_pic = members_url+member_profile.profile_pic
        #     else:
        #         member_profile_pic = ''
        #     message_dict['member_name'] = member_name
        #     message_dict['member_id'] = member_id
        #     message_dict['member_profile_pic'] = member_profile_pic
        #     messages_list.append(message_dict.copy())
        print('test---------',messages_list)
        html = render_template('Employer/update_chat.html',all_messages=messages_list)
        return jsonify({'html':html})

#Send Messages
@web_routes_bp.route('/sendMessage/', methods=['POST'])
def sendMessage():
    if request.method == 'POST':
        print('here---------',request.form)
        messages_list = []
        message_dict = {}
        member_id = request.form['member_id']
        message = request.form['message']
        message_instance = ChatHistory(
            message = message,
            sent_by = current_user.id,
            sent_to = member_id
            )
        try:
            local_object = db.session.merge(message_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(message_instance)
        db.session.commit()
        ###get messages #####
        sent_messages = ChatHistory.query.filter_by(sent_by=member_id).filter_by(sent_to=current_user.id).order_by(desc(ChatHistory.created_at))
        received_messages = ChatHistory.query.filter_by(sent_to=member_id).filter_by(sent_by=current_user.id).order_by(desc(ChatHistory.created_at))
        q3 = sent_messages.union(received_messages)
        for message in q3:
            print('q3',message.message)
            if str(message.sent_by) == str(member_id):
                message_direction = 'sent'
            else:
                message_direction = 'received'
            member_instance = User.query.get(member_id)
            member_name = member_instance.name
            member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
            if member_profile_exists:
                member_profile = Profile.query.filter_by(user_id=member_id).first()
                member_profile_pic = members_url+member_profile.profile_pic
            else:
                member_profile_pic = ''
            can_send = True 
            msg = message.message
            time = message.created_at
            try:
                if message.document == '':
                    document_sent = ''
                else:
                    document_sent = chats_uploads_url+message.document
            except Exception as e:
                document_sent = ''
            message_dict['document_name'] = document_sent
            message_dict['document_string'] = document_sent
            message_dict['message'] = msg
            message_dict['time'] = time
            # message_dict['employer'] = current_user.id
            message_dict['member_name'] = member_name
            message_dict['member_id'] = member_id
            message_dict['member_profile_pic'] = member_profile_pic
            message_dict['sent_or_received'] = message_direction
            messages_list.append(message_dict.copy())
            messages_list.sort(key = lambda x:x['time'])
        # print('test---------',last_messages)
        html = render_template('Employer/update_chat.html',all_messages=messages_list)
        return jsonify({'html':html})

#Get Users 
@web_routes_bp.route('/searchUser/', methods=['POST'])
def searchUser():
    if request.method == 'POST':
        print('here---------',request.form)
        messages_list = []
        message_dict = {}
        query_string = request.form['query_string']
        print('---query_string',query_string)
        sent_messages = ChatHistory.query.filter_by(sent_by=current_user.id)
        received_messages = ChatHistory.query.filter_by(sent_to=current_user.id)
        q3 = sent_messages.union(received_messages)
        for message in q3:
            # print('q3',message.message)
            if str(message.sent_by) == str(current_user.id):
                message_direction = 'sent'
                member_id = message.sent_to
            else:
                message_direction = 'received'
                member_id = message.sent_by
            member_instance = User.query.get(member_id)
            member_name = member_instance.name
            member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
            if member_profile_exists:
                member_profile = Profile.query.filter_by(user_id=member_id).first()
                member_profile_pic = members_url+member_profile.profile_pic
            else:
                member_profile_pic = ''
            can_send = True 
            msg = message.message
            time = message.created_at
            try:
                if message.document == '':
                    document_sent = ''
                else:
                    document_sent = chats_uploads_url+message.document
            except Exception as e:
                document_sent = ''
            message_dict['document_name'] = document_sent
            message_dict['document_string'] = document_sent
            message_dict['message'] = msg
            message_dict['time'] = time
            # message_dict['employer'] = current_user.id
            message_dict['member_name'] = member_name
            message_dict['member_id'] = member_id
            message_dict['member_profile_pic'] = member_profile_pic
            message_dict['sent_or_received'] = message_direction
            print('query',query_string,'member_name',member_name)
            if query_string in member_name:
                print('in iff') 
                messages_list.append(message_dict.copy())
                messages_list.sort(key = lambda x:x['time'])
            else:
                print('in else')
                # messages_list.append(message_dict.copy())
        # print('test---------',last_messages)
        last_messages = list({v['member_id']:v for v in messages_list}.values())
        html = render_template('Employer/search_users.html',messages=last_messages)
        return jsonify({'html':html})

#Finances
@web_routes_bp.route('/financeDetails/', methods=['POST','GET'])
def finances():
    try:
        if request.method == 'GET':
            try:
                print('current_user',current_user.id)
            except Exception as e:
                flash('Please Login Again')
                return redirect('/loginEnquirer/')
            paid_finances_list = []
            paid_finance_dict = {}
            unpaid_finances_list = []
            unpaid_finance_dict = {}    
            enquirer_instance = User.query.get(current_user.id)
            company = enquirer_instance.name
            enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
            if enquirer_profile_exists:
                profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
                profile_pic = server_url+str(profile.company_logo)
            else:
                profile_pic = ''
            #Finance Details
            jobs_exist = bool(Jobs.query.filter_by(posted_by=current_user.id).first())
            if jobs_exist:
                user_jobs = Jobs.query.filter_by(posted_by=current_user.id)
                application_id_list = []
                jobs_list = []
                for job in user_jobs:
                    job_instance = Jobs.query.get(job.id)
                    job_type = job_instance.job_type
                    application_exists = bool(AppliedJobs.query.filter_by(job_id=job.id).first())
                    if application_exists:
                        application_details = AppliedJobs.query.filter_by(job_id=job.id).first()
                        application_id = application_details.id
                        if application_details.is_active:
                            pass
                        else:
                            jobs_list.append(job.id)
                            application_id_list.append(application_id)
                print('application_id_list',application_id_list)
                funded_amount_list = []
                for app_id in application_id_list:
                    application = AppliedJobs.query.get(app_id)
                    funded_amount = application.funded_amount
                    if funded_amount != '':
                        funded_amount_list.append(float(funded_amount))
                    member_id = application.applied_by
                    member_instance = User.query.get(member_id)
                    member_name = member_instance.name
                    member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first()) 
                    if member_profile_exists:
                        profile = Profile.query.filter_by(user_id=member_id).first()
                        member_profile_pic = members_url+str(profile.profile_pic)
                    else:
                        member_profile_pic = ''
                    reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).first())
                    if reviews_exist:
                        stars_list = []
                        reviews = Reviews.query.filter_by(member_id=member_id)
                        for review in reviews:
                                stars = review.employer_stars
                                stars_list.append(int(stars))
                                total = sum(stars_list)
                                count = len(stars_list)
                                avg = int(total/count)
                    else:
                        avg = 0
                    rec_exists = bool(JobPayments.query.filter_by(application_id=app_id).first())
                    if rec_exists:
                        record_data = JobPayments.query.filter_by(application_id=app_id).first()
                        if (record_data.work_status == 'completed'):
                            paid_amount_list = []
                            if record_data.payment_status == 'paid':
                                paid_amount_list.append(float(record_data.total_amount))
                                paid_finance_dict['transaction_id']= record_data.id
                                paid_finance_dict['job_type']= job_type
                                paid_finance_dict['amount']= record_data.total_amount
                                paid_finance_dict['date']= record_data.updated_at
                                paid_finance_dict['company']= company
                                paid_finance_dict['member']= member_name
                                paid_finance_dict['member_profile_pic']= member_profile_pic
                                paid_finance_dict['rating']= avg
                                paid_finances_list.append(paid_finance_dict.copy())
                            else:
                                unpaid_finance_dict['transaction_id']= record_data.id
                                unpaid_finance_dict['job_type']= job_type
                                unpaid_finance_dict['amount']= record_data.total_amount
                                unpaid_finance_dict['date']= record_data.updated_at
                                unpaid_finance_dict['company']= company
                                unpaid_finance_dict['member']= member_name
                                unpaid_finance_dict['member_profile_pic']= member_profile_pic
                                unpaid_finance_dict['rating']= avg
                                unpaid_finances_list.append(unpaid_finance_dict.copy())
                try:
                    total_amount = sum(paid_amount_list)
                except Exception as e:
                    total_amount = 0
                mydate = datetime.datetime.now()
                month_name = mydate.strftime("%B")
                current_year = mydate.year
                print('current_year',current_year)
                print('jobs',jobs_list)
                total_jobs = str(len(jobs_list)) + ' jobs completed till ' + month_name +' '+ str(current_year)
                funded_amount = sum(funded_amount_list)
            else:
                total_amount = 0
                total_jobs = 0
                funded_amount = 0
            notifications_list = []
            notification_dict ={}
            notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
            if notifications_exists:
                unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
                total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
                notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
                for n in notifications:
                    notification_dict['body'] = n.body
                    notification_dict['status'] = n.status
                    notification_dict['time'] = n.created_at
                    notifications_list.append(notification_dict.copy())
            else:
                unread_count = 0
                total_count = 0
            return render_template('Employer/finances.html',profile_pic=profile_pic,paid_finances=paid_finances_list,
                unpaid_finances=unpaid_finances_list,total_amount=total_amount,total_jobs=total_jobs,
                funded_amount=funded_amount,notifications=notifications_list,
                total_count=total_count,unread_count=unread_count)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in finances at line', lNumber,'error is',e)
        flash(str(e))
        return redirect('/loginEnquirer/')

#Get Details For An Invoice
@web_routes_bp.route('/getDetailsInvoice/', methods=['POST'])
def getDetailsInvoice():
    if request.method == 'POST':
        invoice_list = []
        invoice_dict = {}
        invoice_id = request.form['invoice_id']
        print('---invoice_id',invoice_id)
        invoice_details = JobPayments.query.get(invoice_id)
        application_id = invoice_details.application_id
        application_instance = AppliedJobs.query.get(application_id)
        member_id = application_instance.applied_by
        member_instance = User.query.get(member_id)
        member_name = member_instance.name
        invoice_dict['invoice_id'] = invoice_id
        invoice_dict['date_paid'] = invoice_details.updated_at
        invoice_dict['total_hours'] = invoice_details.total_hours
        invoice_dict['total_amount'] = '£'+str(invoice_details.total_amount)
        application_id = invoice_details.application_id
        application_instance = AppliedJobs.query.get(application_id)
        invoice_dict['hourly_rate'] = '£'+str(application_instance.pay_expected)+'/hr'
        job_id = application_instance.job_id
        job_instance = Jobs.query.get(job_id)
        employer_id = job_instance.posted_by
        invoice_dict['start_date'] = job_instance.shift_start_date
        invoice_dict['end_date'] = job_instance.shift_end_date
        employer_instance = User.query.get(employer_id)
        invoice_dict['employer_name'] = employer_instance.name
        try:
            body = {
                "data":{
                    "company_name": employer_instance.name,
                    "amount": '£'+str(invoice_details.total_amount),
                    "employee": member_name,
                    "start_date": job_instance.shift_start_date,
                    "end_date": job_instance.shift_end_date,
                    "total_hours": invoice_details.total_hours,
                    "hourly_rate": '£'+str(application_instance.pay_expected)+'/hr',
                    "payment_date": invoice_details.updated_at,
                }
            }
            sourceHtml = employer_template.render(json_data=body["data"]) 
            outputFilename = str(employer_id)+"_"+"invoice.pdf"
            # resultFile = open('/var/www/Projects/OpenArc/Push/openarc-flask/'+outputFilename, "w+b")
            resultFile = open('/var/www/html/uploads/employer/'+outputFilename, "w+b")
            filepath = 'https://arcopen.space/files/uploads/employer/'+outputFilename
            # convert HTML to PDF
            pisaStatus = pisa.CreatePDF(
                    src=sourceHtml,            # the HTML to convert
                    dest=resultFile)           # file handle to receive result

            # close output file
            resultFile.close()
        except Exception as e:
            print('error in download invoice',e)
            filepath = ''
        invoice_dict['file_link'] = filepath
        invoice_list.append(invoice_dict)
        return jsonify({'invoice':invoice_list})

#Get Details For An Invoice
@web_routes_bp.route('/getUnpaidInvoice/', methods=['POST'])
def getUnpaidInvoice():
    if request.method == 'POST':
        invoice_list = []
        invoice_dict = {}
        invoice_id = request.form['invoice_id']
        print('---invoice_id',invoice_id)
        invoice_details = JobPayments.query.get(invoice_id)
        application_id = invoice_details.application_id
        application_instance = AppliedJobs.query.get(application_id)
        member_id = application_instance.applied_by
        member_instance = User.query.get(member_id)
        member_name = member_instance.name
        invoice_dict['invoice_id'] = invoice_id
        invoice_dict['date_paid'] = invoice_details.updated_at
        invoice_dict['total_hours'] = invoice_details.total_hours
        invoice_dict['total_amount'] = '£'+str(invoice_details.total_amount)
        application_id = invoice_details.application_id
        application_instance = AppliedJobs.query.get(application_id)
        job_id = application_instance.job_id
        invoice_dict['hourly_rate'] = '£'+str(application_instance.pay_expected)+'/hr'
        job_id = application_instance.job_id
        job_instance = Jobs.query.get(job_id)
        employer_id = job_instance.posted_by
        invoice_dict['start_date'] = job_instance.shift_start_date
        invoice_dict['end_date'] = job_instance.shift_end_date
        employer_instance = User.query.get(employer_id)
        invoice_dict['employer_name'] = employer_instance.name
        invoice_dict['member_id'] = member_id
        invoice_dict['job_id'] = job_id
        try:
            body = {
                "data":{
                    "company_name": employer_instance.name,
                    "amount": '£'+str(invoice_details.total_amount),
                    "employee": member_name,
                    "start_date": job_instance.shift_start_date,
                    "end_date": job_instance.shift_end_date,
                    "total_hours": invoice_details.total_hours,
                    "hourly_rate": '£'+str(application_instance.pay_expected)+'/hr',
                }
            }
            sourceHtml = employer_template.render(json_data=body["data"]) 
            outputFilename = str(employer_id)+"_"+"invoice.pdf"
            # resultFile = open('/var/www/Projects/OpenArc/Push/openarc-flask/'+outputFilename, "w+b")
            resultFile = open('/var/www/html/uploads/employer/'+outputFilename, "w+b")
            filepath = 'https://arcopen.space/files/uploads/employer/'+outputFilename
            # convert HTML to PDF
            pisaStatus = pisa.CreatePDF(
                    src=sourceHtml,            # the HTML to convert
                    dest=resultFile)           # file handle to receive result

            # close output file
            resultFile.close()
        except Exception as e:
            print('error in download unpaid invoice',e)
            filepath = ''
        invoice_dict['file_link'] = filepath
        invoice_list.append(invoice_dict)
        return jsonify({'invoice':invoice_list})


#Make Payment To Employee
@web_routes_bp.route("/payToEmployee/", methods=['POST'])
def payToEmployee():
    try:
        ###############Sent Data######################
        post_data = request.form
        print(post_data)
        amount = post_data['amount']
        if '£' in amount:
            amount = amount.replace('£','')
        else:
            amount = amount
        employee_id = post_data['member_id']
        job_id = post_data['job_id']
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
                return jsonify({'message':'Connected Id not found'}) 
        else:
            return jsonify({'message':'No stripe details found'}) 
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
        return jsonify({'message':'success'}) 
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error paying employee at line',lNumber,'error',e)
        return jsonify({'message':str(e)})


#JOB Listing Page
@web_routes_bp.route('/jobListing/', methods=['POST','GET'])
def jobsListing():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        jobs_list = []
        job_dict = {} 
        drafts_list = []
        drafts_dict = {}
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        jobs_exists = bool(Jobs.query.filter_by(posted_by=current_user.id).first())
        if jobs_exists:
            jobs = Jobs.query.filter_by(posted_by=current_user.id)
            for job in jobs:
                if job.is_draft == False:
                    job_dict['job_id'] = job.id
                    job_dict['city'] = job.city
                    job_dict['business_name'] = job.business_name
                    job_dict['job_description'] = job.job_description
                    start_date = job.shift_start_date
                    today_date = date.today()
                    delta = start_date - today_date
                    days_remaining = delta.days
                    if days_remaining < 0:
                        days_left = 0
                    else:
                        days_left = int(days_remaining)
                    job_dict['days_left'] = days_left
                    jobs_list.append(job_dict.copy())
                else:
                    drafts_dict['job_id'] = job.id
                    drafts_dict['city'] = job.city
                    drafts_dict['business_name'] = job.business_name
                    drafts_dict['job_description'] = job.job_description
                    start_date = job.shift_start_date
                    today_date = date.today()
                    delta = start_date - today_date
                    days_remaining = delta.days
                    if days_remaining < 0:
                        days_left = 0
                    else:
                        days_left = int(days_remaining)
                    drafts_dict['days_left'] = days_left
                    drafts_list.append(drafts_dict.copy())
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/job-listing.html',profile_pic=profile_pic,
            jobs=jobs_list,draft_jobs=drafts_list,total_count=total_count,
            unread_count=unread_count,notifications=notifications)


#Subscriptions
@web_routes_bp.route('/subscriptionDetails/', methods=['POST','GET'])
def subscriptionDetails():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        try:
            subscription_exists = bool(Subscriptions.query.filter_by(user=current_user.id).first())
            print('>>>>>>>>>>>>>>>>>>>>>>>>',subscription_exists)
            if subscription_exists:
                subscription_details = Subscriptions.query.filter_by(user=current_user.id).first()
                billing_cycle = subscription_details.billing_cycle
                payment_date = subscription_details.payment_date
                plan_id = subscription_details.plan_id
                plan_instance = SubscriptionPlans.query.get(plan_id)
                current_plan = plan_instance.plan_name
                if billing_cycle == 'monthly':
                    expiry_date = payment_date + relativedelta(months=+1)
                else:
                    expiry_date = payment_date + relativedelta(months=+12)
            else:
                current_plan = 'Free'
                employer_instance = User.query.get(current_user.id)
                start_date = employer_instance.created_at
                three_months = start_date + relativedelta(months=+3)
                expiry_date = three_months
        except Exception as e:
            pass
        employer_plans_list = []
        employer_plans_dict = {}
        employer_plans = SubscriptionPlans.query.filter(SubscriptionPlans.plan_type !='Member')
        for plan in employer_plans:
            employer_plans_dict['plan_id']=plan.id
            employer_plans_dict['description']=plan.description 
            employer_plans_dict['discount']=plan.discount  
            employer_plans_dict['name']=plan.plan_name
            employer_plans_dict['free_days']=plan.free_days
            try:
                price = plan.monthly_price
                price = price.replace('£','')
                price_value = price.split('+')[0]
            except Exception as e:
                print('eee',e)
                price_value = plan.monthly_price
            print('----',price_value)
            employer_plans_dict['monthly_price']=price_value
            employer_plans_dict['yearly_price']=plan.yearly_price
            employer_plans_dict['created_at']=plan.created_at
            employer_plans_dict['updated_at']=plan.updated_at
            employer_plans_dict['plan_type']=plan.plan_type
            employer_plans_list.append(employer_plans_dict.copy())
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/subscriptions.html',profile_pic=profile_pic,
            employer_plans=employer_plans_list,current_plan=current_plan,expiry_date=expiry_date,
            notifications=notifications_list,unread_count=unread_count,
            total_count=total_count)


#Subscriptions
@web_routes_bp.route('/subscriptionBilling/<plan_id>/', methods=['POST','GET'])
def subscriptionBilling(plan_id):
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        plan_dict = {}
        plan_details = SubscriptionPlans.query.get(plan_id)
        plan_dict['name'] = plan_details.plan_name
        plan_dict['monthly_payment'] = plan_details.monthly_payment
        plan_dict['yearly_payment'] = plan_details.yearly_payment
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/subscription_billing.html',profile_pic=profile_pic,
            plan_id=plan_id,plan_details=plan_dict,notifications=notifications_list,
            total_count=total_count,unread_count=unread_count)
    else:
        print('here',request.form)
        post_data = request.form
        plan_id = plan_id
        billing_cycle = post_data['billing_cycle']
        plan_instance = SubscriptionPlans.query.get(plan_id)
        if (billing_cycle == '') or (billing_cycle == None):
            flash('Please Select billing cycle')
            url="/subscriptionBilling/"+plan_id+'/'
            return redirect(url)
        card_number = post_data['card_number']
        exp_month = post_data['exp_month']
        exp_year = post_data['exp_year']
        cvv = post_data['cvv']
        if ((exp_month == '') or (card_number == '') or (exp_year == '') or (cvv == '')):
            flash('Please provide card details')
            url="/subscriptionBilling/"+plan_id+'/'
            return redirect(url)
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
        import math
        f=math.floor(float(final_price))
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
        payable_amount = int(f)*100
        charge = stripe.Charge.create(
          amount=payable_amount,
          currency=currency,
          description='For Subscription',
          source=token,
        )
        account_id = connected_account_id
        transfer_amount = (int(f)*100)
        print('transfer_amount',transfer_amount,account_id)
        if account_id:
            transfer = stripe.Transfer.create(
              amount=int(transfer_amount),
              currency='gbp',
              destination= account_id,
              transfer_group="Subscription Payment"
            )
        print('transfer done')
        ##Add Payment details
        payment_instance = UserPayments(
                reference = 'Subscription',
                medium = 'card',
                amount = f,
                user_id = current_user.id
            )
        print('intent_created')
        try:
            local_object = db.session.merge(payment_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(payment_instance)
        ##########Add Subscription Details################
        ###Create/Update Subscription Plan
        subscription_exists = bool(Subscriptions.query.filter_by(user=current_user.id).first())
        if subscription_exists:
            subscription_instance = Subscriptions.query.filter_by(user=current_user.id).first()
            subscription_instance.plan_id = plan_id
            subscription_instance.billing_cycle = billing_cycle
            subscription_instance.user = current_user.id
            subscription_instance.is_active = True
            subscription_instance.payment_date = datetime.datetime.now()
            subscription_instance.payment_status = PaymentStatusEnum.approved
        else:
            subscription_instance = Subscriptions(
                    plan_id = plan_id,
                    billing_cycle = billing_cycle,
                    user = current_user.id,
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
        flash('Subscription Selected Successfully')
        return redirect('/subscriptionDetails/')


#Saved
@web_routes_bp.route('/saved/', methods=['POST','GET'])
def saved():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        drafts_list = []
        draft_dict = {}
        drafts_exist = bool(Jobs.query.filter_by(posted_by=current_user.id).filter_by(is_draft=True).first())
        if drafts_exist:
            drafts = Jobs.query.filter_by(posted_by=current_user.id).filter_by(is_draft=True)
            for draft in drafts:
                draft_dict['id'] = draft.id
                draft_dict['shift_start_date'] = draft.shift_start_date
                draft_dict['shift_end_date'] = draft.shift_end_date
                draft_dict['shift_start_time'] = draft.shift_start_time
                draft_dict['shift_end_time'] = draft.shift_end_time
                draft_dict['business_name'] = draft.business_name
                draft_dict['job_category'] = draft.job_category
                draft_dict['company_name'] = current_user.name
                draft_dict['budget'] = draft.budget
                draft_dict['city'] = draft.city
                drafts_list.append(draft_dict.copy())
        saved_members_list = []
        saved_member_dict ={}
        saved_exists = bool(SavedMembers.query.filter_by(saved_by=current_user.id).first())
        if saved_exists:
            saved_members = SavedMembers.query.filter_by(saved_by=current_user.id)
            for member in saved_members:
                member_id = member.member_id
                saved_member_dict['instance_id'] = member.id
                saved_member_dict['member_id'] = member_id
                member_instance = User.query.get(member_id)
                member_name = member_instance.name
                saved_member_dict['member_name'] = member_name
                reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).first())
                stars_list = []
                if reviews_exist:
                    reviews = Reviews.query.filter_by(member_id=member_id)
                    for review in reviews:
                            stars = review.employer_stars
                            stars_list.append(int(stars))
                            total = sum(stars_list)
                            count = len(stars_list)
                            avg = total/count
                else:
                    avg = 0
                saved_member_dict['avg'] = avg
                member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first()) 
                if member_profile_exists:
                    profile = Profile.query.filter_by(user_id=member_id).first()
                    profile_pic = members_url+profile.profile_pic
                else:
                    profile_pic = ''
                saved_member_dict['profile_pic'] = profile_pic
                saved_members_list.append(saved_member_dict.copy())
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/saved.html',profile_pic=profile_pic,drafts=drafts_list,
            saved_members=saved_members_list,unread_count=unread_count,
            total_count=total_count,notifications=notifications_list)


#Saved
@web_routes_bp.route('/removeSavedMember/<instance_id>', methods=['POST','GET'])
def removeSavedMember(instance_id):
    try:
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    get_profile = SavedMembers.query.get(instance_id)
    try:
        local_object = db.session.merge(get_profile)
        db.session.delete(local_object)
    except Exception as e:
        print('error in commit',e)
        db.session.delete(get_profile)
    db.session.commit()
    flash('Removed Successfully')
    return redirect('/saved/')


#Disputes
@web_routes_bp.route('/disputes/', methods=['POST','GET'])
def disputes():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        disputes_list = []
        dispute_dict = {}
        disputes_exists = bool(Disputes.query.filter_by(submitted_by=current_user.id).first())
        if disputes_exists:
            disputes = Disputes.query.filter_by(submitted_by=current_user.id)
            for dispute in disputes:
                dispute_dict['id']=dispute.id
                dispute_dict['dispute_type']=dispute.dispute_type
                dispute_dict['created_at']=dispute.created_at
                dispute_dict['description']=dispute.description
                dispute_dict['status']=dispute.status
                disputes_list.append(dispute_dict.copy())
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        past_projects = []
        jobs_list = []
        past_projects_dict = {}
        completed_instance_exists = bool(JobPayments.query.filter_by(work_status='completed').first())
        if completed_instance_exists:
            completed_instances = JobPayments.query.filter_by(work_status='completed')
            for instance in completed_instances:
                amount = instance.total_amount
                application_id = instance.application_id
                application_instances = AppliedJobs.query.filter_by(id=application_id).filter_by(is_active=False)
                for application in application_instances:
                    job_id = application.job_id
                    job_instance = Jobs.query.get(job_id)
                    job_id = job_instance.id
                    employer = job_instance.posted_by
                    print('employer',employer,'current_user',current_user.id)
                    if employer == current_user.id:
                        business_name = job_instance.business_name 
                        city = job_instance.city
                        applications = AppliedJobs.query.filter_by(job_id=job_id)
                        amounts_list = []
                        for app_instance in applications:
                            app_id = app_instance.id
                            pay_instance_exists = bool(JobPayments.query.filter_by(application_id=app_id).first())
                            if pay_instance_exists:
                                pay_instance = JobPayments.query.filter_by(application_id=app_id).first()
                                amount = pay_instance.total_amount
                                amounts_list.append(float(amount))
                            # print('amounts_list',amounts_list)
                        total_amount = sum(amounts_list)
                        # print('total_amount',total_amount,'job_id',job_id)
                        applications_count = AppliedJobs.query.filter_by(job_id=job_id).count()
                        # print('applications_count',applications_count)
                        if applications_count > 1:
                            applicants_count = applications_count-1
                        app_job_id = application.job_id
                        applicant_id = application.applied_by
                        applicant_instance = User.query.get(applicant_id)
                        applicant_name = applicant_instance.name
                        if applications_count > 1:
                            applicants = applicant_name + ' + ' + str(applicants_count) + ' other members worked'
                        else:
                            applicants = applicant_name + ' has worked'
                        city = job_instance.city 
                        try:
                            city_name = city.split('(')[0]
                        except Exception as e:
                            city_name = city
                        if job_id in jobs_list:
                            pass
                        else:
                            past_projects_dict['applications_count'] = '£'+str(applications_count)
                            past_projects_dict['total_amount'] = '£'+str(round(total_amount,2))
                            past_projects_dict['job_id'] = job_id
                            past_projects_dict['business_name'] = business_name
                            past_projects_dict['applicants'] = applicants
                            past_projects_dict['city'] = city_name
                            past_projects_dict['status'] = 'completed'
                            jobs_list.append(job_id)
                            past_projects.append(past_projects_dict.copy())
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/disputes.html',profile_pic=profile_pic,disputes=disputes_list,
            past_projects=past_projects,notifications=notifications_list,
            unread_count=unread_count,total_count=total_count)
    else:
        print('>>>>>>>>>>>',request.form)
        try:
            dispute = Disputes(
                    dispute_type=request.form.get('dispute_type'),
                    amount='£'+str(request.form.get('budget')),
                    submitted_by = current_user.id,
                    description=request.form.get('description'),
                    job_id = request.form.get('job'),
                    member_id = request.form.get('member')
                )
            db.session.add(dispute)
            db.session.commit()  # Create new dispute
            flash('Saved Successfully')
            subject = "Dispute Raised"
            member_id = request.form.get('member')
            member_instance = User.query.get(member_id)
            member_name = member_instance.name
            employer_instance = User.query.get(current_user.id)
            employer_name = employer_instance.name
            job_id = request.form.get('job')
            job_details = Jobs.query.get(job_id)
            business_name = job_details.business_name
            try:
                send_dispute_email(subject, member_name, employer_name, business_name)
            except Exception as e:
                print('error in dispute email',e)
            return redirect('/disputes/')
        except Exception as e:
            print('error',e)
            flash('Error occured')
            return redirect('/disputes/')

#get Memebers
@web_routes_bp.route('/getApplicants/', methods=['GET','POST'])
def getApplicants():
    applicants_list = []
    applicant_dict = {}
    job_id = request.form['job_id']
    applications = AppliedJobs.query.filter_by(job_id=job_id).filter_by(application_status='approved')
    for application in applications:
        applicant_id = application.applied_by
        applicant_dict['applicant_id'] = applicant_id
        member_instance = User.query.get(applicant_id)
        applicant_dict['guard_name'] = member_instance.name
        applicants_list.append(applicant_dict.copy())
    return jsonify({'applicants':applicants_list})



#Jobs
@web_routes_bp.route('/jobs/', methods=['POST','GET'])
def jobs():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        ##Posted##
        posted_projects = []
        user_instance = User.query.get(current_user.id)
        posted_projects_dict = {}
        posted_jobs_exist = bool(Jobs.query.filter_by(posted_by=current_user.id).filter_by(is_draft=False).first())
        print('???',posted_jobs_exist)
        if posted_jobs_exist:
            posted_jobs = Jobs.query.filter_by(posted_by=current_user.id).filter_by(is_draft=False)
            for job_instance in posted_jobs:
                job_id = job_instance.id
                start_date = job_instance.shift_start_date
                today_date = date.today()
                delta = start_date - today_date
                days_remaining = delta.days
                print('days_remaining',days_remaining)
                if days_remaining > 0:
                    business_name = job_instance.business_name
                    budget = job_instance.budget
                    applications_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).first())
                    if applications_exists:
                        applications = AppliedJobs.query.filter_by(job_id=job_id)
                        applications_count = AppliedJobs.query.filter_by(job_id=job_id).count()
                        print('applications_count',applications_count)
                        if applications_count > 1:
                            applicants_count = applications_count-1
                        for application in applications:
                            applicant_id = application.applied_by
                            applicant_instance = User.query.get(applicant_id)
                            applicant_name = applicant_instance.name
                            if applications_count > 1:
                                applicants = applicant_name + ' + ' + str(applicants_count) + ' members applied'
                            else:
                                applicants = applicant_name + ' has applied'
                    else:
                        applicants = 0
                        applications_count = 0
                    # applicants = job_instance.interested_count
                    city = job_instance.city
                    try:
                        city_name = city.split('(')[0]
                    except Exception as e:
                        city_name = city 
                    posted_projects_dict['applications_count'] = applications_count
                    posted_projects_dict['job_id'] = job_id
                    posted_projects_dict['business_name'] = business_name
                    posted_projects_dict['days_remaining'] = days_remaining
                    posted_projects_dict['company_name'] = user_instance.name
                    posted_projects_dict['applicants'] = applicants
                    posted_projects_dict['city'] = city_name
                    posted_projects_dict['budget'] = budget
                    posted_projects.append(posted_projects_dict.copy())
        ####Past Projects#########
        past_projects = []
        jobs_list = []
        past_projects_dict = {}
        completed_instance_exists = bool(JobPayments.query.filter_by(work_status='completed').first())
        if completed_instance_exists:
            completed_instances = JobPayments.query.filter_by(work_status='completed')
            for instance in completed_instances:
                amount = instance.total_amount
                application_id = instance.application_id
                application_instances = AppliedJobs.query.filter_by(id=application_id).filter_by(is_active=False)
                for application in application_instances:
                    job_id = application.job_id
                    job_instance = Jobs.query.get(job_id)
                    job_id = job_instance.id
                    employer = job_instance.posted_by
                    print('employer',employer,'current_user',current_user.id)
                    if employer == current_user.id:
                        business_name = job_instance.business_name 
                        city = job_instance.city
                        applications = AppliedJobs.query.filter_by(job_id=job_id)
                        amounts_list = []
                        for app_instance in applications:
                            app_id = app_instance.id
                            pay_instance_exists = bool(JobPayments.query.filter_by(application_id=app_id).first())
                            if pay_instance_exists:
                                pay_instance = JobPayments.query.filter_by(application_id=app_id).first()
                                amount = pay_instance.total_amount
                                amounts_list.append(float(amount))
                            # print('amounts_list',amounts_list)
                        total_amount = sum(amounts_list)
                        # print('total_amount',total_amount,'job_id',job_id)
                        applications_count = AppliedJobs.query.filter_by(job_id=job_id).count()
                        # print('applications_count',applications_count)
                        if applications_count > 1:
                            applicants_count = applications_count-1
                        app_job_id = application.job_id
                        applicant_id = application.applied_by
                        applicant_instance = User.query.get(applicant_id)
                        applicant_name = applicant_instance.name
                        if applications_count > 1:
                            applicants = applicant_name + ' + ' + str(applicants_count) + ' other members worked'
                        else:
                            applicants = applicant_name + ' has worked'
                        city = job_instance.city 
                        try:
                            city_name = city.split('(')[0]
                        except Exception as e:
                            city_name = city
                        if job_id in jobs_list:
                            pass
                        else:
                            past_projects_dict['applications_count'] = '£'+str(applications_count)
                            past_projects_dict['total_amount'] = '£'+str(round(total_amount,2))
                            past_projects_dict['job_id'] = job_id
                            past_projects_dict['business_name'] = business_name
                            past_projects_dict['company_name'] = user_instance.name
                            past_projects_dict['applicants'] = applicants
                            past_projects_dict['city'] = city_name
                            past_projects_dict['status'] = 'completed'
                            jobs_list.append(job_id)
                            past_projects.append(past_projects_dict.copy())
        #######Active#################
        active_projects = []
        jobs_list = []
        user_instance = User.query.get(current_user.id)
        active_projects_dict = {}
        jobs_exist = bool(Jobs.query.filter_by(posted_by=current_user.id).filter(Jobs.shift_start_date<=date.today()).filter(Jobs.shift_end_date>=date.today()).filter_by(is_draft=False).first())
        if jobs_exist:
            active_jobs = Jobs.query.filter_by(posted_by=current_user.id).filter(Jobs.shift_start_date<=date.today()).filter(Jobs.shift_end_date>=date.today()).filter_by(is_draft=False)
            for job_instance in active_jobs:
                job_id = job_instance.id
                start_date = job_instance.shift_start_date
                today_date = date.today()
                delta = start_date - today_date
                days_remaining = delta.days
                business_name = job_instance.business_name
                budget = job_instance.budget
                applications_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).first())
                if applications_exists:
                    applications = AppliedJobs.query.filter_by(job_id=job_id)
                    applications_count = AppliedJobs.query.filter_by(job_id=job_id).count()
                    print('applications_count',applications_count)
                    if applications_count > 1:
                        applicants_count = applications_count-1
                    for application in applications:
                        is_active = application.is_active
                        app_job_id = application.job_id
                        if is_active:
                            applicant_id = application.applied_by
                            applicant_instance = User.query.get(applicant_id)
                            applicant_name = applicant_instance.name
                            if applications_count > 1:
                                applicants = applicant_name + ' + ' + str(applicants_count) + ' members are working'
                            else:
                                applicants = applicant_name + ' is working'
                            city = job_instance.city
                            try:
                                city_name = city.split('(')[0]
                            except Exception as e:
                                city_name = city
                            if app_job_id in jobs_list:
                                pass
                            else:
                                active_projects_dict['applications_count'] = applications_count
                                active_projects_dict['job_id'] = job_id
                                active_projects_dict['business_name'] = business_name
                                active_projects_dict['days_remaining'] = days_remaining
                                active_projects_dict['company_name'] = user_instance.name
                                active_projects_dict['applicants'] = applicants
                                active_projects_dict['city'] = city_name
                                active_projects_dict['budget'] = budget
                                jobs_list.append(app_job_id)
                                active_projects.append(active_projects_dict.copy())
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        print('active_projects',active_projects)
        return render_template('Employer/jobs.html',profile_pic=profile_pic,active_projects=active_projects,
            past_projects=past_projects,posted_projects=posted_projects,notifications=notifications_list,
            unread_count=unread_count,total_count=total_count)


#Ongoing Job Details
@web_routes_bp.route('/jobsgoing/<job_id>', methods=['POST','GET'])
def jobsgoing(job_id):
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        job_dict = {}
        job_details = Jobs.query.get(job_id)
        job_dict['id'] = job_details.id
        job_dict['business_name'] = job_details.business_name
        job_dict['job_type'] = job_details.job_type
        shift_start_date_db = job_details.shift_start_date
        shift_end_date_db = job_details.shift_end_date
        mydate1 = datetime.datetime.strptime(str(shift_start_date_db), '%Y-%m-%d')
        mydate2 = datetime.datetime.strptime(str(shift_end_date_db), '%Y-%m-%d')
        shift_start_date = mydate1.strftime('%B %d, %Y')
        shift_end_date = mydate2.strftime('%B %d, %Y')
        job_dict['shift_start_date'] = shift_start_date
        job_dict['shift_end_date'] = shift_end_date
        job_dict['job_description'] = job_details.job_description
        hired_members_list = []
        hired_member_dict={}
        hired_members_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).filter_by(is_active=True).first())
        if hired_members_exists:
            job_applications =  AppliedJobs.query.filter_by(job_id=job_id).filter_by(is_active=True)
            for application in job_applications:
                application_id = application.id
                # member_details_dict['application_id'] = application_id
                today_date = date.today()
                mydate3 = datetime.datetime.strptime(str(today_date), '%Y-%m-%d')
                date_today = mydate3.strftime('%B %d, %Y')
                member_id = application.applied_by
                member_instance = User.query.get(member_id)
                member_name = member_instance.name
                profile_instance_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                if profile_instance_exists:
                    profile_instance = Profile.query.filter_by(user_id=member_id).first()
                    profile_pic = members_url+profile_instance.profile_pic
                    city = profile_instance.city
                else:
                    profile_pic = ''
                    city = ''
                job_log_exists = bool(StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).first())
                if job_log_exists:
                    job_log = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).first()
                    end_time = job_log.end_time
                    print('end_time',end_time)
                    if str(end_time) == '00:00:00':
                        member_status = 'active'
                        clock_in = job_log.start_time
                    else:
                        member_status = job_log.member_status
                        clock_in = ''
                else:
                    member_status = 'away'
                    clock_in = ''
                hired_member_dict['member_id'] = member_id
                hired_member_dict['clock_in'] = clock_in
                hired_member_dict['member_status'] = member_status
                hired_member_dict['city'] = city
                hired_member_dict['application_id'] = application_id
                hired_member_dict['profile_pic'] = profile_pic
                hired_member_dict['member_name'] = member_name
                hired_member_dict['today_date'] = date_today
                hired_members_list.append(hired_member_dict.copy())
        print('hired_members',hired_members_list)
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/jobs-going.html',profile_pic=profile_pic,job_dict=job_dict,
            hired_members=hired_members_list,notifications=notifications_list,
            unread_count=unread_count,total_count=total_count)

#getMemberTodayHistory
@web_routes_bp.route('/getMemberTodayHistory/', methods=['POST'])
def getMemberTodayHistory():
    if request.method == 'POST':
        member_dict = {}
        # today_date = date.today()
        application_id = request.form['application_id']
        application_details = AppliedJobs.query.get(application_id)
        member_id = application_details.applied_by
        member_details = User.query.get(member_id)
        member_dict['name'] = member_details.name
        member_dict['member_id'] = member_details.id
        member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
        if member_profile_exists:
            member_profile = Profile.query.filter_by(user_id=member_id).first()
            member_profile_pic = members_url+member_profile.profile_pic
            hourly_rate = member_profile.hourly_rate
            city = member_profile.city
            city_str = city.split('(')
            city_name = city_str[0]
        else:
            member_profile_pic = ''
            hourly_rate = '£10'
            city_name = ''
        if city_name:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent='openarc')
            location = geolocator.geocode(city)
            latitude = location.latitude
            longitude = location.longitude
            member_dict['latitude'] = latitude
            member_dict['longitude'] = longitude
        member_dict['profile_pic'] = member_profile_pic
        member_dict['city'] = city
        member_dict['hourly_rate'] = hourly_rate
        #Rating
        stars_list = []
        reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).first())
        if reviews_exist:
            reviews = Reviews.query.filter_by(member_id=member_id)
            for review in reviews:
                    stars = review.employer_stars
                    stars_list.append(int(stars))
                    total = sum(stars_list)
                    count = len(stars_list)
                    avg = total/count
        else:
            avg = 0
        member_dict['rating'] = avg
        logs_list =[]
        log_dict ={}
        print('today----------------------',date.today())
        log_exists = bool(StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=date.today()).first())
        if log_exists:
            log = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=date.today()).first()
            end_time = log.end_time
            print('end_time',end_time)
            if str(end_time) == '00:00:00':
                member_status = 'active'
            else:
                member_status = job_log.member_status
            log = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=date.today()).first()
            date_work = log.date
            mydate = datetime.datetime.strptime(str(date_work), '%Y-%m-%d')
            work_date = mydate.strftime('%B %d, %Y')
            start_time = log.start_time
            end_time = log.end_time
            hours = log.hours
            after_hours = log.after_hours
        else:
            member_status = 'away'
            work_date = ''
            start_time = ''
            end_time = ''
            hours = ''
            after_hours = ''
        log_dict['work_date'] = work_date
        log_dict['member_status'] = member_status
        log_dict['start_time'] = start_time
        log_dict['end_time'] = end_time
        log_dict['hours'] = hours
        log_dict['after_hours'] = after_hours
        # logs_list.append(log_dict.copy())
        html = render_template('Employer/job-going-details.html',member_dict=member_dict,logs=log_dict)
        return jsonify({'html':html})

#Posted Job Details
@web_routes_bp.route('/jobsList/<job_id>/', methods=['POST','GET'])
def jobsList(job_id):
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        job_details_dict = {}
        job_details = Jobs.query.get(job_id)
        job_details_dict['id'] = job_details.id
        job_details_dict['business_name'] = job_details.business_name
        job_details_dict['job_description'] = job_details.job_description
        job_details_dict['shift_start_date'] = job_details.shift_start_date
        job_details_dict['budget'] = job_details.budget
        applicants_list = []
        applicant_dict = {}
        applications_exist = bool(AppliedJobs.query.filter_by(job_id=job_id).first())
        if applications_exist:
            applications= AppliedJobs.query.filter_by(job_id=job_id)
            for application in applications:
                applicant_dict['application_id'] = application.id
                applicant_dict['message'] = application.message
                status = application.application_status
                if status == AppliedJobStatusEnum.approved:
                    app_status = 'Approved'
                elif status == AppliedJobStatusEnum.rejected:
                    app_status == 'Rejected'
                else:
                    app_status = 'Pending'
                applicant_dict['status'] = app_status
                member_id = application.applied_by
                member_instance = User.query.get(member_id)
                member_name = member_instance.name
                profile_instance_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                if profile_instance_exists:
                    profile_instance = Profile.query.filter_by(user_id=member_id).first()
                    profile_pic = members_url+profile_instance.profile_pic
                    city = profile_instance.city
                else:
                    city=''
                    profile_pic = ''
                applicant_dict['city'] = city
                applicant_dict['member_id'] = member_id
                applicant_dict['profile_pic'] = profile_pic
                applicant_dict['member_name'] = member_name
                applicant_dict['pay_expected'] = '£'+application.pay_expected+'/hr'
                #Rating
                stars_list = []
                reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).first())
                if reviews_exist:
                    reviews = Reviews.query.filter_by(member_id=member_id)
                    for review in reviews:
                            stars = review.employer_stars
                            stars_list.append(int(stars))
                            total = sum(stars_list)
                            count = len(stars_list)
                            avg = total/count
                else:
                    avg = 0
                applicant_dict['rating'] = avg
                applicants_list.append(applicant_dict.copy())
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/jobs-list.html',profile_pic=profile_pic,job_details=job_details_dict,
            applicants=applicants_list,notifications=notifications_list,
            unread_count=unread_count,total_count=total_count)


#Fund Details For a Job Application
@web_routes_bp.route('/fundJobDetails/', methods = ['GET','POST'])
def fundJobDetails():
    try:
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    fund_details_list = []
    fund_details_dict = {}
    application_id = request.form['application_id']
    user_instance = User.query.get(current_user.id)
    try:
        application_instance = AppliedJobs.query.get(application_id)
        if application_instance is None:
            return make_response(jsonify({"error":"No application exists"}),400)
    except Exception as e:
        return make_response(jsonify({"error":"No application exists"}),400)
    job_id = application_instance.job_id
    job_detail = Jobs.query.get(job_id)
    business_name = job_detail.business_name
    application = AppliedJobs.query.get(application_id)
    if application:
        job_budget = application.pay_expected
        print('job_budget',job_budget)
        if('-' in job_budget):
            budget_amount_list = job_budget.split('-')
            amount_str = str(budget_amount_list[1])
            per_hour_amount = amount_str.replace('$','')
        elif '$' in job_budget:
            per_hour_amount = job_budget.replace('$','')
        elif '£' in job_budget:
            per_hour_amount = job_budget.replace('£','')
        else:
            per_hour_amount = job_budget
        #Time Calculation
        shift_start_time = job_detail.shift_start_time
        shift_end_time = job_detail.shift_end_time
        print('job_time',shift_start_time,shift_end_time)
        start_time = convert24(shift_start_time)
        end_time = convert24(shift_end_time)
        print('time>>>>>>',start_time,end_time)
        if 'AM' or 'PM' in start_time:
            start_time_final = start_time.replace(' AM','')
            start_time_final = start_time.replace(' PM','')
        if 'AM' or 'PM' in end_time:
            end_time_final = end_time.replace(' AM','')
            end_time_final = end_time.replace(' PM','')
        FMT = '%H:%M'
        print('start_time_final',start_time_final,'end_time_final',end_time_final)
        tdelta = datetime.datetime.strptime(end_time_final.strip(' \t\r\n'), FMT) - datetime.datetime.strptime(start_time_final.strip(' \t\r\n'), FMT)
        shift_hours = tdelta.seconds/3600
        print('shift_hours',int(shift_hours))
        #shifts calculation
        shift_start_date = job_detail.shift_start_date
        shift_end_date = job_detail.shift_end_date
        delta = shift_end_date - shift_start_date
        shifts_count = delta.days
        print('shifts_count',shifts_count)
        total_pay = int(shifts_count)*int(shift_hours)*int(per_hour_amount) 
        print('total_pay',total_pay)
        fee_details = EnquirerFees.query.get(1)
        print('fee_details>>>>>>>>>',fee_details)
        admin_charges = int(shifts_count)*int(shift_hours)*float(fee_details.admin_charges_per_hour_pounds)
        print('admin_charges',admin_charges)
        bidding_fees = int(shifts_count)*int(shift_hours)*float(1/int(fee_details.bidding_fees_per_hour_pence))
        print('bidding_fees',bidding_fees)
        amount_excluding_vat = total_pay+admin_charges+bidding_fees+float(fee_details.aos_standard_addition_per_hour)+float(fee_details.aos_one_off_misc_payment)
        print('amount_excluding_vat',amount_excluding_vat)
        vat = float(fee_details.vat)
        vat_amount = (vat/100)*amount_excluding_vat
        print('vat_amount',vat_amount)
        net_payable = amount_excluding_vat+vat_amount
        print('net_payable',net_payable)
        fund_details_dict['application_id'] = application_id
        fund_details_dict['business_name'] = business_name
        fund_details_dict['Pay_Per_Hour'] = "£"+str(per_hour_amount)
        fund_details_dict['AOS_Standard_Addition_Per_Hour'] = float(fee_details.aos_standard_addition_per_hour)
        fund_details_dict['AOS_One_Off_Misc_Payment'] = float(fee_details.aos_one_off_misc_payment)
        fund_details_dict['Total_Expected_Hours_Worked'] = int(shifts_count)*int(shift_hours)
        fund_details_dict['Total_Pay'] = "£"+str(total_pay)
        fund_details_dict['Admin_Charges'] = "£"+str(admin_charges)
        fund_details_dict['Bidding_Fees'] = "£"+str(bidding_fees)
        fund_details_dict['Sub_Total'] = "£"+str(amount_excluding_vat)
        fund_details_dict['Vat'] = "£"+str(vat_amount)
        fund_details_dict['Net_Payable'] = "£"+str(net_payable)
        html = render_template('Employer/fund-details.html',fund_details=fund_details_dict)
        return jsonify({'html':html})


#Fund For Job Application by Card
@web_routes_bp.route("/fundJob/<application_id>/", methods=['GET','POST'])
def fundJob(application_id):
    try:
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    if request.method == 'GET':
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        return render_template('Employer/fund-job.html',application_id=application_id,profile_pic=profile_pic)
    else:
        try:
            ###############Card Token######################
            post_data = request.form
            application_id = application_id
            application = AppliedJobs.query.get(application_id)
            job_id = application.job_id
            job_detail = Jobs.query.get(job_id)
            job_budget = application.pay_expected
            print('job_budget',job_budget)
            if('-' in job_budget):
                budget_amount_list = job_budget.split('-')
                amount_str = str(budget_amount_list[1])
                per_hour_amount = amount_str.replace('$','')
            elif '$' in job_budget:
                per_hour_amount = job_budget.replace('$','')
            elif '£' in job_budget:
                per_hour_amount = job_budget.replace('£','')
            else:
                per_hour_amount = job_budget
            #Time Calculation
            shift_start_time = job_detail.shift_start_time
            shift_end_time = job_detail.shift_end_time
            print('job_time',shift_start_time,shift_end_time)
            start_time = convert24(shift_start_time)
            end_time = convert24(shift_end_time)
            print('time>>>>>>',start_time,end_time)
            if 'AM' or 'PM' in start_time:
                start_time_final = start_time.replace(' AM','')
                start_time_final = start_time.replace(' PM','')
            if 'AM' or 'PM' in end_time:
                end_time_final = end_time.replace(' AM','')
                end_time_final = end_time.replace(' PM','')
            FMT = '%H:%M'
            print('start_time_final',start_time_final,'end_time_final',end_time_final)
            tdelta = datetime.datetime.strptime(end_time_final.strip(' \t\r\n'), FMT) - datetime.datetime.strptime(start_time_final.strip(' \t\r\n'), FMT)
            shift_hours = tdelta.seconds/3600
            print('shift_hours',int(shift_hours))
            #shifts calculation
            shift_start_date = job_detail.shift_start_date
            shift_end_date = job_detail.shift_end_date
            delta = shift_end_date - shift_start_date
            shifts_count = delta.days
            print('shifts_count',shifts_count)
            total_pay = int(shifts_count)*int(shift_hours)*int(per_hour_amount) 
            print('total_pay',total_pay)
            fee_details = EnquirerFees.query.get(1)
            print('fee_details>>>>>>>>>',fee_details)
            admin_charges = int(shifts_count)*int(shift_hours)*float(fee_details.admin_charges_per_hour_pounds)
            print('admin_charges',admin_charges)
            bidding_fees = int(shifts_count)*int(shift_hours)*float(1/int(fee_details.bidding_fees_per_hour_pence))
            print('bidding_fees',bidding_fees)
            amount_excluding_vat = total_pay+admin_charges+bidding_fees+float(fee_details.aos_standard_addition_per_hour)+float(fee_details.aos_one_off_misc_payment)
            print('amount_excluding_vat',amount_excluding_vat)
            vat = float(fee_details.vat)
            vat_amount = (vat/100)*amount_excluding_vat
            print('vat_amount',vat_amount)
            net_payable = amount_excluding_vat+vat_amount
            print('net_payable',net_payable)
            card_number = post_data['card_number']
            exp_month = post_data['exp_month']
            exp_year = post_data['exp_year']
            cvv = post_data['cvv']
            if((card_number == '') or (exp_year=='') or (exp_month=='') or (cvv=='') or (application_id=='')):
                flash('Please provide card details')
                url = 'fundJob/'+application_id+'/'
                return redirect(url)
            application_instance = AppliedJobs.query.get(application_id)
            member_id = application_instance.applied_by
            member_data = User.query.get(member_id)
            member_device_id = member_data.device_id
            member_email = member_data.email
            job_id = application_instance.job_id
            job_profile_data = Jobs.query.get(job_id)
            enquirer_id = job_profile_data.posted_by
            enquirer_data = User.query.get(enquirer_id)
            employer_email = enquirer_data.email
            job_title = job_profile_data.business_name
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
            payable_amount = float(net_payable)*100
            charge = stripe.Charge.create(
              amount=int(payable_amount),
              currency=currency,
              description='job funding by card',
              source=token,
            )
            funding_instance = UserPayments(
                reference = 'Wallet Funding For Job',
                medium = 'card',
                amount = total_pay,
                user_id = current_user.id,
                job_id = job_id
            )
            try:
                local_object = db.session.merge(funding_instance)
                db.session.add(local_object)
            except Exception as e:
                print('error in commit',e)
                db.session.add(funding_instance)
            wallet_exists = bool(Wallet.query.filter_by(user_id=current_user.id).first())
            if wallet_exists:
                wallet_instance = Wallet.query.filter_by(user_id=current_user.id).first()
                balance = wallet_instance.balance
                total_balance = int(balance)+int(total_pay)
                wallet_instance.balance = total_balance
            else:
                wallet_instance = Wallet(
                        balance = total_pay,
                        user_id = current_user.id
                )
            try:
                local_object = db.session.merge(wallet_instance)
                db.session.add(local_object)
            except Exception as e:
                print('error in commit',e)
                db.session.add(wallet_instance)
            db.session.commit()
            ##############################################Save to openarc db####################################
            admin_payment = float(admin_charges)+float(bidding_fees)+float(vat)+float(fee_details.aos_one_off_misc_payment)+float(fee_details.aos_standard_addition_per_hour)
            print('admin_payment',admin_payment)
            application_instance.is_funded = True
            application_instance.funded_amount = total_pay
            application_instance.brokerage = admin_payment
            application_instance.application_status="approved"
            application_instance.is_active=True
            application_instance.funded_on=datetime.datetime.now()
            try:
                local_object = db.session.merge(application_instance)
                db.session.add(local_object)
            except Exception as e:
                print('error in commit',e)
                db.session.add(application_instance)
            db.session.commit()
            account_id = connected_account_id
            transfer_amount = float(admin_payment)*100
            print('transfer_amount',transfer_amount)
            if account_id:
                transfer = stripe.Transfer.create(
                  amount=int(transfer_amount),
                  currency='gbp',
                  destination= account_id,
                  transfer_group="Job Fund Payment brokerage"
                )
            try:
                #send email
                message_title = "Job Application Approval-OpenArc"
                message_body = 'An application has been approved for job at'+job_title
                # send_notification(member_device_id, message_title, message_body)
                subject = "Job Application Approval-OpenArc"
                to = [member_email,employer_email]
                for address in to:
                    if address == member_email:
                        agree_link = ''
                    else:
                        agree_link = ''
                    body = 'Hello '+address+',\nYour application has been approved for job at\n'
                    try:
                        send_email(address, subject, job_title, agree_link, 'approved')
                    except Exception as e:
                        print('error sending email',e)
            except Exception as e:
                print('error in sending email',e)
            flash('Funded Successfully')
            url = 'jobsList/'+job_id+'/'
            return redirect(url)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            lNumber = exc_tb.tb_lineno
            print('line',lNumber,'error',e)
            flash('Error Occured')
            url = '/fundJob/'+application_id+'/'
            return redirect(url)

#Posted Job Preview
@web_routes_bp.route('/jobPreview/<job_id>/', methods=['POST','GET'])
def jobPreviewDetails(job_id):
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        job_details_dict = {}
        job_details = Jobs.query.get(job_id)
        job_details_dict['id'] = job_details.id
        job_details_dict['business_name'] = job_details.business_name
        job_details_dict['job_description'] = job_details.job_description
        job_details_dict['shift_start_date'] = job_details.shift_start_date
        job_details_dict['shift_end_date'] = job_details.shift_end_date
        job_details_dict['shift_start_time'] = job_details.shift_start_time
        job_details_dict['shift_end_time'] = job_details.shift_end_time
        job_details_dict['budget'] = job_details.budget
        job_details_dict['city'] = job_details.city
        job_details_dict['job_type'] = job_details.job_type
        job_details_dict['vacancies'] = job_details.vacancies
        job_details_dict['address'] = job_details.address
        job_details_dict['shift_type'] = job_details.shift_type
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/job-preview.html',profile_pic=profile_pic,job_details=job_details_dict,
            notifications=notifications_list,
            unread_count=unread_count,total_count=total_count)





#Ongoing Job Details
@web_routes_bp.route('/jobsHistory/<job_id>', methods=['POST','GET'])
def jobsHistory(job_id):
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        user_instance = User.query.get(current_user.id)
        job_dict = {}
        job_details = Jobs.query.get(job_id)
        job_dict['id'] = job_details.id
        job_dict['business_name'] = job_details.business_name
        job_dict['job_type'] = job_details.job_type
        job_dict['shift_start_date'] = job_details.shift_start_date
        job_dict['shift_end_date'] = job_details.shift_end_date
        job_dict['job_description'] = job_details.job_description
        hired_members_list = []
        hired_member_dict={}
        total_hours = []
        total_amount = []
        hired_members_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).first())
        if hired_members_exists:
            job_applications =  AppliedJobs.query.filter_by(job_id=job_id)
            for application in job_applications:
                application_id = application.id
                payment_instance_exists = bool(JobPayments.query.filter_by(application_id = application_id).first())
                if payment_instance_exists:
                    payment_instance = JobPayments.query.filter_by(application_id = application_id).first()
                    hours = payment_instance.total_hours
                    total_hours.append(float(hours))
                    amount = payment_instance.total_amount
                    total_amount.append(float(amount))
                else:
                    hours = 0
                today_date = date.today()
                member_id = application.applied_by
                member_instance = User.query.get(member_id)
                member_name = member_instance.name
                profile_instance_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                if profile_instance_exists:
                    profile_instance = Profile.query.filter_by(user_id=member_id).first()
                    profile_pic = members_url+profile_instance.profile_pic
                    city = profile_instance.city
                else:
                    profile_pic = ''
                    city = ''
                hired_member_dict['member_id'] = member_id
                hired_member_dict['hours'] = hours
                hired_member_dict['hourly_rate'] = '£'+str(application.pay_expected)+'/hr'
                hired_member_dict['application_id'] = application_id
                hired_member_dict['profile_pic'] = profile_pic
                hired_member_dict['member_name'] = member_name
                hired_member_dict['today_date'] = today_date
                hired_members_list.append(hired_member_dict.copy())
        total_hours_worked = round(sum(total_hours),1)
        total_amount_spnt = round(sum(total_amount),2)
        total_amount_spent = '£'+str(total_amount_spnt)
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/jobs-history.html',profile_pic=profile_pic,job_dict=job_dict,
            hired_members=hired_members_list,total_hours_worked=total_hours_worked,
            total_amount_spent=total_amount_spent,
            notifications=notifications_list,total_count=total_count,
            unread_count=unread_count)


#Get Memebr Details
@web_routes_bp.route('/getMemberWorkHistory/', methods=['POST'])
def getMemberWorkHistory():
    if request.method == 'POST':
        member_dict = {}
        application_id = request.form['application_id']
        application_details = AppliedJobs.query.get(application_id)
        member_id = application_details.applied_by
        member_details = User.query.get(member_id)
        member_dict['name'] = member_details.name
        member_dict['member_id'] = member_details.id
        member_profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
        if member_profile_exists:
            member_profile = Profile.query.filter_by(user_id=member_id).first()
            member_profile_pic = members_url+member_profile.profile_pic
            hourly_rate = member_profile.hourly_rate
        else:
            member_profile_pic = ''
            hourly_rate = '£10'
        pay_instance_exists = bool(JobPayments.query.filter_by(application_id = application_id).first())
        if pay_instance_exists:
            payment_instance = JobPayments.query.filter_by(application_id = application_id).first()
            hours = payment_instance.total_hours
            amount = payment_instance.total_amount
        else:
            hours = 0
            amount = 0
        member_dict['profile_pic'] = member_profile_pic
        member_dict['hours'] = hours
        member_dict['amount'] = amount
        member_dict['hourly_rate'] = hourly_rate
        logs_list =[]
        log_dict ={}
        job_logs = StartedJobLogs.query.filter_by(application_id=application_id)
        for log in job_logs:
            date = log.date
            mydate = datetime.datetime.strptime(str(date), '%Y-%m-%d')
            work_date = mydate.strftime('%B %d, %Y')
            log_dict['date'] = work_date
            log_dict['start_time'] = log.start_time
            log_dict['end_time'] = log.end_time
            log_dict['hours'] = log.hours
            log_dict['after_hours'] = log.after_hours
            logs_list.append(log_dict.copy())
        html = render_template('Employer/work_history.html',member_dict=member_dict,logs=logs_list)
        return jsonify({'html':html})

#JOB Invites Page
@web_routes_bp.route('/jobInvites/', methods=['POST','GET'])
def jobInvites():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        jobs_list = []
        job_dict = {} 
        drafts_list = []
        drafts_dict = {}
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        jobs_exists = bool(Jobs.query.filter_by(posted_by=current_user.id).first())
        if jobs_exists:
            jobs = Jobs.query.filter_by(posted_by=current_user.id)
            for job in jobs:
                if job.is_draft == False:
                    job_dict['job_id'] = job.id
                    job_dict['city'] = job.city
                    job_dict['business_name'] = job.business_name
                    job_dict['job_description'] = job.job_description
                    start_date = job.shift_start_date
                    today_date = date.today()
                    delta = start_date - today_date
                    days_remaining = delta.days
                    if days_remaining < 0:
                        days_left = 0
                    else:
                        days_left = int(days_remaining)
                    job_dict['days_left'] = days_left
                    jobs_list.append(job_dict.copy())
                else:
                    drafts_dict['job_id'] = job.id
                    drafts_dict['city'] = job.city
                    drafts_dict['business_name'] = job.business_name
                    drafts_dict['job_description'] = job.job_description
                    start_date = job.shift_start_date
                    today_date = date.today()
                    delta = start_date - today_date
                    days_remaining = delta.days
                    if days_remaining < 0:
                        days_left = 0
                    else:
                        days_left = int(days_remaining)
                    drafts_dict['days_left'] = days_left
                    drafts_list.append(drafts_dict.copy())
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/job-invites.html',profile_pic=profile_pic,jobs=jobs_list,
            notifications=notifications_list,unread_count=unread_count,
            total_count=total_count)


#Invite Guards Page
@web_routes_bp.route('/inviteGuards/<job_id>', methods=['POST','GET'])
def inviteGuards(job_id):
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        guards_list = []
        guards_dict = {}
        members = User.query.filter_by(user_type='member')
        job_details = Jobs.query.get(job_id)
        business_name = job_details.business_name
        for member in members:
            member_name = member.name
            member_email = member.email
            member_id = member.id
            #Rating
            stars_list = []
            reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).first())
            if reviews_exist:
                reviews = Reviews.query.filter_by(member_id=member_id)
                for review in reviews:
                        stars = review.employer_stars
                        stars_list.append(int(stars))
                        total = sum(stars_list)
                        count = len(stars_list)
                        avg = total/count
            else:
                avg = 0
            invite_sent = bool(JobInvites.query.filter_by(job_id = job_id).filter_by(guard_id=member_id).first())
            profile_exists = bool(Profile.query.filter_by(user_id=member_id).first()) 
            if profile_exists:
                profile = Profile.query.filter_by(user_id=member_id).first()
                profile_pic = members_url+profile.profile_pic
                hourly_rate = profile.hourly_rate+'/hr'
            else:
                profile_pic = ''
                hourly_rate = ''
            try:
                jobs_completed = AppliedJobs.query.filter_by(applied_by=member_id).filter_by(is_completed=True).count()
            except Exception as e:
                jobs_completed = 0
            guards_dict['guard_id'] = member_id
            guards_dict['rating'] = avg
            guards_dict['invite_sent'] = invite_sent
            guards_dict['guard_name'] = member_name
            guards_dict['guard_email'] = member_email
            guards_dict['jobs_completed'] = jobs_completed
            guards_dict['hourly_rate'] = hourly_rate
            guards_dict['profile_pic'] = profile_pic
            guards_list.append(guards_dict.copy())
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/invite_guards.html',guards_list=guards_list,job_id=job_id,
            business_name=business_name,profile_pic=profile_pic,
            notifications=notifications_list,unread_count=unread_count,
            total_count=total_count)


#Invite Guard For a Job
@web_routes_bp.route('/inviteGuard/<job_id>/<guard_id>', methods=['GET','POST'])
def inviteGuard(job_id,guard_id):
    if request.method == 'GET':
        guard_id = guard_id
        job_id=job_id
        invite_instance = JobInvites(
                    job_id=job_id,
                    guard_id=guard_id,
                )
        db.session.add(invite_instance)
        db.session.commit()  # Create new invite
        job_profile_data = Jobs.query.get(job_id)
        # member_id = job_profile_data.posted_by
        member_data = User.query.get(guard_id)
        member_device_id = member_data.device_id
        member_email = member_data.email
        job_title = job_profile_data.business_name
        message_title = "Job Invitation"
        message_body = 'Invitation to apply for a job at'+job_title
        # send_notification(member_device_id, message_title, message_body)
        subject = "Job Invitation-OpenArc"
        to = member_email
        body = 'Hello '+to+',\nYou are invited to apply on  job at:\n'+job_title
        try:
            send_email(to, subject, '', '', job_title, '', 'invited')
        except Exception as e:
            print('error sending email',e)
        flash('invite sent')
        url = '/inviteGuards/'+str(job_id)
        return redirect (url)
        


#Profile Page
@web_routes_bp.route('/profileEnquirer/', methods=['POST','GET'])
def profilePage():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        user_details = User.query.get(current_user.id)
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
            profile = ''
        jobs_exist = bool(Jobs.query.filter_by(posted_by=current_user.id).first())
        if jobs_exist:
            jobs_count = Jobs.query.filter_by(posted_by=current_user.id).count()
            user_jobs = Jobs.query.filter_by(posted_by=current_user.id)
            application_id_list = []
            for job in user_jobs:
                application_exists = bool(AppliedJobs.query.filter_by(job_id=job.id).first())
                if application_exists:
                    application_details = AppliedJobs.query.filter_by(job_id=job.id).first()
                    application_id = application_details.id
                    application_id_list.append(application_id)
            print('application_id_list',application_id_list)
            complete_count = 0
            for app_id in application_id_list:
                rec_exists = bool(JobPayments.query.filter_by(application_id=app_id).first())
                if rec_exists:
                    record_data = JobPayments.query.filter_by(application_id=app_id).first()
                    if (record_data.work_status == 'completed'):
                        complete_count+=1
        else:
            jobs_count = 0
            complete_count = 0
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/profile.html',complete_count=complete_count,
            user_details=user_details,jobs=jobs_count,profile_pic=profile_pic,email=current_user.email,
            profile=profile,unread_count=unread_count,total_count=total_count,
            notifications=notifications_list)
    else:
        print('form---',request.form)
        company_name = request.form['company']
        about = request.form['about']
        postal_code = request.form['postal_code']
        # email = request.form['email']
        contact = request.form['contact']
        # company_contact = request.form['company_contact']
        city = request.form['city']
        address = request.form['address']
        registration_number = request.form['registration_number']
        acs_reference_number = request.form['acs_reference_number']
        # profile_pic = request.files.get('profile_pic')
        # print('-------',profile_pic,'name',profile_pic.filename)
        if (company_name and contact and city and address and postal_code and acs_reference_number):
            user_instance = User.query.get(current_user.id)
            # user_instance.email = email
            user_instance.name = company_name
            try:
                local_object = db.session.merge(user_instance)
                db.session.add(local_object)
            except Exception as e:
                print('error in commit',e)
                db.session.add(user_instance)
            db.session.commit()
            enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
            if enquirer_profile_exists:
                profile_instance = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
                profile_instance.acs_reference_number = acs_reference_number
                profile_instance.company_contact = contact
                # profile_instance.company_contact = company_contact
                profile_instance.city = city
                profile_instance.address = address
                profile_instance.postal_code = postal_code
                profile_instance.registration_number = registration_number
                profile_instance.about = about
                # if(( profile_pic is not None ) and (profile_pic.filename != '')):
                #     filename = secure_filename(profile_pic.filename)
                #     profile_pic.save(os.path.join(server_url_local_local, filename))
                #     profile_instance.company_logo = filename
                try:
                    local_object = db.session.merge(profile_instance)
                    db.session.add(local_object)
                except Exception as e:
                    print('error in commit',e)
                    db.session.add(profile_instance)
            db.session.commit()
            flash('Update successfull')
        else:
            flash('Please fill all the fields')
        return redirect('/profileEnquirer/')


#JOB Listing Page Profile
@web_routes_bp.route('/profileJobListing/', methods=['POST','GET'])
def profileJobListing():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        jobs_list = []
        job_dict = {} 
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.profile_pic
        jobs_exists = bool(Jobs.query.filter_by(posted_by=current_user.id).first())
        if jobs_exists:
            jobs = Jobs.query.filter_by(posted_by=current_user.id)
            for job in jobs:
                job_dict['job_id'] = job.id
                job_dict['city'] = job.city
                job_dict['job_title'] = job.job_title
                job_dict['job_description'] = job.job_description
                start_date = job.start_date
                today_date = date.today()
                delta = start_date - today_date
                days_remaining = delta.days
                if days_remaining < 0:
                    days_left = 'NO'
                else:
                    days_left = days_remaining
                job_dict['days_left'] = days_left
                jobs_list.append(job_dict.copy())
        return render_template('Employer/profile_job_listing.html',profile_pic=profile_pic,jobs=jobs_list)


#Logout
@web_routes_bp.route("/logoutEnquirer/")
def logout():
    logout_user()
    return redirect('/loginEnquirer')

######################################################################################################

#################################Add JOB#############################################################
#Add New JOB
#Job Type
@web_routes_bp.route('/jobType/', methods=['POST','GET'])
def jobType():
    try:
        print('>>>>>>>>>>>>',os.path)
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
    if enquirer_profile_exists:
        profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
        profile_pic = server_url+profile.company_logo
    else:
        profile_pic = ''
    notifications_list = []
    notification_dict ={}
    notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
    if notifications_exists:
        unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
        total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
        notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
        for n in notifications:
            notification_dict['body'] = n.body
            notification_dict['status'] = n.status
            notification_dict['time'] = n.created_at
            notifications_list.append(notification_dict.copy())
    else:
        unread_count = 0
        total_count = 0
    try:
        subscription_exists = bool(Subscriptions.query.filter_by(user=current_user.id).first())
        if subscription_exists:
            subscription_details = Subscriptions.query.filter_by(user=current_user.id).first()
            billing_cycle = subscription_details.billing_cycle
            payment_date = subscription_details.payment_date
            plan_id = subscription_details.plan_id
            plan_instance = SubscriptionPlans.query.get(plan_id)
            current_plan = plan_instance.plan_name
            if billing_cycle == 'monthly':
                expiry_date = payment_date + relativedelta(months=+1)
            else:
                expiry_date = payment_date + relativedelta(months=+12)
        else:
            current_plan = 'Free'
            employer_instance = User.query.get(current_user.id)
            start_date = employer_instance.created_at
            three_months = start_date + relativedelta(months=+3)
            expiry_date = three_months
        print('expiry_date',expiry_date.date())
        exp_date = expiry_date.date()
        if exp_date < date.today():
            status = 'Expired'
        else:
            status = 'Active'
    except Exception as e:
        print('error in getting subscription',e)
    return render_template('Employer/job_type.html',profile_pic=profile_pic,unread_count=unread_count,
        total_count = total_count, notifications=notifications_list,
        status=status,exp_date=exp_date)


#Add JOB Details
@web_routes_bp.route('/jobDetails/', methods=['POST','GET'])
def jobDetails():
    if request.method == 'POST':
        # print('form-------',request.form)
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        job_type = request.form.get('job_type')
        session['job_category'] = job_type
        enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
        if enquirer_profile_exists:
            profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
            profile_pic = server_url+profile.company_logo
        else:
            profile_pic = ''
        html = render_template('Employer/job_details.html')
        return jsonify({'html':html})

#Add JOB 
@web_routes_bp.route('/addJob/', methods=['POST','GET'])
def addJob():
    try:
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    try:
        if request.method == 'POST':
            print('>>>>>>>>>>',request.form,'file>>',request.files)
            if request.files:
                try:
                    contract_file = request.files['contract_file']
                    filename = secure_filename(contract_file.filename)
                    contract_file.save(os.path.join(server_contracts_uploads, filename))
                    contract = filename
                except Exception as e:
                    contract = ''
                    print('error in upload',e)
            else:
                contract_terms = request.form.get('contract_terms')
                contract = contract_terms
            action = request.form['action']
            business_name = request.form.get('business_name')
            job_category = session['job_category']
            job_description = request.form.get('job_description')
            no_of_vacancies = request.form.get('no_of_vacancies')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            address = request.form.get('address')
            city = request.form.get('city')
            try:
                city_name=city.replace(' ','')
            except Exception as e:
                city_name = city
            shift_type = request.form.get('shift_type')
            job_type = request.form.get('job_type')
            budget = request.form.get('budget')
            emergency_rate = request.form.get('emergency_rate')
            #Add to Session
            session['business_name'] = request.form.get('business_name')
            session['job_description'] = request.form.get('job_description')
            session['no_of_vacancies'] = request.form.get('no_of_vacancies')
            session['start_date'] = request.form.get('start_date')
            session['end_date'] = request.form.get('end_date')
            session['start_time'] = request.form.get('start_time')
            session['end_time'] = request.form.get('end_time')
            session['address'] = request.form.get('address')
            session['city'] = city_name
            session['shift_type'] = request.form.get('shift_type')
            session['job_type'] = request.form.get('job_type')
            session['budget'] = request.form.get('budget')
            session['emergency_rate'] = request.form.get('emergency_rate')
            session['contract'] = contract
            if action == 'draft':
                if start_date:
                    start_date = start_date
                else:
                    start_date = '1111-11-11'
                if end_date:
                    end_date = end_date
                else:
                    end_date = '1111-11-11'
                job_instance = Jobs(
                    business_name = business_name,
                    job_category = job_category,
                    job_description = job_description,
                    address = address,
                    city = city_name,
                    vacancies = no_of_vacancies,
                    shift_start_date = start_date,
                    shift_end_date = end_date,
                    shift_start_time = start_time,
                    shift_end_time = end_time,
                    shift_type = shift_type,
                    emergency_rate=emergency_rate,
                    job_type = job_type,
                    budget = budget,
                    posted_by = current_user.id,
                    is_draft = True,
                    contract=contract
                )
                try:
                    local_object = db.session.merge(job_instance)
                    db.session.add(local_object)
                except Exception as e:
                    print('error in commit',e)
                    db.session.add(job_instance)
                db.session.commit()  # Create new job
                return redirect('/saved/')
            else:
                job_details = {}
                job_details['business_name'] = request.form.get('business_name')
                job_details['job_category'] = session['job_category']
                job_details['job_description'] = request.form.get('job_description')
                job_details['no_of_vacancies'] = request.form.get('no_of_vacancies')
                job_details['start_date'] = request.form.get('start_date')
                job_details['end_date'] = request.form.get('end_date')
                job_details['start_time'] = request.form.get('start_time')
                job_details['end_time'] = request.form.get('end_time')
                job_details['address'] = request.form.get('address')
                job_details['city'] = request.form.get('city')
                job_details['shift_type'] = request.form.get('shift_type')
                job_details['job_type'] = request.form.get('job_type')
                job_details['budget'] = request.form.get('budget')
                job_details['emergency_rate'] = request.form.get('emergency_rate')
                enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
                if enquirer_profile_exists:
                    profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
                    profile_pic = server_url+str(profile.company_logo)
                else:
                    profile_pic = ''
            notifications_list = []
            notification_dict ={}
            notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
            if notifications_exists:
                unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
                total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
                notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
                for n in notifications:
                    notification_dict['body'] = n.body
                    notification_dict['status'] = n.status
                    notification_dict['time'] = n.created_at
                    notifications_list.append(notification_dict.copy())
            else:
                unread_count = 0
                total_count = 0
            return render_template('Employer/save_job_preview.html',profile_pic=profile_pic,
                job_details=job_details,notifications=notifications_list,
                unread_count=unread_count,total_count=total_count) 
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in add Job at line number',lNumber,'error is:',e)
        flash('Error posting Job')
        return redirect('/jobType/')

#Edit Job  
@web_routes_bp.route('/editJob/', methods=['POST','GET'])
def editJob():
    try:
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    job_details = {}
    job_details['job_category'] = session['job_category']
    job_details['business_name'] = session['business_name']
    job_details['job_description'] = session['job_description']
    job_details['no_of_vacancies'] = session['no_of_vacancies']
    job_details['start_date'] = session['start_date']
    job_details['end_date'] = session['end_date']
    job_details['start_time'] = session['start_time']
    job_details['end_time'] = session['end_time']
    job_details['address'] = session['address']
    job_details['city'] = session['city']
    job_details['job_type'] = session['job_type']
    job_details['budget'] = session['budget']
    job_details['shift_type'] = session['shift_type']
    job_details['emergency_rate'] = session['emergency_rate']
    job_details['contract'] = session['contract']
    enquirer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()) 
    if enquirer_profile_exists:
        profile = EnquirerProfile.query.filter_by(enquirer_id=current_user.id).first()
        profile_pic = server_url+str(profile.company_logo)
    else:
        profile_pic = ''
    return render_template('Employer/edit-job.html',profile_pic=profile_pic,job_details=job_details)


#Post Job  
@web_routes_bp.route('/postJob/', methods=['POST','GET'])
def postJob():
    try:
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        print(session)
        user_instance = User.query.get(current_user.id)
        subscription_exists = bool(Subscriptions.query.filter_by(user=current_user.id).first())
        if subscription_exists:
            print('existing')
            subscription_instance = Subscriptions.query.filter_by(user=current_user.id).first()
            start_date = subscription_instance.payment_date
            billing_cycle = subscription_instance.billing_cycle
            if billing_cycle == 'yearly':
                end_date =  start_date + datetime.timedelta(days=int(365))
            if billing_cycle == 'monthly':
                end_date =  start_date + datetime.timedelta(days=int(30))
            print('end_date',end_date)
            today = datetime.datetime.now()
            if end_date > today:
                print('can post job')
                pass
            else:
                flash('Your subscription plan has expired')
                return redirect('/jobListing/')
        else:
            plan_instance = SubscriptionPlans.query.filter_by(plan_name='Free').first()
            free_days = plan_instance.free_days
            start_date = user_instance.created_at
            end_date =  start_date + datetime.timedelta(days=int(free_days))
            print('end_date',end_date)
            today = datetime.datetime.now()
            if end_date > today:
                print('you can post a job ')
                pass
            else:
                flash('Your subscription plan has expired')
                return redirect('/jobType/')
        job_category = session['job_category']
        business_name = session['business_name']
        job_description = session['job_description']
        no_of_vacancies = session['no_of_vacancies']
        start_date = session['start_date']
        end_date = session['end_date']
        start_time = session['start_time']
        end_time = session['end_time']
        address = session['address']
        city = session['city']
        job_type = session['job_type']
        budget = session['budget']
        shift_type = session['shift_type']
        emergency_rate = session['emergency_rate']
        contract = session['contract']
        job_instance = Jobs(
            business_name = business_name,
            job_category = job_category,
            job_description = job_description,
            address = address,
            city = city,
            vacancies = no_of_vacancies,
            shift_start_date = start_date,
            shift_end_date = end_date,
            shift_start_time = start_time,
            shift_end_time = end_time,
            shift_type = shift_type,
            emergency_rate=emergency_rate,
            job_type = job_type,
            budget = budget,
            contract = contract,
            posted_by = current_user.id,
            is_draft = False
        )
        try:
            local_object = db.session.merge(job_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(job_instance)
        db.session.commit()  # Create new job
        return redirect('/jobs/')
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in post Job at line number',lNumber,'error is:',e)
        flash('Error posting Job')
        return redirect('/addJob/')





#Add Draft Details  
@web_routes_bp.route('/addDraftDetails/', methods=['POST','GET'])
def addDraftDetails():
    if request.method == 'POST':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        # print(session)
        job_category = session['job_category']
        business_name = session['business_name']
        job_description = session['job_description']
        no_of_vacancies = session['no_of_vacancies']
        start_date = session['start_date']
        end_date = session['end_date']
        start_time = session['start_time']
        end_time = session['end_time']
        address = session['address']
        city = session['city']
        
        job_type = request.form.get('job_type')
        if job_type:
            job_type = job_type
        else:
            job_type = session['job_type']
        
        budget = request.form.get('budget')
        if budget:
            budget = budget
        else:
            budget = session['budget']

        shift_type = request.form.get('shift_type')
        if shift_type:
            shift_type = shift_type
        else:
            shift_type = session['shift_type']

        emergency_rate = request.form.get('emergency_rate')
        if emergency_rate:
            emergency_rate = emergency_rate
        else:
            emergency_rate = session['emergency_rate']

        job_instance = Jobs(
            business_name = business_name,
            job_category = job_category,
            job_description = job_description,
            address = address,
            city = city,
            vacancies = no_of_vacancies,
            shift_start_date = start_date,
            shift_end_date = end_date,
            shift_start_time = start_time,
            shift_end_time = end_time,
            shift_type = shift_type,
            emergency_rate=emergency_rate,
            job_type = job_type,
            budget = budget,
            posted_by = current_user.id,
            is_draft = True
        )
        try:
            local_object = db.session.merge(job_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(job_instance)
        db.session.commit()  # Create new job
        return jsonify({'message':"success"})

#View Draft Details
@web_routes_bp.route('/draftDetails/<job_id>', methods=['GET','POST'])
def draftDetails(job_id):
    try:
        print('current_user',current_user.id)
    except Exception as e:
        flash('Please Login Again')
        return redirect('/loginEnquirer/')
    job_id = job_id
    job_details = Jobs.query.get(job_id)
    business_name = job_details.business_name
    job_category = job_details.job_category
    job_description = job_details.job_description
    address = job_details.address
    city = job_details.city
    shift_type = job_details.shift_type
    vacancies = job_details.vacancies
    shift_start_date = job_details.shift_start_date
    shift_end_date = job_details.shift_end_date
    shift_start_time = job_details.shift_start_time
    shift_end_time = job_details.shift_end_time
    shift_type = job_details.shift_type,
    emergency_rate = job_details.emergency_rate
    job_type = job_details.job_type
    budget = job_details.budget
    return render_template('Employer/draft_preview.html',shift_type=shift_type,job_id=job_id,job_category=job_category,business_name=business_name,
            job_description=job_description,no_of_vacancies=vacancies,start_date=shift_start_date,
            end_date=shift_end_date,start_time=shift_start_time,end_time=shift_end_time,address=address,city=city,job_type=job_type,
            budget=budget,emergency_rate=emergency_rate)


#Draft To Job
@web_routes_bp.route('/draftToJob/', methods=['GET','POST'])
def draftToJob():
    print('request',request.form)
    job_id = request.form.get('job_id')
    job_instance = Jobs.query.get(job_id)
    job_instance.job_category = request.form.get('job_category')
    job_instance.business_name = request.form.get('business_name')
    job_instance.job_description = request.form.get('job_description')
    job_instance.no_of_vacancies = request.form.get('no_of_vacancies')
    job_instance.shift_start_date = request.form.get('shift_start_date')
    job_instance.shift_end_date = request.form.get('end_date')
    job_instance.shift_start_time = request.form.get('start_time')
    job_instance.shift_end_time = request.form.get('end_time')
    job_instance.address = request.form.get('address')
    job_instance.city = request.form.get('city')
    job_instance.job_type = request.form.get('job_type')
    job_instance.budget = request.form.get('budget')
    job_instance.shift_type = request.form.get('shift_type')
    job_instance.emergency_rate = request.form.get('emergency_rate')
    job_instance.is_draft = False
    try:
        local_object = db.session.merge(job_instance)
        db.session.add(local_object)
    except Exception as e:
        print('error in commit',e)
        db.session.add(job_instance)
    db.session.commit()  # Create new job
    return jsonify({'message':"success"})


# #Invite Guards For Job  
# @web_routes_bp.route('/inviteGuards/', methods=['POST','GET'])
# def inviteGuards():
#     if request.method == 'GET':
#         try:
#             print('current_user',current_user.id)
#         except Exception as e:
#             flash('Please Login Again')
#             return redirect('/loginEnquirer/')
#         guards_list = []
#         guards_dict = {}
#         members = User.query.filter_by(user_type='member')
#         for member in members:
#             member_name = member.name
#             member_email = member.email
#             member_id = member.id
#             profile_exists = bool(Profile.query.filter_by(user_id=member_id).first()) 
#             if profile_exists:
#                 profile = Profile.query.filter_by(user_id=member_id).first()
#                 profile_pic = members_url+profile.profile_pic
#             else:
#                 profile_pic = ''
#             try:
#                 jobs_completed = AppliedJobs.query.filter_by(applied_by=member_id).filter_by(is_completed=True).count()
#             except Exception as e:
#                 jobs_completed = 0
#             guards_dict['guard_id'] = member_id
#             guards_dict['guard_name'] = member_name
#             guards_dict['guard_email'] = member_email
#             guards_dict['jobs_completed'] = jobs_completed
#             guards_dict['profile_pic'] = profile_pic
#             guards_list.append(guards_dict.copy())
#         return render_template('Employer/invite_guards.html',guards_list=guards_list)


#Settings  
@web_routes_bp.route('/settings/', methods=['POST','GET'])
def settings():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        notifications_list = []
        notification_dict ={}
        notifications_exists = bool(EnquirerNotification.query.filter_by(employer_id=current_user.id).first())
        if notifications_exists:
            unread_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).filter_by(status='unread').count()
            total_count = EnquirerNotification.query.filter_by(employer_id=current_user.id).count()
            notifications = EnquirerNotification.query.filter_by(employer_id=current_user.id)
            for n in notifications:
                notification_dict['body'] = n.body
                notification_dict['status'] = n.status
                notification_dict['time'] = n.created_at
                notifications_list.append(notification_dict.copy())
        else:
            unread_count = 0
            total_count = 0
        return render_template('Employer/settings.html',unread_count=unread_count,
            total_count=total_count,notifications=notifications_list)


#Change Password  
@web_routes_bp.route('/changePassword/', methods=['POST','GET'])
def changePassword():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if len(new_password) < 8 :
            flash('Password length should be minimum 8 characters')
            return redirect('/settings/')
        if (new_password == '') or (confirm_password == ''):
            flash('Please pass both the values')
            return redirect('/settings/')
        if (new_password != confirm_password):
            flash('password and confirm_password are not matching')
            return redirect('/settings/')
        user = User.query.get(current_user.id)
        user.set_password(new_password)
        try:
            local_object = db.session.merge(user)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(user)
        db.session.commit()  # Create new user
        flash('Password Updated')
        return redirect('/settings/')


#Payments  
@web_routes_bp.route('/payments/', methods=['POST','GET'])
def payments():
    if request.method == 'GET':
        try:
            print('current_user',current_user.id)
        except Exception as e:
            flash('Please Login Again')
            return redirect('/loginEnquirer/')
        jobs = Jobs.query.filter_by(posted_by=current_user.id)
        payments_list = []
        payments_dict = {}
        user_payments_exists = bool(UserPayments.query.filter_by(user_id=current_user.id).first())
        if user_payments_exists:
            payments = UserPayments.query.filter_by(user_id=current_user.id)
            for payment in payments:
                payments_dict['medium'] = payment.medium
                payments_dict['reference'] = payment.reference
                payments_dict['job_id'] = payment.job_id
                payments_dict['amount'] = '£'+str(payment.amount)
                payments_dict['date'] = payment.created_at
                payments_list.append(payments_dict.copy())
        return render_template('Employer/payments.html',payments_list=payments_list)


@web_routes_bp.route('/table')
def table():
    jobs = Jobs.query.filter_by(posted_by=current_user.id)
    payments_list = []
    payments_dict = {}
    user_payments_exists = bool(UserPayments.query.filter_by(user_id=current_user.id).first())
    if user_payments_exists:
        payments = UserPayments.query.filter_by(user_id=current_user.id)
        for payment in payments:
            try:
                job_id = payment.job_id
                job_instance = Jobs.query.get(job_id)
                business_name = job_instance.business_name
                payments_dict['job'] = business_name
            except Exception as e:
                pass
            payments_dict['medium'] = payment.medium
            payments_dict['reference'] = payment.reference
            payments_dict['amount'] = '£'+str(payment.amount)
            payments_dict['date'] = payment.created_at
            payments_list.append(payments_dict.copy())
    print('payments_list',payments_list)
    return render_template('Employer/table.html',payments_list=payments_list)

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

