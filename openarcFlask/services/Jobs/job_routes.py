from flask import Blueprint, request, jsonify, make_response, Response, redirect
from .models import db, Reviews, Jobs, JobsSchema, AppliedJobs, AppliedJobsSchema, AppliedJobStatusEnum, Disputes, DisputesSchema
from .models import EnquirerFees, MemberFees
from services.Users.Enquirer.models import *
from services.Users.Member.models import *
from services.Subscriptions.models import *
from os import environ, path
from dotenv import load_dotenv
import sys, os
from . import login_manager
from flask_login import current_user, login_required, logout_user
from flask_jwt_extended import jwt_required , get_jwt_identity
import requests,json
# from flask_mail import Mail, Message
from . import mail
import datetime
from services.push_notifications import send_notification
from flask import render_template
from geopy.geocoders import Nominatim
from werkzeug.utils import secure_filename
from datetime import date, datetime, timedelta
from app.main.models import *
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import re
import base64
from datetime import datetime
import datetime
import stripe
from xhtml2pdf import pisa 
import jinja2
templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
EMPLOYER_TEMPLATE_FILE = "/templates/invoice.html"
MEMBER_TEMPLATE_FILE = "/templates/member_invoice.html"
employer_template = templateEnv.get_template(EMPLOYER_TEMPLATE_FILE)
member_template = templateEnv.get_template(MEMBER_TEMPLATE_FILE)

basedir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..'))
load_dotenv(path.join(basedir, '.env'))

connected_account_id = environ.get('STRIPE_CONNECTED_ACCOUNT')

stripe.api_key = environ.get('STRIPE_SECRET_KEY')



distance_matrix_api_key =environ.get('distance_matrix_api_key')
distance_matrix_url ='https://maps.googleapis.com/maps/api/distancematrix/json?'


from_email = environ.get('FROM_EMAIL')
sendgrid_api_key = environ.get('SENDGRID_API_KEY')

# Blueprint Configuration
jobs_main_bp = Blueprint(
    'jobs_main_bp', __name__,
)

# disputes_uploads = 'http://ec2-3-15-1-100.us-east-2.compute.amazonaws.com/uploads/disputes'
# contracts_uploads = 'http://ec2-3-15-1-100.us-east-2.compute.amazonaws.com/u[loads/contracts'
disputes_uploads = environ.get('DISPUTES_UPLOADS')
contracts_uploads = environ.get('CONTRACTS_UPLOADS')
#################################################Send Email Function######################################
def send_email(to, subject, job_title, agree_link , mode):
    if (mode == 'applied'):
            html_content = render_template('Email/job_status.html', job_title=job_title, username=to, subject=subject)
    if (mode == 'approved'):
        html_content = render_template('Email/jobapplication_approved.html', job_title=job_title, username=to, agree_link=agree_link, subject=subject)
    if (mode == 'rejected'):
        html_content = render_template('Email/jobapplication_rejected.html', job_title=job_title, username=to, subject=subject)
    if (mode == 'started'):
        html_content = render_template('Email/job_started.html', job_title=job_title, username=to, subject=subject)
    if (mode == 'stopped'):
        html_content = render_template('Email/job_stopped.html', job_title=job_title, username=to, subject=subject)
    if (mode == 'invited'):
        html_content = render_template('Email/job_invited.html', job_title=job_title, username=to, subject=subject)
    if (mode == 'applicationInvite'):
        html_content = render_template('Email/app_invite.html', user_name=user_name, username=to, subject=subject)
    if (mode == 'dispute'):
        html_content = render_template('Email/dispute.html',username=agree_link, record_id=job_title, subject=subject)
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

#CREATE JOB
@jobs_main_bp.route("/job/", methods=['POST'])
@jwt_required
def createJob():
    """Add Job"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer"}),400)
        subscription_exists = bool(Subscriptions.query.filter_by(user=current_user).first())
        if subscription_exists:
            print('existing')
            subscription_instance = Subscriptions.query.filter_by(user=current_user).first()
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
                return make_response(jsonify({"error": "Your subscription plan has expired"}),400)
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
                return make_response(jsonify({"error": "Your subscription plan has expired"}),400)
        post_data = request.get_json()
        business_name = post_data['business_name']
        job_category = post_data['job_category']
        job_type = post_data.get('job_type')
        budget = post_data.get('budget')
        emergency_rate = post_data.get('emergency_rate')
        is_draft = post_data.get('is_draft')
        shift_type = post_data.get('shift_type')
        contract = post_data.get('contract',None)
        file_name = post_data.get('file_name',None)
        if contract:
            # print('contract',contract)
            try:
                path_to_image = contracts_uploads+file_name
                with open(path_to_image, "wb") as fh:
                    fh.write(base64.b64decode(contract))
                contract = file_name
            except Exception as e:
                print('error',e)
                contract = contract
            # images_list.append(image_name)
        print('contract',contract)
        if is_draft == "True":
            is_draft = True
        else:
            is_draft = False
        job_description = post_data['job_description']
        address = post_data['address']
        city = post_data['city']
        shift_start_date = post_data.get('shift_start_date')
        shift_end_date = post_data.get('shift_end_date')
        shift_start_time = post_data.get('shift_start_time')
        shift_end_time = post_data.get('shift_end_time')
        vacancies = post_data['vacancies']
        existing_job = Jobs.query.filter_by(business_name=business_name).filter_by(posted_by=current_user).first()
        if existing_job:
            return make_response(jsonify({"error":"Already existing job with same business name"}),400)
        job_profile = Jobs(
                business_name = business_name,
                job_category = job_category,
                job_type = job_type,
                budget = budget,
                emergency_rate = emergency_rate,
                shift_type = shift_type,
                contract = file_name,
                job_description = job_description,
                posted_by = current_user,
                address = address,
                city = city,
                shift_start_date = shift_start_date,
                shift_end_date = shift_end_date,
                shift_start_time = shift_start_time,
                shift_end_time = shift_end_time,
                vacancies = vacancies,
                is_draft = is_draft
            )
        db.session.add(job_profile)
        db.session.commit()  # Create Job profile
        db.session.close()
        user_profile_instance = User.query.get(current_user)
        try:
            company_name = user_profile_instance.name
        except Exception as e:
            company_name = ''
        all_jobs = db.session.query(Jobs).all()
        try:
            existing_job = all_jobs[-1]
        except Exception as e:
            existing_job = all_jobs[0]
        start_date = existing_job.shift_start_date
        today_date = date.today()
        delta = start_date - today_date
        days_remaining = delta.days
        profile_id = existing_job.id
        print('profile_id',profile_id)
        get_profile = db.session.query(Jobs).get(profile_id)
        print('get_profile',get_profile)
        profile_schema = JobsSchema()
        print('////',profile_schema)
        job = profile_schema.dump(get_profile)
        print('job----',job)
        print('is_draft',is_draft)
        if is_draft == False:
            return make_response(jsonify({"success":"Job post successfull",'job_details':job,'company_name':company_name}),200)
        else:
            return make_response(jsonify({"success":"Draft saved successfully",'draft_details':job,'company_name':company_name}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in saving job at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":"Error posting a job"}),400)


#CREATE
@jobs_main_bp.route("/inviteGuard", methods=['POST'])
@jwt_required
def inviteGuard():
    """Invite  for a Job"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
        post_data = request.get_json()
        job_id = post_data['job_id']
        guard_id = post_data['guard_id']
        job_profile_data = Jobs.query.get(job_id)
        # member_id = job_profile_data.posted_by
        member_data = User.query.get(guard_id)
        member_device_id = member_data.device_id
        member_email = member_data.email
        job_title = job_profile_data.business_name
        invite_profile = JobInvites(
                job_id = job_id,
                guard_id = guard_id
            )
        db.session.add(invite_profile)
        db.session.commit()  #Job Invite
        message_title = "Job Invitation"
        message_body = 'Invitation to apply for a job at'+job_title
        send_notification(member_device_id, message_title, message_body,'Job Invitation')
        subject = "Job Invitation-OpenArc"
        to = member_email
        body = 'Hello '+to+',\nYou are invited to apply on  job at:\n'+job_title
        try:
            send_email(to, subject, job_title, '', 'invited')
        except Exception as e:
            print('error sending email',e)
        get_invites = JobInvites.query.filter_by(job_id=job_id).filter_by(guard_id=guard_id)
        invites_schema = JobInvitesSchema(many=True)
        invites = invites_schema.dump(get_invites)
        return make_response(jsonify({"success":"Invitation sent"}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in applying for job at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)

######################################################Member Job Functions######################################

#browseJobs
@jobs_main_bp.route('/browseJobs', methods = ['GET'])
@jwt_required
def getRecommendedJobs():
    try:
        jobs_list = []
        job_dict = {}
        recommended_jobs_list = []
        recommended_job_dict = {}
        categories = ['Warehouse','Industrial Complex','Retail Store','Corporate Events',
        'NightClub']
        distance = 10
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Member"}),400)
        profile_instance = Profile.query.filter_by(user_id=current_user)
        try:
            for profile in profile_instance:
                user_city = profile.city
            print('user_city',user_city)
        except Exception as e:
            user_city = ''
        source = user_city
        get_jobs = Jobs.query.filter_by(is_draft=False).filter(Jobs.shift_start_date > date.today())
        if not get_jobs:
            return make_response(jsonify({"message":"No recommended Jobs found","recommended_jobs": jobs_list}))
        for job in get_jobs:
            job_city = job.city
            enquirer_id = job.posted_by
            employer_instance = User.query.get(enquirer_id)
            enquirer_company = employer_instance.name
            dest = job_city
            job_id = job.id
            application_instance_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).filter_by(applied_by=current_user).first())
            #API to get distance betwen two cities
            if source != '':
                r = requests.get(str(distance_matrix_url+'origins='+source+'&destinations='+dest+'&key='+'AIzaSyAbOQGYshvI_FCLYFaCWhYsXN5-x1T3ENk'))  
                response = r.json()
                try:
                    city_distance = response['rows'][0]['elements'][0]['distance']['text']
                    city_distance_km = city_distance.split(' ')[0]
                except Exception as e:
                    city_distance_km = 0
            else:
                city_distance_km = '5'
            print('city_distance_km',city_distance_km)
            if city_distance_km != 0:
                if ',' in city_distance_km:
                    city_distance_km = city_distance_km.replace(',','')
            if float(city_distance_km) < float(distance):
                recommended_job_dict['id'] = job.id
                recommended_job_dict['applied'] = application_instance_exists
                recommended_job_dict['business_name'] = job.business_name
                recommended_job_dict['job_category'] = job.job_category
                recommended_job_dict['job_type'] = job.job_type
                recommended_job_dict['budget'] = job.budget 
                recommended_job_dict['job_description'] = job.job_description
                recommended_job_dict['address'] = job.address
                recommended_job_dict['city'] = job.city
                recommended_job_dict['created_at'] = job.created_at
                recommended_job_dict['updated_at'] = job.updated_at
                recommended_job_dict['posted_by'] = job.posted_by
                recommended_job_dict['bidding_started'] = job.bidding_started
                recommended_job_dict['enquirer_company'] = enquirer_company
                recommended_job_dict['shift_start_date'] = job.shift_start_date
                recommended_job_dict['shift_end_date'] = job.shift_end_date
                recommended_job_dict['shift_start_time'] = job.shift_start_time
                recommended_job_dict['shift_end_time'] = job.shift_end_time
                recommended_jobs_list.append(recommended_job_dict.copy())
        jobs_exists = bool(Jobs.query.filter_by(is_draft=False).filter(Jobs.shift_start_date > date.today()).first())
        if jobs_exists:
            jobs = Jobs.query.filter_by(is_draft=False).filter(Jobs.shift_start_date > date.today())
            for job in jobs:
                job_id = job.id
                application_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).filter_by(applied_by=current_user).first())
                applicants_count = AppliedJobs.query.filter_by(job_id=job_id).count()
                employer_id = job.posted_by
                employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
                if employer_profile_exists:
                    employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
                    profile_pic = employer_profile.company_logo
                else:
                    profile_pic = ''
                saved = bool(SavedJobs.query.filter_by(job_id=job_id).filter_by(saved_by=current_user).first())
                job_dict['saved'] = saved
                job_dict['applied'] = application_exists
                job_dict['id'] = job.id
                job_dict['business_name'] = job.business_name
                job_dict['job_category'] = job.job_category
                job_dict['job_type'] = job.job_type
                job_dict['budget'] = job.budget 
                job_dict['job_description'] = job.job_description
                job_dict['address'] = job.address
                job_dict['city'] = job.city
                job_dict['created_at'] = job.created_at
                job_dict['updated_at'] = job.updated_at
                job_dict['posted_by'] = job.posted_by
                job_dict['bidding_started'] = job.bidding_started
                job_dict['enquirer_company'] = enquirer_company
                job_dict['shift_start_date'] = job.shift_start_date
                job_dict['shift_end_date'] = job.shift_end_date
                job_dict['shift_start_time'] = job.shift_start_time
                job_dict['shift_end_time'] = job.shift_end_time
                job_dict['shift_type'] = job.shift_type
                job_dict['profile_pic'] = profile_pic
                job_dict['applicants_count'] = applicants_count
                jobs_list.append(job_dict.copy())
        return make_response(jsonify({"recommended_jobs": recommended_jobs_list,"jobs":jobs_list}))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in browse job at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)

#Save Job
@jobs_main_bp.route("/saveJob/", methods=['POST'])
@jwt_required
def saveJob():
    """saveJob"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Member"}),400)
        post_data = request.get_json()
        job_id = post_data['job_id']
        exists = bool(SavedJobs.query.filter_by(job_id=job_id).filter_by(saved_by=current_user).first())
        if exists:
            return make_response(jsonify({"error": "You have already saved this job"}),400)
        else:
            saved_profile = SavedJobs(
                    job_id = job_id,
                    saved_by = current_user,
                )
            db.session.add(saved_profile)
            db.session.commit()  # Create Enquirer profile
        return make_response(jsonify({"status":"success",'message':'save succesfull'}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in save jobs at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#City Filter Jobs
@jobs_main_bp.route("/cityFilterJobs/", methods=['POST'])
@jwt_required
def cityFilterJobs():
    """City Filter Jobs"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Member"}),400)
        jobs_list = []
        job_dict = {}
        post_data = request.get_json()
        city = post_data['city']
        try:
            city_list = city.split(',')
        except Exception as e:
            city_list = list(city)
        for city in city_list:
            print('city>',city)
            jobs_exists = bool(Jobs.query.filter(Jobs.shift_start_date > date.today()).filter_by(is_draft=False).filter_by(city=city).first())
            if jobs_exists:
                jobs = Jobs.query.filter(Jobs.shift_start_date > date.today()).filter_by(is_draft=False).filter_by(city=city)
                for job in jobs:
                    job_id = job.id
                    print('job_id',job_id)
                    application_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).filter_by(applied_by=current_user).first())
                    applicants_count = AppliedJobs.query.filter_by(job_id=job_id).count()
                    employer_id = job.posted_by
                    employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
                    if employer_profile_exists:
                        employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
                        employer_instance = User.query.get(employer_id)
                        profile_pic = employer_profile.company_logo
                        enquirer_company = employer_instance.name
                    else:
                        profile_pic = ''
                        enquirer_company = ''
                    saved = bool(SavedJobs.query.filter_by(job_id=job_id).filter_by(saved_by=current_user).first())
                    job_dict['saved'] = saved
                    job_dict['id'] = job.id
                    job_dict['applied'] = application_exists
                    job_dict['business_name'] = job.business_name
                    job_dict['job_category'] = job.job_category
                    job_dict['job_type'] = job.job_type
                    job_dict['budget'] = job.budget 
                    job_dict['job_description'] = job.job_description
                    job_dict['address'] = job.address
                    job_dict['city'] = job.city
                    job_dict['created_at'] = job.created_at
                    job_dict['updated_at'] = job.updated_at
                    job_dict['posted_by'] = job.posted_by
                    job_dict['bidding_started'] = job.bidding_started
                    job_dict['enquirer_company'] = enquirer_company
                    job_dict['shift_start_date'] = job.shift_start_date
                    job_dict['shift_end_date'] = job.shift_end_date
                    job_dict['shift_start_time'] = job.shift_start_time
                    job_dict['shift_end_time'] = job.shift_end_time
                    job_dict['shift_type'] = job.shift_type
                    job_dict['profile_pic'] = profile_pic
                    job_dict['applicants_count'] = applicants_count
                    jobs_list.append(job_dict.copy())
        return make_response(jsonify({"jobs":jobs_list}))
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in filter city jobs at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#READ BY DISTANCE
@jobs_main_bp.route('/filterJobs/', methods = ['POST'])
@jwt_required
def getFilteredJobs():
    try:
        job_dict = {}
        jobs_list = []
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Member"}),400)
        ########New#############
        post_data = request.get_json()
        proximity = post_data['proximity']
        hourly_rate = post_data['hourly_rate']
        category_list = post_data['category']
        categories = list(category_list)
        print('category_list',category_list,type(category_list))
        if ((category_list == '') and (hourly_rate == '') and (proximity == '')):
            return make_response(jsonify({"error": "Please select atleast one filter"}),400)
        jobs_exists = bool(Jobs.query.filter(Jobs.shift_start_date > date.today()).filter_by(is_draft=False).first())
        if jobs_exists:
            print('exist')
            if category_list:
                print('if')
                jobs = Jobs.query.filter(Jobs.job_category.in_(categories)).filter(Jobs.shift_start_date > date.today()).filter_by(is_draft=False)
                if jobs:
                    for job in jobs:
                        print('jjj',job.id)
                else:
                    return make_response(jsonify({"error": "No jobs with such category"}),400)
            else:
                print('else')
                jobs = Jobs.query.filter(Jobs.shift_start_date > date.today()).filter_by(is_draft=False)
            if proximity:
                proximity_value = post_data['proximity']
                profile_exists = bool(Profile.query.filter_by(user_id=current_user).first())
                profile_instance = Profile.query.filter_by(user_id=current_user).first()
                if profile_instance:
                    source = profile_instance.city
                else: 
                    source = ''
                for job in jobs:
                    job_id = job.id
                    print('job_id',job_id)
                    dest = job.city
                    if source != '':
                        #API to get distance betwen two cities
                        r = requests.get(str(distance_matrix_url+'origins='+source+'&destinations='+dest+'&key='+'AIzaSyAbOQGYshvI_FCLYFaCWhYsXN5-x1T3ENk'))  
                        response = r.json()
                        try:
                            city_distance = response['rows'][0]['elements'][0]['distance']['text']
                            city_distance_km = city_distance.split(' ')[0]
                            if ',' in city_distance_km:
                                city_distance_km = city_distance_km.replace(',','')
                        except Exception as e:
                            print('error in city distance',e)
                            city_distance_km = 0
                    else:
                        city_distance_km = '10'
                    print('distance',city_distance_km)
                    applicants_count = AppliedJobs.query.filter_by(job_id=job_id).count()
                    employer_id = job.posted_by
                    employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
                    if employer_profile_exists:
                        employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
                        employer_instance = User.query.get(employer_id)
                        profile_pic = employer_profile.company_logo
                        enquirer_company = employer_instance.name
                    else:
                        profile_pic = ''
                        enquirer_company = ''
                    saved = bool(SavedJobs.query.filter_by(job_id=job_id).filter_by(saved_by=current_user).first())
                    application_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).filter_by(applied_by=current_user).first())
                    if proximity_value == 'Within 10 kms':
                        if int(city_distance_km) <= 10:
                            job_dict['distance'] = str(city_distance_km)+'km'
                            job_dict['saved'] = saved
                            job_dict['applied'] = application_exists
                            job_dict['id'] = job.id
                            job_dict['business_name'] = job.business_name
                            job_dict['job_category'] = job.job_category
                            job_dict['job_type'] = job.job_type
                            job_dict['budget'] = job.budget 
                            job_dict['job_description'] = job.job_description
                            job_dict['address'] = job.address
                            job_dict['city'] = job.city
                            job_dict['created_at'] = job.created_at
                            job_dict['updated_at'] = job.updated_at
                            job_dict['posted_by'] = job.posted_by
                            job_dict['bidding_started'] = job.bidding_started
                            job_dict['enquirer_company'] = enquirer_company
                            job_dict['shift_start_date'] = job.shift_start_date
                            job_dict['shift_end_date'] = job.shift_end_date
                            job_dict['shift_start_time'] = job.shift_start_time
                            job_dict['shift_end_time'] = job.shift_end_time
                            job_dict['shift_type'] = job.shift_type
                            job_dict['profile_pic'] = profile_pic
                            job_dict['applicants_count'] = applicants_count                        
                            jobs_list.append(job_dict.copy())
                    if proximity_value == 'Within 20 kms':
                        if int(city_distance_km) <= 20:
                            job_dict['distance'] = str(city_distance_km)+'km'
                            job_dict['saved'] = saved
                            job_dict['applied'] = application_exists
                            job_dict['id'] = job.id
                            job_dict['business_name'] = job.business_name
                            job_dict['job_category'] = job.job_category
                            job_dict['job_type'] = job.job_type
                            job_dict['budget'] = job.budget 
                            job_dict['job_description'] = job.job_description
                            job_dict['address'] = job.address
                            job_dict['city'] = job.city
                            job_dict['created_at'] = job.created_at
                            job_dict['updated_at'] = job.updated_at
                            job_dict['posted_by'] = job.posted_by
                            job_dict['bidding_started'] = job.bidding_started
                            job_dict['enquirer_company'] = enquirer_company
                            job_dict['shift_start_date'] = job.shift_start_date
                            job_dict['shift_end_date'] = job.shift_end_date
                            job_dict['shift_start_time'] = job.shift_start_time
                            job_dict['shift_end_time'] = job.shift_end_time
                            job_dict['shift_type'] = job.shift_type
                            job_dict['profile_pic'] = profile_pic
                            job_dict['applicants_count'] = applicants_count                        
                            jobs_list.append(job_dict.copy())
                    if proximity_value == '30-45 kms':
                        if int(city_distance_km) >= 30 and int(city_distance_km) <= 45 :
                            job_dict['distance'] = str(city_distance_km)+'km'
                            job_dict['saved'] = saved
                            job_dict['applied'] = application_exists
                            job_dict['id'] = job.id
                            job_dict['business_name'] = job.business_name
                            job_dict['job_category'] = job.job_category
                            job_dict['job_type'] = job.job_type
                            job_dict['budget'] = job.budget 
                            job_dict['job_description'] = job.job_description
                            job_dict['address'] = job.address
                            job_dict['city'] = job.city
                            job_dict['created_at'] = job.created_at
                            job_dict['updated_at'] = job.updated_at
                            job_dict['posted_by'] = job.posted_by
                            job_dict['bidding_started'] = job.bidding_started
                            job_dict['enquirer_company'] = enquirer_company
                            job_dict['shift_start_date'] = job.shift_start_date
                            job_dict['shift_end_date'] = job.shift_end_date
                            job_dict['shift_start_time'] = job.shift_start_time
                            job_dict['shift_end_time'] = job.shift_end_time
                            job_dict['shift_type'] = job.shift_type
                            job_dict['profile_pic'] = profile_pic
                            job_dict['applicants_count'] = applicants_count                        
                            jobs_list.append(job_dict.copy())
                    if proximity_value == '45-100 kms':
                        if int(city_distance_km) > 45 and int(city_distance_km) <= 100 :
                            job_dict['distance'] = str(city_distance_km)+'km'
                            job_dict['saved'] = saved
                            job_dict['applied'] = application_exists
                            job_dict['id'] = job.id
                            job_dict['business_name'] = job.business_name
                            job_dict['job_category'] = job.job_category
                            job_dict['job_type'] = job.job_type
                            job_dict['budget'] = job.budget 
                            job_dict['job_description'] = job.job_description
                            job_dict['address'] = job.address
                            job_dict['city'] = job.city
                            job_dict['created_at'] = job.created_at
                            job_dict['updated_at'] = job.updated_at
                            job_dict['posted_by'] = job.posted_by
                            job_dict['bidding_started'] = job.bidding_started
                            job_dict['enquirer_company'] = enquirer_company
                            job_dict['shift_start_date'] = job.shift_start_date
                            job_dict['shift_end_date'] = job.shift_end_date
                            job_dict['shift_start_time'] = job.shift_start_time
                            job_dict['shift_end_time'] = job.shift_end_time
                            job_dict['shift_type'] = job.shift_type
                            job_dict['profile_pic'] = profile_pic
                            job_dict['applicants_count'] = applicants_count                        
                    jobs_list.append(job_dict.copy())
                    if proximity_value == 'Within 200 kms':
                        if int(city_distance_km) < 200:
                            job_dict['distance'] = str(city_distance_km)+'km'
                            job_dict['saved'] = saved
                            job_dict['applied'] = application_exists
                            job_dict['id'] = job.id
                            job_dict['business_name'] = job.business_name
                            job_dict['job_category'] = job.job_category
                            job_dict['job_type'] = job.job_type
                            job_dict['budget'] = job.budget 
                            job_dict['job_description'] = job.job_description
                            job_dict['address'] = job.address
                            job_dict['city'] = job.city
                            job_dict['created_at'] = job.created_at
                            job_dict['updated_at'] = job.updated_at
                            job_dict['posted_by'] = job.posted_by
                            job_dict['bidding_started'] = job.bidding_started
                            job_dict['enquirer_company'] = enquirer_company
                            job_dict['shift_start_date'] = job.shift_start_date
                            job_dict['shift_end_date'] = job.shift_end_date
                            job_dict['shift_start_time'] = job.shift_start_time
                            job_dict['shift_end_time'] = job.shift_end_time
                            job_dict['shift_type'] = job.shift_type
                            job_dict['profile_pic'] = profile_pic
                            job_dict['applicants_count'] = applicants_count                        
                            jobs_list.append(job_dict.copy())
                    if proximity_value == 'National':
                        job_dict['distance'] = str(city_distance_km)+'km'
                        job_dict['saved'] = saved
                        job_dict['applied'] = application_exists
                        job_dict['id'] = job.id
                        job_dict['business_name'] = job.business_name
                        job_dict['job_category'] = job.job_category
                        job_dict['job_type'] = job.job_type
                        job_dict['budget'] = job.budget 
                        job_dict['job_description'] = job.job_description
                        job_dict['address'] = job.address
                        job_dict['city'] = job.city
                        job_dict['created_at'] = job.created_at
                        job_dict['updated_at'] = job.updated_at
                        job_dict['posted_by'] = job.posted_by
                        job_dict['bidding_started'] = job.bidding_started
                        job_dict['enquirer_company'] = enquirer_company
                        job_dict['shift_start_date'] = job.shift_start_date
                        job_dict['shift_end_date'] = job.shift_end_date
                        job_dict['shift_start_time'] = job.shift_start_time
                        job_dict['shift_end_time'] = job.shift_end_time
                        job_dict['shift_type'] = job.shift_type
                        job_dict['profile_pic'] = profile_pic
                        job_dict['applicants_count'] = applicants_count                        
                        jobs_list.append(job_dict.copy())
            if hourly_rate:
                final_list = []
                hourly_rate = post_data['hourly_rate']
                for d in jobs_list:
                    try:
                        budget = d['budget']
                        numbers = budget.replace('£','').replace('/','').replace('hr','')
                        print('numbers',numbers)
                        l = numbers.split('-')
                        total = sum([int(i) for i in l])
                        avg = int(total)/2
                    except Exception as e:
                        avg = 12
                    print(avg)
                    if hourly_rate == 'Less than £10':
                        if avg <= 10:
                            final_list.append(d)
                    if hourly_rate == '£10-£20':
                        if avg >= 10 and avg <=20:
                            final_list.append(d)
                    if hourly_rate == '£20-£30':
                        if avg > 20 and avg <= 30:
                            final_list.append(d)
                    if hourly_rate == 'More than £30':
                        if avg >= 30:
                            final_list.append(d)
                jobs_list = final_list
        ########Ends here######
        res_list = []
        for i in range(len(jobs_list)):
            if jobs_list[i] not in jobs_list[i + 1:]:
                res_list.append(jobs_list[i])
        return make_response(jsonify({"jobs":res_list}))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in filter jobs at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)


#browseJobs
@jobs_main_bp.route('/getInvites/', methods = ['GET'])
@jwt_required
def getInvites():
    try:
        jobs_list = []
        job_dict = {}
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Member"}),400)
        profile_instance = Profile.query.filter_by(user_id=current_user)
        jobs_exists = bool(JobInvites.query.filter_by(guard_id=current_user).first())
        if jobs_exists:
            invites = JobInvites.query.filter_by(guard_id=current_user)
            for invite in invites:
                job_id = invite.job_id
                job = Jobs.query.get(job_id)
                applicants_count = AppliedJobs.query.filter_by(job_id=job_id).count()
                employer_id = job.posted_by
                employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
                if employer_profile_exists:
                    employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
                    employer_instance = User.query.get(employer_id)
                    profile_pic = employer_profile.company_logo
                    enquirer_company = employer_instance.name
                else:
                    profile_pic = ''
                    enquirer_company = ''
                saved = bool(SavedJobs.query.filter_by(job_id=job_id).filter_by(saved_by=current_user).first())
                job_dict['saved'] = saved
                job_dict['job_id'] = job.id
                job_dict['business_name'] = job.business_name
                job_dict['job_category'] = job.job_category
                job_dict['job_type'] = job.job_type
                job_dict['budget'] = job.budget 
                job_dict['job_description'] = job.job_description
                job_dict['address'] = job.address
                job_dict['city'] = job.city
                job_dict['created_at'] = job.created_at
                job_dict['updated_at'] = job.updated_at
                job_dict['posted_by'] = job.posted_by
                job_dict['bidding_started'] = job.bidding_started
                job_dict['enquirer_company'] = enquirer_company
                job_dict['shift_start_date'] = job.shift_start_date
                job_dict['shift_end_date'] = job.shift_end_date
                job_dict['shift_start_time'] = job.shift_start_time
                job_dict['shift_end_time'] = job.shift_end_time
                job_dict['shift_type'] = job.shift_type
                job_dict['profile_pic'] = profile_pic
                job_dict['applicants_count'] = applicants_count
                jobs_list.append(job_dict.copy())
        return make_response(jsonify({"jobs":jobs_list}))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in invites list  at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)

#READ JOB DETAILS BY ID
@jobs_main_bp.route('/job/<id>', methods = ['GET'])
def getJobById(id):
    try:
        job_list = []
        job_dict = {}
        job = Jobs.query.get(id)
        employer  = job.posted_by
        employer_instance = User.query.get(employer)
        employer_name = employer_instance.name
        profile_instance = EnquirerProfile.query.filter_by(enquirer_id=employer).first()
        try:
            company_name = profile_instance.company_name
        except Exception as e:
            company_name = ''
        job_dict['id'] = job.id
        job_dict['business_name'] = job.business_name
        job_dict['job_category'] = job.job_category
        job_dict['job_type'] = job.job_type
        job_dict['budget'] = job.budget 
        job_dict['job_description'] = job.job_description
        job_dict['address'] = job.address
        job_dict['city'] = job.city
        job_dict['created_at'] = job.created_at
        job_dict['updated_at'] = job.updated_at
        job_dict['posted_by'] = job.posted_by
        job_dict['employer_name'] = employer_name
        job_dict['bidding_started'] = job.bidding_started
        job_dict['company_name'] = company_name
        job_dict['shift_start_date'] = job.shift_start_date
        job_dict['shift_end_date'] = job.shift_end_date
        job_dict['shift_start_time'] = job.shift_start_time
        job_dict['shift_end_time'] = job.shift_end_time
        start_date = job.shift_start_date
        today_date = date.today()
        delta = start_date - today_date
        days_remaining = delta.days
        job_dict['remaining_days'] = days_remaining
        members_data  = []
        members_data_dict = {}
        application_exists = bool(AppliedJobs.query.filter_by(job_id=id).first())
        if not application_exists:
            job_list.append(job_dict.copy())
            return make_response(jsonify({"job_details": job_dict, 'members_count':0, 'members': []}),200)

        try:
            applied_jobs_instance = AppliedJobs.query.filter_by(job_id=id)
        except Exception as e:
            return make_response(jsonify({"error": "No member has applied for this job yet "}),400)
        for application in applied_jobs_instance:
            member_id = application.applied_by
            user_instance = User.query.get(member_id)
            job_dict['is_funded'] = application.is_funded
            # job_dict['transaction_initiated'] = application.transaction_initiated
            job_dict['application_id'] = application.id
            status = application.application_status
            if status == AppliedJobStatusEnum.pending:
                job_dict['application_status'] = 'pending'
            if status == AppliedJobStatusEnum.approved:
                job_dict['application_status'] = 'approved'
            if status == AppliedJobStatusEnum.rejected:
                job_dict['application_status'] = 'rejected'
            if status == AppliedJobStatusEnum.interested:
                job_dict['application_status'] = 'interested'
            print('job_dict',job_dict)
            job_list.append(job_dict.copy())
            try:
                profile_instance = Profile.query.filter_by(user_id=member_id)
                for instance in profile_instance:
                    profile_pic = instance.profile_pic
                    city = instance.city
                    geolocator = Nominatim(user_agent="openarc")
                    location = geolocator.geocode(city)
                    latitude = location.latitude
                    longitude = location.longitude
            except Exception as e:
                    latitude = ''
                    longitude = ''
                    profile_pic = ''
            reviews_instance = Reviews.query.filter_by(member_id=member_id).first()
            try:
                rating = int(reviews_instance.stars)
            except Exception as e:
                rating = 5
            hourly_rate = application.pay_expected+" per hour"
            members_data_dict['member_id'] = member_id
            members_data_dict['name'] = user_instance.name
            members_data_dict['hourly_rate'] = hourly_rate
            members_data_dict['latitude'] = latitude
            members_data_dict['longitude'] = longitude
            members_data_dict['profile_pic'] = profile_pic
            members_data_dict['rating'] = rating
            members_data.append(members_data_dict.copy())
        members_count = len(members_data)
        return make_response(jsonify({"job_details": job_dict, 'members_count':members_count, 'members': members_data}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting  job details at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)

#Saved Jobs
@jobs_main_bp.route("/savedJobs/", methods=['GET'])
@jwt_required
def savedJobs():
    """Saved Jobs"""
    try:
        jobs_list = []
        job_dict = {}
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Member"}),400)
        profile_instance = Profile.query.filter_by(user_id=current_user)
        jobs_exists = bool(SavedJobs.query.filter_by(saved_by=current_user).first())
        if jobs_exists:
            saved_jobs = SavedJobs.query.filter_by(saved_by=current_user)
            for instance in saved_jobs:
                instance_id = instance.id
                job_id = instance.job_id
                job = Jobs.query.get(job_id)
                today_date = datetime.date.today()
                if job.shift_end_date < today_date:
                    status = 'Expired'
                else:
                    status = 'Active' 
                applicants_count = AppliedJobs.query.filter_by(job_id=job_id).count()
                employer_id = job.posted_by
                employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
                if employer_profile_exists:
                    employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
                    employer_instance = User.query.get(employer_id)
                    profile_pic = employer_profile.company_logo
                    enquirer_company = employer_instance.name
                else:
                    profile_pic = ''
                    enquirer_company = ''
                saved = bool(SavedJobs.query.filter_by(job_id=job_id).filter_by(saved_by=current_user).first())
                job_dict['instance_id'] = instance_id
                job_dict['saved'] = saved
                job_dict['id'] = job.id
                job_dict['status'] = status
                job_dict['business_name'] = job.business_name
                job_dict['job_category'] = job.job_category
                job_dict['job_type'] = job.job_type
                job_dict['budget'] = job.budget 
                job_dict['job_description'] = job.job_description
                job_dict['address'] = job.address
                job_dict['city'] = job.city
                job_dict['created_at'] = job.created_at
                job_dict['updated_at'] = job.updated_at
                job_dict['posted_by'] = job.posted_by
                job_dict['bidding_started'] = job.bidding_started
                job_dict['enquirer_company'] = enquirer_company
                job_dict['shift_start_date'] = job.shift_start_date
                job_dict['shift_end_date'] = job.shift_end_date
                job_dict['shift_start_time'] = job.shift_start_time
                job_dict['shift_end_time'] = job.shift_end_time
                job_dict['shift_type'] = job.shift_type
                job_dict['profile_pic'] = profile_pic
                job_dict['applicants_count'] = applicants_count
                jobs_list.append(job_dict.copy())
        return make_response(jsonify({"jobs":jobs_list}))
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in saved jobs list at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)

@jobs_main_bp.route('/removeSavedJob/<saved_instance_id>', methods = ['DELETE'])
@jwt_required
def removeSavedJob(saved_instance_id):
    current_user = get_jwt_identity()
    user_instance = User.query.get(current_user)
    if user_instance.user_type == 'member':
        pass
    else:
        return make_response(jsonify({"error": "Function only allowed for Member"}),400)
    saved_jobs_list = []
    members_dict = {}
    get_profile = SavedJobs.query.get(saved_instance_id)
    if get_profile == None:
        return make_response(jsonify({"error": "No such profile exists"}),400)
    try:
        local_object = db.session.merge(get_profile)
        db.session.delete(local_object)
    except Exception as e:
        print('error in commit',e)
        db.session.delete(get_profile)
    db.session.commit()
    return make_response(jsonify({"success":"Job Removed successfully"}),200)

####################################################################################################################
#CREATE
@jobs_main_bp.route("/applyJob/", methods=['POST'])
@jwt_required
def ApplyJob():
    """Apply  for a Job"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        post_data = request.get_json()
        job_id = post_data['job_id']
        message = post_data['message']
        pay_expected = post_data['pay_expected']
        status = post_data['member_status']
        job_profile_data = Jobs.query.get(job_id)
        enquirer_id = job_profile_data.posted_by
        enquirer_data = User.query.get(enquirer_id)
        employer_device_id = enquirer_data.device_id
        enquirer_email = enquirer_data.email
        business_name = job_profile_data.business_name
        job_title = business_name
        existing_job = AppliedJobs.query.filter_by(job_id=job_id).filter_by(applied_by=current_user).first()
        if existing_job:
            return make_response(jsonify({"error":"Already Applied on this job"}),400)
        user_applied = AppliedJobs.query.filter_by(applied_by=current_user)
        # for application in user_applied:
        #     if ((application.member_status == "Accept")  and (application.is_active == True)):
        #         return make_response(jsonify({"error":"You can not apply on any other job untill your active job completes"}),400)
        job_profile = AppliedJobs(
                job_id = job_id,
                message = message,
                pay_expected = pay_expected,
                applied_by = current_user,
                member_status = status
            )
        chat_instance = ChatHistory(
            message = message,
            sent_by = current_user,
            sent_to = enquirer_id
            )
        notification_message = user_instance.name + ' has applied for your job titled ' + business_name
        notification = EnquirerNotification(
            body = notification_message,
            employer_id = enquirer_id,
            status = 'unread'
            )
        db.session.add(notification)
        db.session.add(job_profile)
        db.session.add(chat_instance)
        db.session.commit()  # Create Applied Job profile
        if ((status == 'Interested') or (status == 'interested')):
            interested_employees = job_profile_data.interested_count
            if ((interested_employees == '') or ( interested_employees == None)):
                job_profile_data.interested_count = 1
            else:
                job_profile_data.interested_count = int(interested_employees)+1
            # db.session.add(job_profile_data)
            try:
                local_object = db.session.merge(job_profile_data)
                db.session.add(local_object)
            except Exception as e:
                print('error in commit',e)
                db.session.add(job_profile_data)
            db.session.commit()
        updated_job_data = Jobs.query.get(job_id)
        if((updated_job_data.interested_count != '') and (updated_job_data.interested_count != None)):
            if(int(updated_job_data.interested_count) == int(updated_job_data.required_employees)):
                    updated_job_data.bidding_started = True
                    # db.session.add(updated_job_data)
                    try:
                        local_object = db.session.merge(updated_job_data)
                        db.session.add(local_object)
                    except Exception as e:
                        print('error in commit',e)
                        db.session.add(updated_job_data)
                    db.session.commit()
        message_title = "Job Application"
        message_body = 'Someone has applied on your job '+business_name
        send_notification(employer_device_id, message_title, message_body, 'Job Application Received')
        subject = "Job Application-OpenArc"
        to = enquirer_email
        body = 'Hello '+to+',\nSomeone has applied on your job titled:\n'+business_name
        try:
            send_email(to, subject, job_title, '', 'applied')
        except Exception as e:
            print('error sending email',e)
        return make_response(jsonify({"success":"You have applied successfully"}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in applying for job at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)



#Reject a job application
@jobs_main_bp.route('/rejectApplication/<application_id>', methods = ['POST'])
@jwt_required
def rejectApplication(application_id):
    current_user = get_jwt_identity()
    user_instance = User.query.get(current_user)
    if user_instance.user_type == 'enquirer':
        pass
    else:
        return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
    application_data = AppliedJobs.query.get(application_id)
    member_id = application_data.applied_by
    job_id = application_data.job_id
    member_data = User.query.get(member_id)
    member_device_id = member_data.device_id
    member_email = member_data.email
    job_profile_data = Jobs.query.get(job_id)
    job_title = job_profile_data.business_name
    try:
        applied_jobs = AppliedJobs.query.filter_by(job_id=job_id)
    except Exception as e:
            return make_response(jsonify({"error":"No application for this job yet"}),400)
    try:
        application_data = AppliedJobs.query.filter_by(job_id=job_id).filter_by(applied_by=member_id)
        if application_data:
            for application in application_data:
                if application.application_status == AppliedJobStatusEnum.rejected:        
                    return make_response(jsonify({"error":"Already Rejected"}),400)
                else:
                    application.application_status="rejected"
                    db.session.add(application)
                    db.session.commit()
                    message_title = "Job Application Rejected-OpenArc"
                    message_body = 'Your application has been rejected for job at'+job_title
                    send_notification(member_device_id, message_title, message_body, 'Application Rejected')
                    subject = "Job Application Rejected-OpenArc"
                    to = member_email
                    body = 'Hello '+to+',\nYour application has been rejected for job at\n'+job_title
                    try:
                        send_email(to, subject, job_title, 'rejected', '')
                    except Exception as e:
                        print('error sending email',e)
                    return make_response(jsonify({"success":"Job application Rejected successfully"}),200)
        else:
            return make_response(jsonify({"error":"No such application exists"}),400)
    except Exception as e:
        print('error in reject menber',e)
        return make_response(jsonify({"error":"No such application exists"}),400)


#Fund Details For a Job Application
@jobs_main_bp.route('/fundDetails/<application_id>/', methods = ['GET'])
@jwt_required
def FundDetails(application_id):
    fund_details_list = []
    fund_details_dict = {}
    current_user = get_jwt_identity()
    user_instance = User.query.get(current_user)
    if user_instance.user_type == 'enquirer':
        pass
    else:
        return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
    try:
        application_instance = AppliedJobs.query.get(application_id)
        if application_instance is None:
            return make_response(jsonify({"error":"No application exists"}),400)
    except Exception as e:
        return make_response(jsonify({"error":"No application exists"}),400)
    job_id = application_instance.job_id
    job_detail = Jobs.query.get(job_id)
    business_name = job_detail.business_name
    try:
        application = AppliedJobs.query.get(application_id)
        if application:
            job_budget = application.pay_expected
            print('job_budget',job_budget)
            if('-' in job_budget):
                budget_amount_list = job_budget.split('-')
                amount_str = str(budget_amount_list[1])
                per_hour_amount = amount_str.replace('$','')
            else:
                per_hour_amount = re.findall(r'\d+', job_budget)[0]
            print('per_hour_amount',per_hour_amount)
            #Time Calculation
            shift_start_time = job_detail.shift_start_time
            shift_end_time = job_detail.shift_end_time
            print('job_time',shift_start_time,shift_end_time)
            shift_start_time_hours = shift_start_time.split(':')[0]
            if int(shift_start_time_hours) > 12:
                start_time = shift_start_time
            else:
                start_time = convert24(shift_start_time)
            shift_end_time_hours = shift_end_time.split(':')[0]
            if int(shift_end_time_hours) > 12:
                end_time = shift_end_time
            else:
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
            fund_details_dict['Pay_Per_Hour'] = "£"+str(per_hour_amount)
            fund_details_dict['AOS_Standard_Addition_Per_Hour'] = float(fee_details.aos_standard_addition_per_hour)
            fund_details_dict['AOS_One_Off_Misc_Payment'] = float(fee_details.aos_one_off_misc_payment)
            fund_details_dict['Total_Expected_Hours_Worked'] = int(shifts_count)*int(shift_hours)
            fund_details_dict['Total_Pay'] = "£"+str(total_pay)
            fund_details_dict['Admin_Charges_@£1.5_Per_Hour'] = "£"+str(admin_charges)
            fund_details_dict['Bidding_Fees_@10P_Per_Hour'] = "£"+str(bidding_fees)
            fund_details_dict['Sub_Total'] = "£"+str(amount_excluding_vat)
            fund_details_dict['AOS_Account_Refund_Vat_@20%'] = "£"+str(vat_amount)
            fund_details_dict['Net_Payable'] = "£"+str(net_payable)
            fund_details_list.append(fund_details_dict)
            return make_response(jsonify({"fund_details":fund_details_list}),200)
            ###############Ends Here#################################
        else:
            return make_response(jsonify({"error":"No such application exists"}),400)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in getting fund details at line',lNumber,'error is',e)
        return make_response(jsonify({"error":str(e)}),400)

#Fund Details For a Job Application
@jobs_main_bp.route('/fundDetailsSession/<application_id>/', methods = ['GET'])
@jwt_required
def fundDetailsSession(application_id):
    fund_details_list = []
    fund_details_dict = {}
    current_user = get_jwt_identity()
    user_instance = User.query.get(current_user)
    email = user_instance.email
    if user_instance.user_type == 'enquirer':
        pass
    else:
        return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
    try:
        application_instance = AppliedJobs.query.get(application_id)
        if application_instance is None:
            return make_response(jsonify({"error":"No application exists"}),400)
    except Exception as e:
        return make_response(jsonify({"error":"No application exists"}),400)
    job_id = application_instance.job_id
    job_detail = Jobs.query.get(job_id)
    business_name = job_detail.business_name
    try:
        application = AppliedJobs.query.get(application_id)
        if application:
            job_budget = application.pay_expected
            print('job_budget',job_budget)
            if('-' in job_budget):
                budget_amount_list = job_budget.split('-')
                amount_str = str(budget_amount_list[1])
                per_hour_amount = amount_str.replace('$','')
            else:
                per_hour_amount = re.findall(r'\d+', job_budget)[0]
            #Time Calculation
            shift_start_time = job_detail.shift_start_time
            shift_end_time = job_detail.shift_end_time
            print('job_time',shift_start_time,shift_end_time)
            shift_start_time_hours = shift_start_time.split(':')[0]
            if int(shift_start_time_hours) > 12:
                start_time = shift_start_time
            else:
                start_time = convert24(shift_start_time)
            shift_end_time_hours = shift_end_time.split(':')[0]
            if int(shift_end_time_hours) > 12:
                end_time = shift_end_time
            else:
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
            fund_details_dict['Pay_Per_Hour'] = "£"+str(per_hour_amount)
            fund_details_dict['AOS_Standard_Addition_Per_Hour'] = float(fee_details.aos_standard_addition_per_hour)
            fund_details_dict['AOS_One_Off_Misc_Payment'] = float(fee_details.aos_one_off_misc_payment)
            fund_details_dict['Total_Expected_Hours_Worked'] = int(shifts_count)*int(shift_hours)
            fund_details_dict['Total_Pay'] = "£"+str(total_pay)
            fund_details_dict['Admin_Charges_@£1.5_Per_Hour'] = "£"+str(admin_charges)
            fund_details_dict['Bidding_Fees_@10P_Per_Hour'] = "£"+str(bidding_fees)
            fund_details_dict['Sub_Total'] = "£"+str(amount_excluding_vat)
            fund_details_dict['AOS_Account_Refund_Vat_@20%'] = "£"+str(vat_amount)
            fund_details_dict['Net_Payable'] = "£"+str(net_payable)
            fund_details_list.append(fund_details_dict)
            # return make_response(jsonify({"fund_details":fund_details_list}),200)
            ###Make Stripe Session##########
            price = stripe.Price.create(
              unit_amount=int(net_payable)*100,
              currency="gbp",
              product_data={'name':'fund_Job'}
            )
            price_id = price['id']
            session_obj = stripe.checkout.Session.create(
                  success_url="https://arcopen.space/checkout?sc_checkout=success&sc_sid={CHECKOUT_SESSION_ID}",
                  cancel_url="https://arcopen.space/checkout?sc_checkout=cancel",
                  payment_method_types=["card"],
                  customer_email = email,
                  line_items=[
                    {
                      "quantity": 1,
                      "name" : 'Job Fund',
                      "description" : 'Job Fund',
                      "amount" : int(net_payable)*100,
                      "currency" : 'gbp',
                    },
                  ],
                  metadata={
                    'Pay_Per_Hour' : "£"+str(per_hour_amount),
                    'AOS_Standard_Addition_Per_Hour' : float(fee_details.aos_standard_addition_per_hour),
                    'AOS_One_Off_Misc_Payment' : float(fee_details.aos_one_off_misc_payment),
                    'Total_Expected_Hours_Worked' : int(shifts_count)*int(shift_hours),
                    'Total_Pay' : "£"+str(total_pay),
                    'Admin_Charges_@£1.5_Per_Hour' : "£"+str(admin_charges),
                    'Bidding_Fees_@10P_Per_Hour' : "£"+str(bidding_fees),
                    'Sub_Total' : "£"+str(amount_excluding_vat),
                    'AOS_Account_Refund_Vat_@20%' : "£"+str(vat_amount),
                    'Net_Payable' : "£"+str(net_payable),
                  },
                  mode="payment"
            )
            print('session_id',session_obj.id)
            success_url = "https://arcopen.space/checkout?sc_checkout=success&sc_sid="+session_obj.id
            cancel_url = "https://arcopen.space/checkout?sc_checkout=cancel"

            # success_url="https://arcopen.space/success/"+session_obj.id,
            # cancel_url="https://arcopen.space/cancel/"+session_obj.id,
            session_obj['success_url'] = success_url
            session_obj['cancel_url'] = cancel_url
            return make_response(jsonify({"session":session_obj}),200) 
            ###############Ends Here#################################
        else:
            return make_response(jsonify({"error":"No such application exists"}),400)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in getting fund details at line',lNumber,'error is',e)
        return make_response(jsonify({"error":str(e)}),400)

#Fund For Job Application by Card
@jobs_main_bp.route("/cardJobFunding/", methods=['POST'])
@jwt_required
def addMoneyToAccount():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer"}),400)
        ###############Card Token######################
        post_data = request.form
        application_id = post_data['application_id']
        total_pay = post_data['total_pay']
        if '£' in total_pay:
            total_pay = total_pay.replace('£','')
        net_payable = post_data['net_payable']
        if '£' in net_payable:
            net_payable = net_payable.replace('£','')
        admin_charges = post_data['admin_charges']
        if '£' in admin_charges:
            admin_charges = admin_charges.replace('£','')
        bidding_fees = post_data['bidding_fees']
        if '£' in bidding_fees:
            bidding_fees = bidding_fees.replace('£','')
        vat = post_data['AOS_Account_Refund']
        if '£' in vat:
            vat = vat.replace('£','')
        misc_payment = post_data['AOS_One_Off_Misc_Payment']
        if '£' in misc_payment:
            misc_payment = misc_payment.replace('£','')
        standard_addition = post_data['AOS_Standard_Addition_Per_Hour']
        if '£' in standard_addition:
            standard_addition = standard_addition.replace('£','')
        card_number = post_data['card_number']
        exp_month = post_data['exp_month']
        exp_year = post_data['exp_year']
        cvv = post_data['cvv']
        if((card_number == '') or (exp_year=='') or (exp_month=='') or (cvv=='') or (application_id=='')):
            return make_response(jsonify({"error":'All parameters are required'}),400)
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
        if application_instance.application_status == AppliedJobStatusEnum.approved:        
            return make_response(jsonify({"error":"Already Approved"}),400)
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
            user_id = current_user,
            job_id = job_id
        )
        try:
            local_object = db.session.merge(funding_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(funding_instance)
        wallet_exists = bool(Wallet.query.filter_by(user_id=current_user).first())
        if wallet_exists:
            wallet_instance = Wallet.query.filter_by(user_id=current_user).first()
            balance = wallet_instance.balance
            total_balance = int(balance)+int(total_pay)
            wallet_instance.balance = total_balance
        else:
            wallet_instance = Wallet(
                    balance = total_pay,
                    user_id = current_user
            )
        try:
            local_object = db.session.merge(wallet_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(wallet_instance)
        db.session.commit()
        ##############################################Save to openarc db####################################
        admin_payment = float(admin_charges)+float(bidding_fees)+float(vat)+float(misc_payment)+float(standard_addition)
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
            send_notification(member_device_id, message_title, message_body)
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
            return make_response(jsonify({"message":"Application Approved","status":"success"}),200)
        except Exception as e:
            print('error in sending email',e)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('line',lNumber,'error',e)
        return make_response(jsonify({"error in payment":str(e)}),400)




######################################Log Time Screens###########################################

#Time Screen
@jobs_main_bp.route('/timesheetJobs/', methods = ['GET'])
@jwt_required
def timesheetJobs():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        if request.method=='GET':
            today_date = datetime.date.today()
            upcoming_list = []
            upcoming_dict ={}
            active_jobs_list = []
            active_job_dict = {}
            applications_exists = bool(AppliedJobs.query.filter_by(applied_by=current_user).filter_by(is_active=True).first())
            if applications_exists:
                applications = AppliedJobs.query.filter_by(applied_by=current_user).filter_by(is_active=True)
                for application in applications:
                    application_id = application.id
                    job_id = application.job_id
                    job_instance = Jobs.query.get(job_id)
                    posted_by = job_instance.posted_by
                    employer_instance = User.query.get(posted_by)
                    employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=posted_by).first())
                    if employer_profile_exists:
                        employer_profile = EnquirerProfile.query.filter_by(enquirer_id=posted_by).first()
                        profile_pic = employer_profile.company_logo
                        city = employer_profile.city
                    else:
                        profile_pic = ''
                        city = ''
                    shift_start_date = job_instance.shift_start_date
                    shift_end_date = job_instance.shift_end_date
                    delta = shift_start_date - today_date
                    days_remaining = delta.days
                    if shift_start_date > today_date:
                        upcoming_dict['job_id'] = job_instance.id
                        upcoming_dict['business_name'] = job_instance.business_name
                        upcoming_dict['company_logo'] = profile_pic
                        upcoming_dict['company_name'] = employer_instance.name
                        upcoming_dict['shift_start_date'] = shift_start_date
                        upcoming_dict['days_remaining'] = days_remaining
                        upcoming_list.append(upcoming_dict.copy())
                    if (shift_start_date == today_date) or (shift_start_date < today_date):
                        exists = bool(StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).first())
                        if exists:
                            job_log = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).first()
                            status = job_log.member_status
                            start_time = job_log.start_time
                            end_time = job_log.end_time
                            total_hours = job_log.hours
                            extra_hours = job_log.after_hours
                        else:
                            status = 'Inactive'
                            start_time = ''
                            end_time = ''
                            total_hours = ''
                            extra_hours = ''
                        active_job_dict['job_id'] = job_instance.id
                        active_job_dict['application_id'] = application_id
                        active_job_dict['business_name'] = job_instance.business_name
                        active_job_dict['company_logo'] = profile_pic
                        active_job_dict['company_name'] = employer_instance.name
                        active_job_dict['shift_start_date'] = shift_start_date
                        active_job_dict['today_date'] = today_date
                        active_job_dict['status'] = status
                        active_job_dict['start_time'] = str(start_time)
                        active_job_dict['end_time'] = str(end_time)
                        active_job_dict['total_hours'] = total_hours
                        active_job_dict['extra_hours'] = extra_hours
                        active_job_dict['city'] = city
                        active_jobs_list.append(active_job_dict.copy())
            return make_response(jsonify({"upcoming_jobs":upcoming_list,'active_job':active_jobs_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in get timesheet at line number',lNumber,'error is:',e)
    
#Change Status
@jobs_main_bp.route('/changeStatus/', methods = ['POST'])
@jwt_required
def changeStatus():
    try:
        today_date = datetime.date.today()
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        post_data = request.get_json()
        print('post_data',post_data)
        application_id = post_data['application_id']
        status = post_data['status']
        print('date>>',datetime.date.today())
        log_instance_exists = bool(StartedJobLogs.query.filter_by(application_id = application_id).filter_by(date=today_date).first())
        if log_instance_exists:
            log_instance = StartedJobLogs.query.filter_by(application_id = application_id).filter_by(date=today_date).first()
            application_instance = AppliedJobs.query.get(application_id)
            per_hour_rate = application_instance.pay_expected
            if '£' in per_hour_rate:
                per_hour_rate = per_hour_rate.replace('£','')
            job_id = application_instance.job_id
            job_details = Jobs.query.get(job_id)
            shift_start_time = job_details.shift_start_time
            shift_end_time = job_details.shift_end_time
            shift_end_date = job_details.shift_end_date
            print('shift_end_date>>',shift_end_date,'today>',today_date)
            if shift_end_date == today_date:
                work_status = 'completed'
            else:
                work_status = 'ongoing'
            start_dt = datetime.datetime.strptime(shift_start_time, '%I:%M %p')
            end_dt = datetime.datetime.strptime(shift_end_time, '%I:%M %p')
            diff = (end_dt - start_dt) 
            shift_hours = (diff.seconds/3600)
            start_time = log_instance.start_time
            end_time = current_time+":00"
            hours = datetime.datetime.strptime(end_time, '%H:%M:%S') - datetime.datetime.strptime(str(start_time), '%H:%M:%S')
            work_hours = (hours.seconds/3600)
            if work_hours > shift_hours:
                work_hours = shift_hours
                after_hours = work_hours - shift_hours
            else:
                work_hours = work_hours
                after_hours = 0
            after_hours_amount = ((33/100)*int(per_hour_rate))*int(after_hours)
            after_hours_amount = round(after_hours_amount,2)
            amount = float(per_hour_rate)*float(work_hours)
            amount = round(amount,2)
            log_instance.member_status = status
            log_instance.end_time = current_time
            log_instance.hours = round(work_hours,2)
            log_instance.after_hours = round(after_hours,2)
            log_instance.amount = amount
            log_instance.after_hours_amount = after_hours_amount 
        else:
            application_instance = AppliedJobs.query.get(application_id)
            if application_instance is None:
                return make_response(jsonify({"error": "No such application exists"}),400)
            job_id = application_instance.job_id
            job_details = Jobs.query.get(job_id)
            shift_start_time = job_details.shift_start_time
            shift_end_time = job_details.shift_end_time
            shift_end_date = job_details.shift_end_date
            print('shift_end_date>>',shift_end_date,'today>',today_date)
            if shift_end_date == today_date:
                work_status = 'completed'
                application_instance.is_active = False  
                try:
                    local_object = db.session.merge(application_instance)
                    db.session.add(local_object)
                except Exception as e:
                    print('error in commit',e)
                    db.session.add(application_instance)
                db.session.commit()
            else:
                work_status = 'ongoing'
            log_instance = StartedJobLogs(
                member_status = status,
                application_id = application_id,
                start_time = current_time,
            )
        try:
            local_object = db.session.merge(log_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(log_instance)
        db.session.commit()
        ##Check for payment Instance
        instance_exists = bool(JobPayments.query.filter_by(application_id=application_id).first())
        if instance_exists:
            print('instance_exists',status)
            if status == 'inactive':
                payment_instance = JobPayments.query.filter_by(application_id=application_id).first()
                payment_instance.work_status = work_status
                previous_hours = payment_instance.total_hours
                if previous_hours:
                    total_time = float(previous_hours) + float(work_hours) + float(after_hours)
                    payment_instance.total_hours = round(total_time,2)
                else:
                    total_time = float(work_hours) + float(after_hours)
                    payment_instance.total_hours = round(total_time,2)
                previous_payment = payment_instance.total_amount
                if previous_payment:
                    total_amount = float(previous_payment) + float(amount) + float(after_hours_amount)
                    payment_instance.total_amount = round(total_amount,2)
                else:
                    total_amount = float(amount) + float(after_hours_amount)
                    payment_instance.total_amount = round(total_amount,2)
                payment_instance.payment_status = 'pending'
                try:
                    local_object = db.session.merge(payment_instance)
                    db.session.add(local_object)
                except Exception as e:
                    print('error in commit',e)
                    db.session.add(payment_instance)
                db.session.commit()
        else:
            payment_instance = JobPayments(
                work_status = 'ongoing',
                application_id = application_id,
            )
            try:
                local_object = db.session.merge(payment_instance)
                db.session.add(local_object)
            except Exception as e:
                print('error in commit',e)
                db.session.add(payment_instance)
            db.session.commit()
        return make_response(jsonify({"status":status}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in change status at line number',lNumber,'error is:',e)


#History Screen
@jobs_main_bp.route('/jobsHistory/', methods = ['GET'])
@jwt_required
def jobsHistory():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        if request.method=='GET':
            today_date = datetime.date.today()
            past_jobs_list = []
            past_job_dict = {}
            applications_exists = bool(AppliedJobs.query.filter_by(applied_by=current_user).filter_by(is_funded=True).filter_by(is_active=False).first())
            if applications_exists:
                applications = AppliedJobs.query.filter_by(applied_by=current_user).filter_by(is_funded=True).filter_by(is_active=False)
                for application in applications:
                    application_id = application.id
                    job_id = application.job_id
                    job_instance = Jobs.query.get(job_id)
                    posted_by = job_instance.posted_by
                    job_type = job_instance.job_type
                    pay_rate = '£'+str(application.pay_expected)
                    employer_instance = User.query.get(posted_by)
                    employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=posted_by).first())
                    if employer_profile_exists:
                        employer_profile = EnquirerProfile.query.filter_by(enquirer_id=posted_by).first()
                        profile_pic = employer_profile.company_logo
                    else:
                        profile_pic = ''
                    shift_start_date = job_instance.shift_start_date
                    job_month = shift_start_date.strftime("%B")
                    shift_end_date = job_instance.shift_end_date
                    exists = bool(StartedJobLogs.query.filter_by(application_id=application_id).first())
                    if exists:
                        job_log = StartedJobLogs.query.filter_by(application_id=application_id)
                        for log in job_log:
                            start_time = log.start_time
                            end_time = log.end_time
                            total_hours = log.hours
                            extra_hours = log.after_hours
                            past_job_dict['start_date'] = log.date
                            past_job_dict['end_date'] = log.date
                            past_job_dict['start_time'] = start_time
                            past_job_dict['end_time'] = end_time
                            past_job_dict['total_hours'] = total_hours
                            past_job_dict['extra_hours'] = extra_hours
                    payment_details_exists = bool(JobPayments.query.filter_by(application_id=application_id).filter_by(work_status='completed').first()) 
                    if payment_details_exists:
                        payment_details = JobPayments.query.filter_by(application_id=application_id).filter_by(work_status='completed').first() 
                        payment_status = payment_details.payment_status
                        payment_amount = payment_details.total_amount
                        status = payment_details.work_status
                    reviews_exist = bool(Reviews.query.filter_by(application_id=application_id).first())
                    stars_list = []
                    if reviews_exist:
                        reviews = Reviews.query.filter_by(application_id=application_id)
                        for review in reviews:
                            stars = review.employer_stars
                            stars_list.append(int(stars))
                            total = sum(stars_list)
                            count = len(stars_list)
                            avg = total/count
                    else:
                        avg = 2
                    past_job_dict['job_id'] = job_instance.id
                    past_job_dict['application_id'] = application_id
                    past_job_dict['job_type'] = job_type
                    past_job_dict['pay_rate'] = pay_rate
                    past_job_dict['job_month'] = job_month
                    past_job_dict['business_name'] = job_instance.business_name
                    past_job_dict['company_logo'] = profile_pic
                    past_job_dict['company_name'] = employer_instance.name
                    past_job_dict['shift_start_date'] = shift_start_date
                    past_job_dict['today_date'] = today_date
                    past_job_dict['status'] = status
                    past_job_dict['start_time'] = str(start_time)
                    past_job_dict['end_time'] = str(end_time)
                    past_job_dict['total_hours'] = total_hours
                    past_job_dict['extra_hours'] = extra_hours
                    past_job_dict['payment_status'] = payment_status
                    past_job_dict['payment_amount'] = '£'+str(payment_amount)
                    past_job_dict['rating'] = avg
                    past_jobs_list.append(past_job_dict.copy())
            return make_response(jsonify({'past_jobs':past_jobs_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in get jobs history at line number',lNumber,'error is:',e)


#History Screen
@jobs_main_bp.route('/pastJobDetails/<application_id>', methods = ['GET'])
@jwt_required
def pastJobDetails(application_id):
    try:
        job_details = {}
        work_details_dict = {}
        work_details_list = []
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        application_instance = AppliedJobs.query.get(application_id)
        job_id = application_instance.job_id
        job_instance = Jobs.query.get(job_id)
        employer_id = job_instance.posted_by
        employer_instance = User.query.get(employer_id)
        employer_name = employer_instance.name
        business_name = job_instance.business_name
        job_type = job_instance.job_type
        budget = job_instance.budget
        shift_start_date = job_instance.shift_start_date
        shift_end_date = job_instance.shift_end_date
        shift_start_time = job_instance.shift_start_time
        shift_end_time = job_instance.shift_end_time
        reviews_exist = bool(Reviews.query.filter_by(application_id=application_id).first())
        stars_list = []
        if reviews_exist:
            reviews = Reviews.query.filter_by(application_id=application_id)
            for review in reviews:
                stars = review.employer_stars
                stars_list.append(int(stars))
                total = sum(stars_list)
                count = len(stars_list)
                avg = total/count
        else:
            avg = 4
        employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
        if employer_profile_exists:
            employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
            profile_pic = employer_profile.company_logo
        else:
            profile_pic = ''
        job_details['application_id'] = application_id
        job_details['job_id'] = job_id
        job_details['employer_id'] = employer_id
        job_details['rating'] = avg
        job_details['business_name'] = business_name
        job_details['job_type'] = job_type
        job_details['budget'] = budget
        job_details['shift_start_date'] = shift_start_date
        job_details['shift_end_date'] = shift_end_date
        job_details['shift_start_time'] = shift_start_time
        job_details['shift_end_time'] = shift_end_time
        job_details['profile_pic'] = profile_pic
        #Work Details
        log_instances = StartedJobLogs.query.filter_by(application_id=application_id)
        for instance in log_instances:
            work_details_dict['start_time'] = str(instance.start_time)
            work_details_dict['end_time'] = str(instance.end_time)
            work_details_dict['total_hours'] = instance.hours
            work_details_dict['after_hours'] = instance.after_hours
            work_details_dict['date'] = instance.date
            work_details_list.append(work_details_dict.copy())
        #Payment Details
        payment_details = {}
        payment_instance = JobPayments.query.filter_by(application_id=application_id).first()
        payment_details['total_amount'] = payment_instance.total_amount
        payment_details['payment_status'] = payment_instance.payment_status
        return make_response(jsonify({'payment_details':payment_details,'job_details':job_details,'work_details':work_details_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in get past job details at line number',lNumber,'error is:',e)

#######Finances####################
@jobs_main_bp.route("/getFinances/", methods=['GET'])
@jwt_required
def getFinances():
    """Get Finances"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Member"}),400)
        paid_transactions = []
        unpaid_transactions = []
        transaction_dict ={}
        amounts_list = []
        user_instance = User.query.get(current_user)
        past_projects_dict = {}
        jobs_list = []
        completed_instance_exists = bool(JobPayments.query.filter_by(work_status='completed').first())
        if completed_instance_exists:
            completed_instances = JobPayments.query.filter_by(work_status='completed')
            for instance in completed_instances:
                amount = instance.total_amount
                status = instance.payment_status
                instance_id = instance.id
                payment_date = instance.updated_at
                application_id = instance.application_id
                application_instances = AppliedJobs.query.filter_by(id=application_id).filter_by(is_active=False)
                for application in application_instances:
                    job_id = application.job_id
                    job_instance = Jobs.query.get(job_id)
                    member_id = application.applied_by
                    shift_start_time = job_instance.shift_start_date
                    shift_end_date = job_instance.shift_end_date
                    job_end_month = shift_end_date.strftime("%B")
                    job_id = job_instance.id
                    job_type= job_instance.job_type
                    employer_id = job_instance.posted_by
                    # print('employer',employer,'current_user',current_user)
                    if member_id == current_user:
                        if job_id not in jobs_list:
                            jobs_list.append(job_id)
                        business_name = job_instance.business_name 
                        city = job_instance.city
                        applications = AppliedJobs.query.filter_by(job_id=job_id)
                        for app_instance in applications:
                            app_id = app_instance.id
                            pay_instance = JobPayments.query.filter_by(application_id=app_id).first()
                        # employer_id = application.applied_by
                        employer_instance = User.query.get(employer_id)
                        employer_name = employer_instance.name 
                        employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
                        if employer_profile_exists:
                            employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
                            profile_pic = employer_profile.company_logo
                        else:
                            profile_pic = ''
                        reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).filter_by(application_id=application_id).first())
                        if reviews_exist:
                            review = Reviews.query.filter_by(member_id=member_id).filter_by(application_id=application_id).first()
                            stars = review.employer_stars
                        else:
                            stars = 4
                        print('status',status,'application_id',application_id)
                        if status == 'paid':
                            transaction_dict['transaction_id'] = instance_id 
                            transaction_dict['payment_date'] = payment_date 
                            transaction_dict['amount'] = '£'+str(amount)
                            transaction_dict['application_id'] = application_id
                            transaction_dict['employer_name'] = employer_name
                            transaction_dict['job_type'] = job_type
                            transaction_dict['profile_pic'] = profile_pic
                            transaction_dict['job_id'] = job_id
                            transaction_dict['month'] = job_end_month
                            transaction_dict['payment_status'] = status
                            transaction_dict['business_name'] = business_name
                            transaction_dict['stars'] = stars
                            paid_transactions.append(transaction_dict.copy())
                        else:
                            transaction_dict['transaction_id'] = instance_id 
                            transaction_dict['amount'] = '£'+str(amount)
                            transaction_dict['application_id'] = application_id
                            transaction_dict['employer_name'] = employer_name
                            transaction_dict['job_type'] = job_type
                            transaction_dict['profile_pic'] = profile_pic
                            transaction_dict['job_id'] = job_id
                            transaction_dict['month'] = job_end_month
                            transaction_dict['payment_status'] = status
                            transaction_dict['business_name'] = business_name
                            transaction_dict['stars'] = stars
                            unpaid_transactions.append(transaction_dict.copy())
            for d in paid_transactions:
                amount = d['amount']
                amount = amount.replace('£','')
                amounts_list.append(float(amount))
            total_amount = '£'+str(sum(amounts_list))
            mydate = datetime.datetime.now()
            month_name = mydate.strftime("%B")
            current_year = mydate.year
            print('current_year',current_year)
            total_jobs = str(len(jobs_list)) + ' jobs completed till ' + month_name +' '+ str(current_year)
        return make_response(jsonify({"paid_transactions":paid_transactions,
            'unpaid_transactions':unpaid_transactions,'total_paid':total_amount,'total_jobs':total_jobs}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in transactions  at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#Fund Details For a Job Application
@jobs_main_bp.route('/getInvoiceDetails/<application_id>/', methods = ['GET'])
@jwt_required
def getInvoiceDetails(application_id):
    fund_details_dict = {}
    current_user = get_jwt_identity()
    user_instance = User.query.get(current_user)
    member_name = user_instance.name
    if user_instance.user_type == 'member':
        pass
    else:
        return make_response(jsonify({"error": "Function only allowed for member"}),400)
    application_instance = AppliedJobs.query.get(application_id)
    payment_instance = JobPayments.query.filter_by(application_id=application_id).first()
    payment_status = payment_instance.payment_status
    fund_details_dict['payment_status'] = payment_status
    if payment_status == 'paid':
        payment_date = payment_instance.updated_at
        fund_details_dict['payment_date'] = payment_date
    job_id = application_instance.job_id
    job_detail = Jobs.query.get(job_id)
    employer_id = job_detail.posted_by
    employer_instance = User.query.get(employer_id)
    company_name = employer_instance.name
    start_date = job_detail.shift_start_date
    end_date = job_detail.shift_end_date
    member_id = application_instance.applied_by
    member_instance = User.query.get(member_id)
    member_name = member_instance.name
    employer_id = current_user
    employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
    if employer_profile_exists:
        employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
        profile_pic = employer_profile.company_logo
    else:
        profile_pic = ''
    business_name = job_detail.business_name
    try:
        application = AppliedJobs.query.get(application_id)
        job_budget = application.pay_expected
        payment_instance = JobPayments.query.filter_by(application_id=application_id).first()
        payment_date = payment_instance.updated_at
        total_hours = payment_instance.total_hours
        total_amount = payment_instance.total_amount
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
        total_pay = round(float(total_hours)*float(per_hour_amount),2)
        fee_details = MemberFees.query.get(1)
        admin_charges = round(0.25*float(total_hours),2)
        net_payable = round(float(total_amount)-float(admin_charges),2)
        reviews_exist = bool(Reviews.query.filter_by(application_id=application_id).first())
        stars_list = []
        if reviews_exist:
            reviews = Reviews.query.filter_by(application_id=application_id)
            for review in reviews:
                stars = review.employer_stars
                stars_list.append(int(stars))
                total = sum(stars_list)
                count = len(stars_list)
                avg = total/count
        else:
            avg = 4
        fund_details_dict['Agreed_Pay_Per_Hour'] = "£"+str(per_hour_amount)+'/hr'
        fund_details_dict['AOS_Standard_Addition_Per_Hour'] = float(fee_details.aos_standard_addition_per_hour)
        fund_details_dict['AOS_One_Off_Misc_Payment'] = "£0"
        fund_details_dict['rating'] = avg
        fund_details_dict['Total_Worked_Hours'] = total_hours
        fund_details_dict['Total_Pay'] = "£"+str(total_pay)
        fund_details_dict['Admin_Charges'] = "£"+str(admin_charges)
        fund_details_dict['AOS_Account_Refund'] = "£0"
        fund_details_dict['Net_Payable'] = "£"+str(net_payable)
        fund_details_dict['company_name'] = company_name
        fund_details_dict['profile_pic'] = profile_pic
        fund_details_dict['paid_to'] = member_name
        fund_details_dict['start_date'] = start_date
        fund_details_dict['end_date'] = end_date
        fund_details_dict['payment_date'] = payment_date
        return make_response(jsonify({"fund_details":fund_details_dict}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in getting fund details at line',lNumber,'error is',e)
        return make_response(jsonify({"error":str(e)}),400)

#Download invoice
@jobs_main_bp.route('/downloadInvoice/<application_id>/', methods = ['GET'])
@jwt_required
def downloadInvoice(application_id):
    fund_details_dict = {}
    current_user = get_jwt_identity()
    user_instance = User.query.get(current_user)
    application_instance = AppliedJobs.query.get(application_id)
    payment_instance = JobPayments.query.filter_by(application_id=application_id).first()
    payment_status = payment_instance.payment_status
    fund_details_dict['payment_status'] = payment_status
    if payment_status == 'paid':
        payment_date = payment_instance.updated_at
        fund_details_dict['payment_date'] = payment_date
    job_id = application_instance.job_id
    job_detail = Jobs.query.get(job_id)
    employer_id = job_detail.posted_by
    employer_instance = User.query.get(employer_id)
    company_name = employer_instance.name
    start_date = job_detail.shift_start_date
    end_date = job_detail.shift_end_date
    member_id = application_instance.applied_by
    member_instance = User.query.get(member_id)
    member_name = member_instance.name
    employer_id = current_user
    employer_profile_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
    if employer_profile_exists:
        employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
        profile_pic = employer_profile.company_logo
    else:
        profile_pic = ''
    business_name = job_detail.business_name
    try:
        application = AppliedJobs.query.get(application_id)
        job_budget = application.pay_expected
        payment_instance = JobPayments.query.filter_by(application_id=application_id).first()
        payment_date = payment_instance.updated_at
        total_hours = payment_instance.total_hours
        total_amount = payment_instance.total_amount
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
        total_pay = round(float(total_hours)*float(per_hour_amount),2)
        fee_details = MemberFees.query.get(1)
        admin_charges = round(0.25*float(total_hours),2)
        net_payable = round(float(total_amount)-float(admin_charges),2)
        reviews_exist = bool(Reviews.query.filter_by(application_id=application_id).first())
        stars_list = []
        if reviews_exist:
            reviews = Reviews.query.filter_by(application_id=application_id)
            for review in reviews:
                stars = review.employer_stars
                stars_list.append(int(stars))
                total = sum(stars_list)
                count = len(stars_list)
                avg = total/count
        else:
            avg = 4
        if user_instance.user_type == 'enquirer':
            body = {
                "data":{
                    "company_name": company_name,
                    "amount": "£"+str(net_payable),
                    "employee": member_name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_hours": total_hours,
                    "hourly_rate": "£"+str(per_hour_amount)+'/hr',
                    "payment_date": payment_date,
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
        else:
            body = {
                "data":{
                    'Agreed_Pay_Per_Hour' : "£"+str(per_hour_amount)+'/hr',
                    'AOS_Standard_Addition_Per_Hour' : float(fee_details.aos_standard_addition_per_hour),
                    'AOS_One_Off_Misc_Payment' : "£0",
                    'rating' : avg,
                    'Total_Worked_Hours' : total_hours,
                    'Total_Pay' : "£"+str(total_pay),
                    'Admin_Charges' : "£"+str(admin_charges),
                    'AOS_Account_Refund' : "£0",
                    'Net_Payable' : "£"+str(net_payable),
                    'company_name' : company_name,
                    'profile_pic' : profile_pic,
                    'paid_to' : user_instance.name,
                    'start_date' : start_date,
                    'end_date' : end_date,
                    'payment_date' : payment_date,
                }
            }
            sourceHtml = member_template.render(json_data=body["data"]) 
            outputFilename = str(member_id)+"_"+"invoice.pdf"
            # resultFile = open('/var/www/Projects/OpenArc/Push/openarc-flask/'+outputFilename, "w+b")
            resultFile = open('/var/www/html/uploads/member/'+outputFilename, "w+b")
            filepath = 'https://arcopen.space/files/uploads/member/'+outputFilename
            # convert HTML to PDF
            pisaStatus = pisa.CreatePDF(
                    src=sourceHtml,            # the HTML to convert
                    dest=resultFile)           # file handle to receive result

            # close output file
            resultFile.close()
        return make_response(jsonify({"message":'success','file_link':filepath}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in downloading fund details at line',lNumber,'error is',e)
        return make_response(jsonify({"error":str(e)}),400)

#CREATE
@jobs_main_bp.route("/inviteFriends/", methods=['POST'])
@jwt_required
def inviteFriend():
    """Invite  friends"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        user_name = user_instance.name
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        post_data = request.get_json()
        user_email = post_data['email']
        message_title = "Invitation For Application"
        message_body = 'Invitation to use app'
        # send_notification(member_device_id, message_title, message_body)
        subject = "App Invitation-OpenArc"
        to = user_email
        body = 'Hello '+to+',\nYou are invited to use openarc by your friend \n'+user_name
        try:
            send_email(to, subject, user_name, '', 'applicationInvite')
        except Exception as e:
            print('error sending email',e)
        return make_response(jsonify({"success":"Invitation sent"}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in invite friend at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":str(e)}),400)

######################################################################################################

################################################ EMPLOYER DISPUTE CRUD###############################################
#CREATE
@jobs_main_bp.route("/addDispute/", methods=['POST'])
@jwt_required
def addDispute():
    """Add  Complaint."""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
        post_data = request.get_json()
        job_id = post_data['job_id']
        description = post_data['description']
        dispute_type = post_data['dispute_type']
        amount = post_data['amount']
        member_id = post_data['member_id']
        submitted_by = current_user
        dispute_exists = bool(Disputes.query.filter_by(job_id=job_id).filter_by(member_id=member_id).filter_by(submitted_by=current_user).first())
        if dispute_exists:
            return make_response(jsonify({"error":"Dispute added already for same member"}),400)
        if ((job_id == '') or (description == '') or (member_id == '') or (amount == '') or (dispute_type == '')):
            return make_response(jsonify({"error":"All fields are required"}),400)
        dispute = Disputes(
                dispute_type = dispute_type,
                description = description,
                submitted_by = current_user,
                job_id = job_id,
                amount = amount,
                member_id = member_id,
                status = 'active'
            )
        db.session.add(dispute)
        db.session.commit()  # Create user complaint
        last_record_id = dispute.id
        user_name = user_instance.name
        message_title = "Dispute"
        message_body = 'Dispute Raised'
        send_notification(member_device_id, message_title, message_body, 'Dispute Added')
        subject = "Dipsute Raised-OpenArc"
        to = user_instance.email
        user_name = user_instance.name
        # body = 'Hello '+user_instance.name+',\nThanks for contacting Arc Open Space Support+'.
        # 'We're writing to let you know that your Arc Open Space Support request (#31256291) has been received and is being reviewed by our Support staff. We'll be back in touch soon.'
        try:
            send_email(to, subject, last_record_id, user_name, 'dispute')
        except Exception as e:
            print('error sending email',e)
        return make_response(jsonify({"success":"Dispute raised successfully"}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in saving dispute at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#READ Complaints Submitted by a User
@jobs_main_bp.route('/getDisputes', methods = ['GET'])
@jwt_required
def getDisputes():
    current_user = get_jwt_identity()
    get_complaints = Disputes.query.filter_by(submitted_by=current_user)
    complaints_list = []
    complaints_dict = {}
    import ast
    for complaint in get_complaints:
        complaints_dict['id']=complaint.id
        complaints_dict['description']=complaint.description
        complaints_dict['status']=complaint.status
        complaints_dict['dispute_type']=complaint.dispute_type
        complaints_dict['created_on']=complaint.created_at
        complaints_dict['member_id']=complaint.member_id
        complaints_list.append(complaints_dict.copy())
    return make_response(jsonify({"complaints": complaints_list}))


################################################ MEMBER DISPUTE CRUD###############################################
#CREATE
@jobs_main_bp.route("/memberAddDispute/", methods=['POST'])
@jwt_required
def memberAddDispute():
    """Add  Complaint."""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for enquirer"}),400)
        post_data = request.get_json()    
        title = post_data.get('title')
        job_id = post_data.get('job_id')
        details = post_data.get('details')
        images = post_data.get('images')
        images_list = []
        for img in images:
            image_dict = img
            keys = img.keys()
            keys_list = list(keys)
            image_name = keys_list[0]
            image_str = img[image_name]
            try:
                if 'base64' in image_str:
                    base64_data = re.sub('^data:image/.+;base64,', '', image_str)
                    picture_string = image_str.split(';')[0]
                path_to_image = disputes_uploads+'/'+image_name
                with open(path_to_image, "wb") as fh:
                    fh.write(base64.b64decode(base64_data))
                images_list.append(image_name)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                lNumber = exc_tb.tb_lineno
                print('error in image',image_name,'at line',lNumber,'error>>',e)
        dispute_exists = bool(Disputes.query.filter_by(job_id=job_id).filter_by(submitted_by=current_user).first())
        if dispute_exists:
            return make_response(jsonify({"error":"Dispute added already for same job"}),400)
        if ((job_id == '') or (details == '') or (title == '')):
            return make_response(jsonify({"error":"All fields are required"}),400)
        dispute_instance = MemberDisputes(
                title = title,
                details = details,
                job_id = job_id,
                images = str(images_list),
                submitted_by = current_user,
                status = 'open'
            )
        db.session.add(dispute_instance)
        db.session.commit()  # Create report
        last_record_id = dispute_instance.id
        user_name = user_instance.name
        message_title = "Dispute"
        message_body = 'Dispute Raised'
        try:
            send_notification(member_device_id, message_title, message_body,'Dispute Added')
        except Exception as e:
            pass
        subject = "Dipsute Raised-OpenArc"
        to = user_instance.email
        user_name = user_instance.name
        # body = 'Hello '+user_instance.name+',\nThanks for contacting Arc Open Space Support+'.
        # 'We're writing to let you know that your Arc Open Space Support request (#31256291) has been received and is being reviewed by our Support staff. We'll be back in touch soon.'
        try:
            send_email(to, subject, last_record_id, user_name, 'dispute')
        except Exception as e:
            print('error sending email',e)
        return make_response(jsonify({"success":"Dispute raised successfully"}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in saving member dispute at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)




#READ Complaints Submitted by a Member
@jobs_main_bp.route('/getMemberDisputes', methods = ['GET'])
@jwt_required
def getMemberDisputes():
    current_user = get_jwt_identity()
    print(current_user)
    get_complaints = MemberDisputes.query.filter_by(submitted_by=current_user)
    complaints_list = []
    complaints_dict = {}
    import ast
    for complaint in get_complaints:
        complaints_dict['id']=complaint.id
        complaints_dict['title']=complaint.title
        complaints_dict['details']=complaint.details
        complaints_dict['status']=complaint.status
        complaints_dict['job_id']=complaint.job_id
        complaints_dict['created_on']=complaint.created_at
        complaints_dict['submitted_by']=complaint.submitted_by
        complaints_list.append(complaints_dict.copy())
    return make_response(jsonify({"complaints": complaints_list}))




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


#######################Other Functions##############################

#READ ALL JOBS
@jobs_main_bp.route('/allJobs/', methods = ['GET'])
def getAllJobs():
    jobs_list = []
    job_dict = {}
    all_jobs = Jobs.query.all()
    for job in all_jobs:
        job_dict['id'] = job.id
        job_dict['job_title'] = job.business_name
        job_dict['job_category'] = job.job_category
        job_dict['payment_type'] = job.payment_type
        job_dict['fixed_price_budget'] = job.fixed_price_budget 
        job_dict['hourly_price_budget'] = job.hourly_price_budget
        job_dict['job_description'] = job.job_description
        job_dict['must_required'] = job.must_required
        job_dict['location'] = job.location
        job_dict['city'] = job.city
        job_dict['created_at'] = job.created_at
        job_dict['updated_at'] = job.updated_at
        job_dict['posted_by'] = job.posted_by
        job_dict['bidding_started'] = job.bidding_started
        user_profile_instance = EnquirerProfile.query.filter_by(enquirer_id=job.posted_by).first()
        company_name = user_profile_instance.company_name
        job_dict['company_name'] = company_name
        job_dict['start_date'] = job.start_date
        job_dict['shift'] = job.shift
        start_date = job.start_date
        today_date = date.today()
        delta = start_date - today_date
        days_remaining = delta.days
        job_dict['remaining_days'] = days_remaining
        applied_jobs_instance = bool(AppliedJobs.query.filter_by(job_id=job.id).first())
        if applied_jobs_instance:
            applicants_count = AppliedJobs.query.filter_by(job_id=job.id).count()
        else:
            applicants_count = 0
        job_dict['applicants_count'] = applicants_count
        jobs_list.append(job_dict.copy())
    return make_response(jsonify({'jobs_details':jobs_list}),200)


#UPDATE
@jobs_main_bp.route("/job/<id>", methods=['PUT'])
@jwt_required
def updateJob(id):
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer"}),400)
        data = request.get_json()
        get_job = Jobs.query.get(id)
        message_title = "Job Budget Updated-OpenArc"
        message_body = 'The budget for job has been updated'
        device_id_list = []
        job_applications = AppliedJobs.query.filter_by(job_id=id)
        if get_job == None:
            return make_response(jsonify({"error":"No such job exists"}),400)
        if data.get('job_title'):
            get_job.job_title = data['job_title']
        if data.get('job_category'):
            get_job.job_category = data['job_category']
        if data.get('payment_type'):
            get_job.payment_type= data['payment_type']
        if data.get('fixed_price_budget'):
            get_job.fixed_price_budget= data['fixed_price_budget']
            for application in job_applications:
                user_id = application.applied_by
                user_instance = User.query.get(user_id)
                device_id = user_instance.device_id
                device_id_list.append(device_id)
            send_notification(device_id_list, message_title, message_body)
        if data.get('hourly_price_budget'):
            get_job.hourly_price_budget= data['hourly_price_budget']
            for application in job_applications:
                user_id = application.applied_by
                user_instance = User.query.get(user_id)
                device_id = user_instance.device_id
                device_id_list.append(device_id)
            send_notification(device_id_list, message_title, message_body) 
        if data.get('job_description'):
            get_job.job_description= data['job_description'] 
        if data.get('must_required'):
            get_job.must_required= data['must_required']
        if data.get('location'):
            get_job.location= data['location']
        if data.get('city'):
            get_job.city= data['city'] 
        if data.get('required_employees'):
            get_job.required_employees= data['required_employees']   
        db.session.add(get_job)
        db.session.commit()
        job_schema = JobsSchema(only=['id','required_employees','job_title','city','location','job_category','payment_type','hourly_price_budget', 'fixed_price_budget','job_description','must_required'])
        job = job_schema.dump(get_job)
        return make_response(jsonify({"success":"Update successfull","job": job}))
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in update job at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":"Error in update"}),400)


#DELETE
@jobs_main_bp.route('/job/<id>', methods = ['DELETE'])
def deleteJob(id):
    job_instance = Jobs.query.get(id)
    if job_instance == None:
        return make_response(jsonify({"error":"No such job exists"}),400)
    if job_instance.is_active == True:
        return make_response(jsonify({"error":"Can not delete an active job"}),400)
    try:
        local_object = db.session.merge(job_instance)
        db.session.delete(local_object)
    except Exception as e:
        print('error in commit',e)
        # db.session.add(funding_instance)
        db.session.delete(job_instance)
    db.session.commit()
    return make_response(jsonify({"success":"Delete successfull"}),200)

#READ
@jobs_main_bp.route('/appliedJobs/', methods = ['GET'])
def getAppliedJobs():
    get_jobs = AppliedJobs.query.all()
    jobs_schema = AppliedJobsSchema(many=True)
    jobs = jobs_schema.dump(get_jobs)
    return make_response(jsonify({"AppliedJobs": jobs}))


#UPDATE
@jobs_main_bp.route("/applyJob/<id>", methods=['PUT'])
@jwt_required
def updateApplyJob(id):
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        data = request.get_json()
        get_profile = AppliedJobs.query.get(id)
        if get_profile == None:
            return make_response(jsonify({"error":"No such job exists"}),400)
        if data.get('pay_expected'):
            get_profile.pay_expected = data['pay_expected']
        if data.get('monthly_available'):
            get_profile.monthly_available = data['monthly_available']
        if data.get('message'):
            get_profile.message= data['message']  
        db.session.add(get_profile)
        db.session.commit()
        profile_schema = AppliedJobsSchema(only=['id','pay_expected','monthly_available','message','job_id'])
        profile = profile_schema.dump(get_profile)
        return make_response(jsonify({"success":"Update successfull","profile": profile}))
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in update applied job at line number',lNumber,'error is:',e)

#DELETE
@jobs_main_bp.route('/applyJob/<id>', methods = ['DELETE'])
def deleteApplyJob(id):
    get_jobs = AppliedJobs.query.get(id)
    if get_jobs == None:
        return make_response(jsonify({"error":"No such job exists"}),400)
    db.session.delete(get_jobs)
    db.session.commit()
    return make_response(jsonify({"success":"Delete successfull"}),200)


#READ Applications BY Job ID
@jobs_main_bp.route('/appliedJobs/<job_id>', methods = ['GET'])
def getJobAppliers(job_id):
    JobAppliers = []
    appliers_dict = {}
    appliedJobs = AppliedJobs.query.filter_by(job_id=job_id)
    if appliedJobs == None:
        return make_response(jsonify({"error":"No such job exists"}),400)
    for job in appliedJobs:
        appliers_dict['id'] = job.id
        appliers_dict['applier_id'] = job.applied_by
        appliers_dict['pay_expected'] = job.pay_expected
        appliers_dict['availability'] = str(job.monthly_available)
        member_id = job.applied_by
        user_instance = User.query.get(member_id)
        name = user_instance.name
        appliers_dict['name'] = name
        status = job.application_status
        if status == AppliedJobStatusEnum.pending:
            appliers_dict['application_status'] = 'pending'
        if status == AppliedJobStatusEnum.approved:
            appliers_dict['application_status'] = 'approved'
        if status == AppliedJobStatusEnum.rejected:
            appliers_dict['application_status'] = 'rejected'
        if status == AppliedJobStatusEnum.interested:
            appliers_dict['application_status'] = 'interested'
        try:
            user_profile = Profile.query.filter_by(user_id=job.applied_by)
            for profile in user_profile:
                try:
                    appliers_dict['profile_pic'] = profile.profile_pic
                except Exception as e:
                    appliers_dict['profile_pic'] = ''
        except Exception as e:
            appliers_dict['profile_pic'] = ''
        reviews_instance = Reviews.query.filter_by(given_to=member_id).first()
        try:
            rating = int(reviews_instance.stars)
        except Exception as e:
            rating = 5
        appliers_dict['rating'] = rating 
        appliers_dict['message'] = job.message
        appliers_dict['created_at'] = job.created_at
        appliers_dict['job_id'] = job.job_id
        JobAppliers.append(appliers_dict.copy())
    return make_response(jsonify({"JobAppliers": JobAppliers}))


#READ By Applier ID
@jobs_main_bp.route('/applierJobs/<applier_id>', methods = ['GET'])
def getApplierJobs(applier_id):
    jobs_list = []
    job_dict = {}
    # user_profile_instance = Profile.query.filter_by(enquirer_id=current_user).first()
    # company_name = user_profile_instance.company_name
    applied_jobs_exist = bool(AppliedJobs.query.filter_by(applied_by=applier_id).first())
    if not applied_jobs_exist:
        return make_response(jsonify({'message':"No jobs applied yet"}),200)
    applied_jobs = AppliedJobs.query.filter_by(applied_by=applier_id)
    for application in applied_jobs:
        if application.is_active == True: 
            status = 'active'
        else:
            status = 'in progress'
        job_id = application.job_id
        print('job_id',job_id)
        job = Jobs.query.get(job_id) 
        job_dict['id'] = job.id
        job_dict['job_title'] = job.job_title
        job_dict['job_category'] = job.job_category
        job_dict['job_type'] = job.job_type
        job_dict['budget'] = job.budget 
        job_dict['job_description'] = job.job_description
        job_dict['location'] = job.location
        job_dict['city'] = job.city
        job_dict['created_at'] = job.created_at
        job_dict['updated_at'] = job.updated_at
        job_dict['posted_by'] = job.posted_by
        job_dict['bidding_started'] = job.bidding_started
        # job_dict['company_name'] = company_name
        job_dict['shift_start_date'] = job.shift_start_date
        job_dict['shift_end_date'] = job.shift_end_date
        job_dict['shift_start_time'] = job.shift_start_time
        job_dict['shift_end_time'] = job.shift_end_time
        start_date = job.shift_start_date
        today_date = date.today()
        delta = start_date - today_date
        days_remaining = delta.days
        job_dict['remaining_days'] = days_remaining
        enquirer_profile_instance = EnquirerProfile.query.filter_by(enquirer_id=job.posted_by).first()
        try:
            company_name = enquirer_profile_instance.company_name
        except Exception as e:
            company_name = ''
        job_dict['company_name'] = company_name
        jobs_list.append(job_dict.copy())
    jobs_list.sort(key=lambda item:item['shift_start_date'], reverse=True)
    return make_response(jsonify({'jobs_details':jobs_list}),200)

#Fund For Job Application by Wallet
@jobs_main_bp.route("/walletJobFunding/", methods=['POST'])
@jwt_required
def addMoneyToAccountWallet():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer"}),400)
        post_data = request.form
        application_id = post_data['application_id']
        total_pay = post_data['total_pay']
        if '£' in total_pay:
            total_pay = total_pay.replace('£','')
        net_payable = post_data['net_payable']
        if '£' in net_payable:
            net_payable = net_payable.replace('£','')
        admin_charges = post_data['admin_charges']
        if '£' in admin_charges:
            admin_charges = admin_charges.replace('£','')
        bidding_fees = post_data['bidding_fees']
        if '£' in bidding_fees:
            bidding_fees = bidding_fees.replace('£','')
        vat = post_data['AOS_Account_Refund']
        if '£' in vat:
            vat = vat.replace('£','')
        misc_payment = post_data['AOS_One_Off_Misc_Payment']
        if '£' in misc_payment:
            misc_payment = misc_payment.replace('£','')
        standard_addition = post_data['AOS_Standard_Addition_Per_Hour']
        if '£' in standard_addition:
            standard_addition = standard_addition.replace('£','')
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
        job_title = job_profile_data.job_title
        if application_instance.application_status == AppliedJobStatusEnum.approved:        
            return make_response(jsonify({"error":"Already Approved"}),400)
        ###############Check Wallet######################
        wallet_exists = bool(Wallet.query.filter_by(user_id=current_user).first())
        if wallet_exists:
            wallet = Wallet.query.filter_by(user_id=current_user).first()
            balance = wallet.balance
            print('balance',balance,'net_payable',net_payable)
            if float(balance) < float(net_payable):
                return make_response(jsonify({"error": "Insufficient Funds. Kindly fund the wallet"}),400)
        else:
            return make_response(jsonify({"error": "Insufficient Funds. Kindly fund the wallet"}),400)
        # funding_instance = UserPayments(
        #     reference = 'Wallet Funding For Job',
        #     medium = 'wallet',
        #     amount = total_pay,
        #     user_id = current_user
        # )
        # try:
        #     local_object = db.session.merge(funding_instance)
        #     db.session.add(local_object)
        # except Exception as e:
        #     print('error in commit',e)
        #     db.session.add(funding_instance)
        ##############################################Save to openarc db####################################
        admin_payment = float(admin_charges)+float(bidding_fees)+float(vat)+float(misc_payment)+float(standard_addition)
        print('admin_payment',admin_payment)
        application_instance.is_funded = True
        application_instance.total_payment = total_pay
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
            message_body = 'An application has been approved for job titled'+job_title
            send_notification(member_device_id, message_title, message_body)
            subject = "Job Application Approval-OpenArc"
            to = [member_email,employer_email]
            for address in to:
                if address == member_email:
                    agree_link = ''
                else:
                    agree_link = ''
                body = 'Hello '+address+',\nYour application has been approved for job titled\n'
                try:
                    send_email(address, subject, job_title, agree_link, 'approved')
                except Exception as e:
                    print('error sending email',e)
            return make_response(jsonify({"message":"Application Approved","status":"success","payment_object": charge}),200)
        except Exception as e:
            print('error in sending email',e)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('line',lNumber,'error',e)
        return make_response(jsonify({"error in payment":str(e)}),400)