"""Logged-in page routes."""
from flask import Blueprint, request, jsonify, make_response, render_template_string
from flask_login import current_user, login_required, logout_user
from flask import Response
from .models import db,EnquirerProfile, EnquirerProfileSchema, Fundings, Wallet, WalletSchema, UserPayments, UserPaymentsSchema
import shutil 
from os import environ, path
from dotenv import load_dotenv
import sys, os
from flask_jwt_extended import jwt_required , get_jwt_identity
from services.Users.Member.models import *
import base64, re
from services.Subscriptions.models import *
from services.Jobs.models import *
from services.Users.Member.models import *

from geopy.geocoders import Nominatim
from datetime import datetime
import stripe
import time
import ast
from werkzeug.utils import secure_filename

basedir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', '..'))
load_dotenv(path.join(basedir, '.env'))

# Blueprint Configuration
enq_main_bp = Blueprint(
    'enq_main_bp', __name__,
)
# destination_uploads = environ.get('ENQUIRER_UPLOADS')
stripe_uploads = environ.get('STRIPE_UPLOAD')
destination_uploads = environ.get('ENQUIRER_UPLOADS')
stripe.api_key = environ.get('STRIPE_SECRET_KEY')
enquirer_uploads = environ.get('ENQUIRER_UPLOADS')
# employer_url_local='/var/www/Projects/OpenArc/Push/openarc-flask/media/uploads/employer/'

@enq_main_bp.route('/checkout/', methods=['GET'])
def checkout():
    try:
        status = request.args.get('sc_checkout')
        if status == 'success':
            session = stripe.checkout.Session.retrieve(request.args.get('sc_sid'))
            print('session',session)
            customer_email = session['customer_email']
            user_instance = User.query.filter_by(email=customer_email).first()
            user_payment = UserPayments(
                amount = session['amount_subtotal'],
                session_id = session['id'],
                medium = 'card',
                reference = 'subscription',
                user_id = user_instance.id,
                )
            db.session.add(user_payment)
            db.session.commit()
            # customer = stripe.Customer.retrieve(session.customer_email)
            return render_template_string('<html><body><h1>Thanks for your purchase, {{customer_email}}!</h1></body></html>',customer_email=customer_email)
        elif status == 'cancel':
            return render_template_string('<html><body><h1>Purchase Cancelled!</h1></body></html>')
        else:
            return render_template_string('<html><body><h1>Error Occured!</h1></body></html>')
    except Exception as e:
        print('error in session',e)
        return render_template_string('<html><body><h1>Error Occured!,{{ e }}</h1></body></html>',e=e)


# @enq_main_bp.route('/cancel/<session_id>/', methods=['GET'])
# def order_cancel(session_id):
#   # session = stripe.checkout.Session.retrieve(request.args.get('session_id'))
#   session = stripe.checkout.Session.retrieve(session_id)
#   customer_email = session['customer_email']
#   # customer = stripe.Customer.retrieve(session.customer)

  # return render_template_string('<html><body><h1>Order Cancelled, {{customer_email}}!</h1></body></html>')

#######Explore Members####################
@enq_main_bp.route("/exploreMembers/", methods=['GET'])
@jwt_required
def exploreMembers():
    """Explore Members"""
    try:
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
                    profile_pic = profile_instance.profile_pic
                else:
                    per_hour_rate = '£0'
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
                    avg = 2
                saved = bool(SavedMembers.query.filter_by(member_id=member_id).filter_by(saved_by=current_user.id).first())
                member_dict['saved'] = saved
                member_dict['member_name'] = member.name
                member_dict['rating'] = avg
                member_dict['per_hour_rate'] = per_hour_rate
                member_dict['city'] = city
                member_dict['profile_pic'] = profile_pic
                members_list.append(member_dict.copy())
        ###High Rated
        high_rated_list = sorted(members_list, key = lambda i: i['rating'],reverse=True)
        return make_response(jsonify({"all_members":members_list,"high_rated":high_rated_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in explore members at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#######City Filter Members####################
@enq_main_bp.route("/cityFilter/", methods=['POST'])
@jwt_required
def cityFilter():
    """City Filter Members"""
    try:
        member_dict = {}
        members_list = []
        post_data = request.get_json()
        city = post_data['city']
        try:
            city_list = city.split(',')
        except Exception as e:
            city_list = list(city)
        print('city_list>>>>>>>>>>>>>',city_list)
        for city in city_list:
            profile_exists = bool(Profile.query.filter_by(city=city).first())
            if profile_exists:
                profile_instances = Profile.query.filter_by(city=city)
                for profile in profile_instances:
                    print('profiles',profile.id)
                    per_hour_rate = profile.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate
                    else:
                        per_hour_rate = '£'+str(per_hour_rate)
                    city = profile.city
                    profile_pic = profile.profile_pic
                    member_id = profile.user_id
                    member_instance = User.query.get(member_id)
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
                        avg = 2
                    saved = bool(SavedMembers.query.filter_by(member_id=member_id).filter_by(saved_by=current_user.id).first())
                    member_dict['saved'] = saved
                    member_dict['member_name'] = member_instance.name
                    member_dict['rating'] = avg
                    member_dict['per_hour_rate'] = per_hour_rate
                    member_dict['city'] = city
                    member_dict['profile_pic'] = profile_pic
                    members_list.append(member_dict.copy())
        ###High Rated
        high_rated_list = sorted(members_list, key = lambda i: i['rating'],reverse=True)
        return make_response(jsonify({"all_members":members_list,"high_rated":high_rated_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in filter city members at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#######Rating Filter Members####################
@enq_main_bp.route("/ratingFilter/", methods=['POST'])
@jwt_required
def ratingFilter():
    """ratingFilter"""
    try:
        member_dict = {}
        members_list = []
        member_id_list = []
        high_rated_list = []
        post_data = request.get_json()
        rating = post_data.get('rating',None)
        hourly_rate = post_data.get('hourly_rate',None)
        print(rating,hourly_rate)
        if not rating and not hourly_rate:
            return make_response(jsonify({"error": 'atleast one filter value is required'}),400)

        if not rating and hourly_rate:
            members_id_list = []
            #less than 10
            if hourly_rate == 'Less than £10':
                profiles = Profile.query.all()
                for profile in profiles:
                    per_hour_rate = profile.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate.replace('£','')
                    else:
                        per_hour_rate = per_hour_rate
                    if int(per_hour_rate) < 10:
                        members_id_list.append(profile.user_id)

            #£10-£20
            if hourly_rate == '£10-£20':
                profiles = Profile.query.all()
                for profile in profiles:
                    per_hour_rate = profile.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate.replace('£','')
                    else:
                        per_hour_rate = per_hour_rate
                    if (int(per_hour_rate) >= 10) and (int(per_hour_rate) <= 20) :
                        members_id_list.append(profile.user_id)

            #£20-£30
            if hourly_rate == '£20-£30':
                profiles = Profile.query.all()
                for profile in profiles:
                    per_hour_rate = profile.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate.replace('£','')
                    else:
                        per_hour_rate = per_hour_rate
                    if (int(per_hour_rate) > 20) and (int(per_hour_rate) <= 30) :
                        members_id_list.append(profile.user_id)

            #More than £30
            if hourly_rate == 'More than £30':
                profiles = Profile.query.all()
                for profile in profiles:
                    per_hour_rate = profile.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate.replace('£','')
                    else:
                        per_hour_rate = per_hour_rate
                    if (int(per_hour_rate) > 30):
                        members_id_list.append(profile.user_id)
            for member_id in members_id_list:
                member_instance = User.query.get(member_id)
                stars_list = []
                review_exists = bool(Reviews.query.filter_by(member_id=member_id).first())
                if review_exists:
                    member_reviews = Reviews.query.filter_by(member_id=member_id)
                    for r in member_reviews:
                        print('rrr',r,'member_id',member_id)
                        stars = r.employer_stars
                        stars_list.append(int(stars))
                        total = sum(stars_list)
                        count = len(stars_list)
                        avg = total/count
                else:
                    avg = 4
                profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                if profile_exists:
                    profile_instance = Profile.query.filter_by(user_id=member_id).first()
                    per_hour_rate = profile_instance.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate
                    else:
                        per_hour_rate = '£'+str(per_hour_rate)
                    city = profile_instance.city
                    profile_pic = profile_instance.profile_pic
                else:
                    per_hour_rate = '£0'
                    city = ''
                    profile_pic = ''
                saved = bool(SavedMembers.query.filter_by(member_id=member_id).filter_by(saved_by=current_user.id).first())
                member_dict['saved'] = saved
                member_dict['member_id'] = member_id
                member_dict['member_name'] = member_instance.name
                member_dict['rating'] = avg
                member_dict['per_hour_rate'] = per_hour_rate
                member_dict['city'] = city
                member_dict['profile_pic'] = profile_pic
                if member_id in member_id_list:
                    pass
                else:
                    members_list.append(member_dict.copy())
                member_id_list.append(member_id)

        if not hourly_rate and rating:
            reviews = Reviews.query.all()
            if reviews:
                for review in reviews:
                    stars_list = []
                    member_id = review.member_id
                    print('member_id',member_id)
                    member_instance = User.query.get(member_id)
                    member_stars_exists = bool(Reviews.query.filter_by(member_id=member_id).first())
                    if member_stars_exists:
                        member_reviews = Reviews.query.filter_by(member_id=member_id)
                        for r in member_reviews:
                            stars = r.employer_stars
                            stars_list.append(int(stars))
                            total = sum(stars_list)
                            count = len(stars_list)
                            avg = total/count
                            print('avg',avg)
                            if float(avg) == float(rating):
                                profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                                if profile_exists:
                                    profile_instance = Profile.query.filter_by(user_id=member_id).first()
                                    per_hour_rate = profile_instance.hourly_rate
                                    if '£' in per_hour_rate:
                                        per_hour_rate = per_hour_rate
                                    else:
                                        per_hour_rate = '£'+str(per_hour_rate)
                                    city = profile_instance.city
                                    profile_pic = profile_instance.profile_pic
                                else:
                                    per_hour_rate = '£0'
                                    city = ''
                                    profile_pic = ''
                                saved = bool(SavedMembers.query.filter_by(member_id=member_id).filter_by(saved_by=current_user.id).first())
                                member_dict['saved'] = saved
                                member_dict['member_id'] = member_id
                                member_dict['member_name'] = member_instance.name
                                member_dict['rating'] = avg
                                member_dict['per_hour_rate'] = per_hour_rate
                                member_dict['city'] = city
                                member_dict['profile_pic'] = profile_pic
                                if member_id in member_id_list:
                                    pass
                                else:
                                    members_list.append(member_dict.copy())
                                member_id_list.append(member_id)
        if hourly_rate and rating:
            members_id_list = []
            #less than 10
            if hourly_rate == 'Less than £10':
                profiles = Profile.query.all()
                for profile in profiles:
                    per_hour_rate = profile.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate.replace('£','')
                    else:
                        per_hour_rate = per_hour_rate
                    if int(per_hour_rate) < 10:
                        members_id_list.append(profile.user_id)

            #£10-£20
            if hourly_rate == '£10-£20':
                profiles = Profile.query.all()
                for profile in profiles:
                    per_hour_rate = profile.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate.replace('£','')
                    else:
                        per_hour_rate = per_hour_rate
                    if (int(per_hour_rate) >= 10) and (int(per_hour_rate) <= 20) :
                        members_id_list.append(profile.user_id)

            #£20-£30
            if hourly_rate == '£20-£30':
                profiles = Profile.query.all()
                for profile in profiles:
                    per_hour_rate = profile.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate.replace('£','')
                    else:
                        per_hour_rate = per_hour_rate
                    if (int(per_hour_rate) > 20) and (int(per_hour_rate) <= 30) :
                        members_id_list.append(profile.user_id)

            #More than £30
            if hourly_rate == 'More than £30':
                profiles = Profile.query.all()
                for profile in profiles:
                    per_hour_rate = profile.hourly_rate
                    if '£' in per_hour_rate:
                        per_hour_rate = per_hour_rate.replace('£','')
                    else:
                        per_hour_rate = per_hour_rate
                    if (int(per_hour_rate) > 30):
                        members_id_list.append(profile.user_id)
            if len(members_id_list)>0:
                reviews = Reviews.query.filter(Reviews.member_id.in_(members_id_list)).all()
                if reviews:
                    for review in reviews:
                        stars_list = []
                        member_id = review.member_id
                        member_instance = User.query.get(member_id)
                        member_stars_exists = bool(Reviews.query.filter_by(member_id=member_id).first())
                        if member_stars_exists:
                            member_reviews = Reviews.query.filter_by(member_id=member_id)
                            for r in member_reviews:
                                stars = r.employer_stars
                                stars_list.append(int(stars))
                                total = sum(stars_list)
                                count = len(stars_list)
                                avg = total/count
                                print('avg',avg)
                                if float(avg) == float(rating):
                                    profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                                    if profile_exists:
                                        profile_instance = Profile.query.filter_by(user_id=member_id).first()
                                        per_hour_rate = profile_instance.hourly_rate
                                        if '£' in per_hour_rate:
                                            per_hour_rate = per_hour_rate
                                        else:
                                            per_hour_rate = '£'+str(per_hour_rate)
                                        city = profile_instance.city
                                        profile_pic = profile_instance.profile_pic
                                    else:
                                        per_hour_rate = '£0'
                                        city = ''
                                        profile_pic = ''
                                    saved = bool(SavedMembers.query.filter_by(member_id=member_id).filter_by(saved_by=current_user.id).first())
                                    member_dict['saved'] = saved
                                    member_dict['member_id'] = member_id
                                    member_dict['member_name'] = member_instance.name
                                    member_dict['rating'] = avg
                                    member_dict['per_hour_rate'] = per_hour_rate
                                    member_dict['city'] = city
                                    member_dict['profile_pic'] = profile_pic
                                    if member_id in member_id_list:
                                        pass
                                    else:
                                        members_list.append(member_dict.copy())
                                    member_id_list.append(member_id)

        ###High Rated
        high_rated_list = sorted(members_list, key = lambda i: i['rating'],reverse=True)
        return make_response(jsonify({"all_members":members_list,"high_rated":high_rated_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in rating filter at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#######Hourly Rate Filter Members####################
@enq_main_bp.route("/hourlyRateFilter/", methods=['POST'])
@jwt_required
def hourlyRateFilter():
    """hourlyRateFilter"""
    try:
        less_than_10_member_dict = {}
        less_than_10_members_list = []
        greater_than_30_member_dict = {}
        greater_than_30_members_list = []
        between_20_30_member_dict = {}
        between_20_30_members_list = []
        between_10_20_member_dict = {}
        between_10_20_members_list = []
        # post_data = request.get_json()
        # hourly_rate_string = post_data['hourly_rate']
        # profiles_exists = bool(Profile.query.filter_by(id=1).first())
        # if profiles_exists:
        profiles = Profile.query.all()
        for profile in profiles:
            per_hour_rate = profile.hourly_rate
            if '£' in per_hour_rate:
                per_hour_rate = per_hour_rate.replace('£','')
            else:
                per_hour_rate = per_hour_rate
            city = profile.city
            profile_pic = profile.profile_pic
            member_id = profile.user_id
            member_instance = User.query.get(member_id)
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
                avg = 2
            saved = bool(SavedMembers.query.filter_by(member_id=member_id).filter_by(saved_by=current_user.id).first())
            if int(per_hour_rate) < 10:
                less_than_10_member_dict['saved'] = saved
                less_than_10_member_dict['member_name'] = member_instance.name
                less_than_10_member_dict['rating'] = avg
                less_than_10_member_dict['per_hour_rate'] = '£'+str(per_hour_rate)
                less_than_10_member_dict['city'] = city
                less_than_10_member_dict['profile_pic'] = profile_pic
                less_than_10_members_list.append(less_than_10_member_dict.copy())
            if (int(per_hour_rate) < 20) and (int(per_hour_rate) >= 10):
                between_10_20_member_dict['saved'] = saved
                between_10_20_member_dict['member_name'] = member_instance.name
                between_10_20_member_dict['rating'] = avg
                between_10_20_member_dict['per_hour_rate'] = '£'+str(per_hour_rate)
                between_10_20_member_dict['city'] = city
                between_10_20_member_dict['profile_pic'] = profile_pic
                between_10_20_members_list.append(between_10_20_member_dict.copy())
            if (int(per_hour_rate) >= 20) and (int(per_hour_rate) <= 30):
                between_20_30_member_dict['saved'] = saved
                between_20_30_member_dict['member_name'] = member_instance.name
                between_20_30_member_dict['rating'] = avg
                between_20_30_member_dict['per_hour_rate'] = '£'+str(per_hour_rate)
                between_20_30_member_dict['city'] = city
                between_20_30_member_dict['profile_pic'] = profile_pic
                between_20_30_members_list.append(between_20_30_member_dict.copy())
            if (int(per_hour_rate) > 30):
                greater_than_30_member_dict['saved'] = saved
                greater_than_30_member_dict['member_name'] = member_instance.name
                greater_than_30_member_dict['rating'] = avg
                greater_than_30_member_dict['per_hour_rate'] = '£'+str(per_hour_rate)
                greater_than_30_member_dict['city'] = city
                greater_than_30_member_dict['profile_pic'] = profile_pic
                greater_than_30_members_list.append(greater_than_30_member_dict.copy())
            # ###High Rated
            # high_rated_list = sorted(members_list, key = lambda i: i['rating'],reverse=True)
        return make_response(jsonify({"less_than_10_members_list":less_than_10_members_list,
            'greater_than_30_members_list':greater_than_30_members_list,
            'between_20_30_members_list':between_20_30_members_list,
            'between_10_20_members_list':between_10_20_members_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in filter hourly rate members at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#######Job Listings ####################
@enq_main_bp.route("/jobListings/", methods=['GET'])
@jwt_required
def jobListings():
    """job Listings"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        posted_projects = []
        user_instance = User.query.get(current_user)
        posted_projects_dict = {}
        posted_jobs_exist = bool(Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=False).first())
        if posted_jobs_exist:
            posted_jobs = Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=False)
            for job_instance in posted_jobs:
                job_id = job_instance.id
                start_date = job_instance.shift_start_date
                today_date = date.today()
                delta = start_date - today_date
                days_remaining = delta.days
                if days_remaining > 0:
                    business_name = job_instance.business_name
                    budget = job_instance.budget
                    applications_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).first())
                    applicants_array_list = []
                    applicant_dict = {}
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
                            profile_exists = bool(Profile.query.filter_by(user_id=applicant_id).first())
                            if profile_exists:
                                profile_instance = Profile.query.filter_by(user_id=applicant_id).first()
                                profile_pic = profile_instance.profile_pic
                            else:
                                profile_pic = ''
                            applicant_dict['name'] = applicant_name
                            applicant_dict['profile_pic'] = profile_pic
                            applicants_array_list.append(applicant_dict.copy())
                            posted_projects_dict['applicants_array'] = applicants_array_list
                            if applications_count > 1:
                                applicants = applicant_name + ' + ' + str(applicants_count) + ' members applied'
                            else:
                                applicants = applicant_name + ' has applied'
                    else:
                        applicants = 0
                    # applicants = job_instance.interested_count
                    city = job_instance.city 
                    posted_projects_dict['job_id'] = job_id
                    posted_projects_dict['business_name'] = business_name
                    posted_projects_dict['days_remaining'] = days_remaining
                    posted_projects_dict['company_name'] = user_instance.name
                    posted_projects_dict['applicants'] = applicants
                    posted_projects_dict['city'] = city
                    posted_projects_dict['budget'] = budget
                    posted_projects.append(posted_projects_dict.copy())
        else:
            posted_projects = []
        return make_response(jsonify({"posted_projects":posted_projects}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in job Listings at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)



#######Save Members####################
@enq_main_bp.route("/saveMember/", methods=['POST'])
@jwt_required
def saveMember():
    """saveMember"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        post_data = request.get_json()
        member_id = post_data['member_id']
        saved_profile = SavedMembers(
                member_id = member_id,
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
        print('Error occurs in save member at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#######Posted Job Details ############################################
@enq_main_bp.route("/postedJobDetails/<job_id>", methods=['GET'])
@jwt_required
def postedJobDetails(job_id):
    """job Details"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        job_details = []
        applicants_list = []
        applicant_dict = {}
        user_instance = User.query.get(current_user)
        job_dict = {}
        job_instance = Jobs.query.get(job_id)
        start_date = job_instance.shift_start_date
        today_date = date.today()
        delta = start_date - today_date
        days_remaining = delta.days
        business_name = job_instance.business_name
        budget = job_instance.budget
        applications_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).first())
        if applications_exists:
            applications = AppliedJobs.query.filter_by(job_id=job_id)
            for application in applications:
                applicant_id = application.applied_by
                reviews_exist = bool(Reviews.query.filter_by(member_id=applicant_id).first())
                stars_list = []
                if reviews_exist:
                    reviews = Reviews.query.filter_by(member_id=applicant_id)
                    for review in reviews:
                        stars = review.employer_stars
                        stars_list.append(int(stars))
                        total = sum(stars_list)
                        count = len(stars_list)
                        avg = total/count
                else:
                    avg = 2
                applicant_instance = User.query.get(applicant_id)
                applicant_name = applicant_instance.name
                profile_exists = bool(Profile.query.filter_by(user_id=applicant_id).first())
                if profile_exists:
                    profile_instance = Profile.query.filter_by(user_id=applicant_id).first()
                    profile_pic = profile_instance.profile_pic
                    hourly_rate = '£'+profile_instance.hourly_rate
                else:
                    profile_pic = ''
                    hourly_rate = '£0'
                applicant_dict['application_id'] = application.id
                applicant_dict['rating'] = avg
                applicant_dict['member_id'] = applicant_id
                applicant_dict['hourly_rate'] = hourly_rate
                applicant_dict['profile_pic'] = profile_pic
                applicant_dict['applicant_name'] = applicant_name
                applicants_list.append(applicant_dict.copy())
        else:
            applicants = applicants_list
        city = job_instance.city 
        job_dict['job_id'] = job_id
        job_dict['business_name'] = business_name
        job_dict['days_remaining'] = days_remaining
        job_dict['company_name'] = user_instance.name
        job_dict['city'] = city
        job_dict['budget'] = budget
        job_dict['job_type'] = job_instance.job_type
        job_dict['job_description'] = job_instance.job_description
        job_dict['shift_start_date'] = job_instance.shift_start_date
        job_dict['shift_end_date'] = job_instance.shift_end_date
        job_dict['shift_start_time'] = job_instance.shift_start_time
        job_dict['shift_end_time'] = job_instance.shift_end_time
        job_details.append(job_dict.copy())
        return make_response(jsonify({"job_details":job_details,'applicants':applicants_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in job Listings at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#######Application Details ############################################
@enq_main_bp.route("/applicationDetails/<application_id>", methods=['GET'])
@jwt_required
def applicationDetails(application_id):
    """Application Details"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        application_details = []
        details_dict = {}
        application_instance = AppliedJobs.query.get(application_id)
        details_dict['application_id'] = application_instance.id
        details_dict['offer_rate'] = application_instance.pay_expected
        details_dict['message'] = application_instance.message
        application_details.append(details_dict)
        return make_response(jsonify({"application_details":application_details}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in application details at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#######View Member Profile ############################################
@enq_main_bp.route("/viewProfile/<member_id>", methods=['GET'])
@jwt_required
def viewProfile(member_id):
    """View Memebr Profile"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        #Member Detials
        profile_instance = bool(Profile.query.filter_by(user_id=member_id).first())
        user_instance = User.query.get(member_id)
        if not user_instance:
            return make_response(jsonify({"error": "No such member exists"}),400)
        name = user_instance.name
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
            avg = 2
            # employer_name = ''
        if profile_instance:
            profile_data = Profile.query.filter_by(user_id=member_id)
            for profile in profile_data:
                profile_id = profile.id
                get_profile = Profile.query.get(profile_id)
                profile_schema = ProfileSchema(many=False)
                user_profile = profile_schema.dump(get_profile)
                user_profile['name'] = name
                user_profile['rating'] = avg
                user_profile['document_name'] = get_profile.documents
                user_profile['document_string'] = get_profile.documents
                user_profile['badge_number'] = user_instance.badge_number
                unavailability = get_profile.unavailability
                print('unavailability',unavailability)
                if ((unavailability == '') or (unavailability == None)):
                    user_profile['unavailable_dates'] = []
                else:
                    user_profile['unavailable_dates'] = ast.literal_eval(get_profile.unavailability)
        else:
            user_profile={'id':'','name':'','document_name':'','profile_pic':'','about':'','contact':'','address':'',
            'city':'','hourly_rate':'','created_at':'','updated_at':'','availability_dates':'','postal_code':'',
            'drive':'','name':'','badge_number':''}
        #Reviews
        reviews_list = []
        review_dict = {}
        reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).first())
        if reviews_exist:
            reviews = Reviews.query.filter_by(member_id=member_id)
            for review in reviews:
                employer_id = review.employer_id
                employer_instance = User.query.get(employer_id)
                employer_name = employer_instance.name
                stars = review.employer_stars
                employer_id = review.employer_id
                profile_instance_exists = bool(EnquirerProfile.query.filter_by(enquirer_id=employer_id).first())
                if profile_instance_exists:
                    employer_profile = EnquirerProfile.query.filter_by(enquirer_id=employer_id).first()
                    employer_profile_pic = employer_profile.company_logo
                else:
                    employer_profile_pic = ''
                text = review.employer_review
                review_dict['id'] = review.id
                review_dict['employer'] = employer_name
                review_dict['text'] = text
                review_dict['rating'] = stars
                review_dict['profile_pic'] = employer_profile_pic
                reviews_list.append(review_dict.copy())
        return make_response(jsonify({"profile": user_profile,'reviews':reviews_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in view profile at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#######Drafts and Saved Members############################################
@enq_main_bp.route("/savedDetails/", methods=['GET'])
@jwt_required
def savedDetails():
    """Drafts and Saved Members"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        drafts_list = []
        saved_members_list = []
        draft_dict = {}
        members_dict = {}
        #Drafts
        drafts_exists = bool(Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=True).first())
        if drafts_exists:
            drafts = Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=True)
            for draft in drafts:
                start_date = draft.shift_start_date
                today_date = date.today()
                delta = start_date - today_date
                days_remaining = delta.days
                draft_dict['job_id'] = draft.id
                draft_dict['business_name'] = draft.business_name
                draft_dict['days_remaining'] = days_remaining
                draft_dict['company_name'] = user_instance.name
                draft_dict['city'] = draft.city
                draft_dict['budget'] = draft.budget
                draft_dict['job_type'] = draft.job_type
                draft_dict['job_description'] = draft.job_description
                draft_dict['shift_start_date'] = draft.shift_start_date
                draft_dict['shift_end_date'] = draft.shift_end_date
                draft_dict['shift_start_time'] = draft.shift_start_time
                draft_dict['shift_end_time'] = draft.shift_end_time
                drafts_list.append(draft_dict.copy())
        #Saved Memebrs
        saved_exists = bool(SavedMembers.query.filter_by(saved_by=current_user).first())
        if saved_exists:
            saved_members = SavedMembers.query.filter_by(saved_by=current_user)
            for member in saved_members:
                member_id = member.member_id
                save_instance_id = member.id
                member_instance = User.query.get(member_id)
                member_name = member_instance.name
                profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                if profile_exists:
                    profile_instance = Profile.query.filter_by(user_id=member_id).first()
                    profile_pic = profile_instance.profile_pic
                    hourly_rate = '£'+profile_instance.hourly_rate
                else:
                    profile_pic = ''
                    hourly_rate = '£0'
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
                    avg = 2
                members_dict['member_id'] = member_id
                members_dict['save_instance_id'] = save_instance_id
                members_dict['member_name'] = member_name
                members_dict['profile_pic'] = profile_pic
                members_dict['rating'] = avg
                saved_members_list.append(members_dict.copy())
        return make_response(jsonify({"drafts":drafts_list,"saved_members":saved_members_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in saved details at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


###########Delete Saved Member###########
@enq_main_bp.route('/removeSavedMember/<saved_instance_id>', methods = ['DELETE'])
@jwt_required
def removeSavedMember(saved_instance_id):
    current_user = get_jwt_identity()
    user_instance = User.query.get(current_user)
    if user_instance.user_type == 'enquirer':
        pass
    else:
        return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
    saved_members_list = []
    members_dict = {}
    get_profile = SavedMembers.query.get(saved_instance_id)
    if get_profile == None:
        return make_response(jsonify({"error": "No such profile exists"}),400)
    db.session.delete(get_profile)
    db.session.commit()
    ###Get Saved Members
    saved_exists = bool(SavedMembers.query.filter_by(saved_by=current_user).first())
    if saved_exists:
        saved_members = SavedMembers.query.filter_by(saved_by=current_user)
        for member in saved_members:
            member_id = member.member_id
            save_instance_id = member.id
            member_instance = User.query.get(member_id)
            member_name = member_instance.name
            profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
            if profile_exists:
                profile_instance = Profile.query.filter_by(user_id=member_id).first()
                profile_pic = profile_instance.profile_pic
                hourly_rate = '£'+profile_instance.hourly_rate
            else:
                profile_pic = ''
                hourly_rate = '£0'
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
                avg = 2
            members_dict['member_id'] = member_id
            members_dict['save_instance_id'] = save_instance_id
            members_dict['member_name'] = member_name
            members_dict['profile_pic'] = profile_pic
            members_dict['rating'] = avg
            saved_members_list.append(members_dict.copy())
    return make_response(jsonify({"success":"Member Removed successfully",'saved_members':saved_members_list}),200)


###################################################CARD CRUD#####################################

#Get User Cards
@enq_main_bp.route("/cards/", methods=['GET'])
@jwt_required
def getCards():
    """Get Card"""
    try:
        current_user = get_jwt_identity()
        cards_list = []
        card_dict = {}
        try:
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
            return make_response(jsonify({"cards": cards_list}),200)
        except Exception as e:
            card_list = []
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting cards at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":"Error getting a card"}),400)


#Cards
@enq_main_bp.route("/card/", methods=['POST'])
@jwt_required
def createCard():
    """Add Card"""
    try:
        current_user = get_jwt_identity()
        post_data = request.get_json()
        card_number = post_data['card_number']
        name_on_card = post_data['name_on_card']
        expiry_date = post_data['expiry_date']
        card_type = post_data['card_type']
        cvv = post_data['cvv'] 
        if ((card_number == '') or (name_on_card == '') or (expiry_date == '')
            or (card_type == '')):
            return make_response(jsonify({"error":"All fields are required"}),400)
        try:
            existing_card = Cards.query.filter_by(card_number=card_number)
            for card in existing_card:
                card_id = card.id
                if card_id:
                    return make_response(jsonify({"error":"Card already exists"}),400)
        except Exception as e:
            pass
        card_instance = Cards(
                card_number = card_number,
                name_on_card = name_on_card,
                expiry_date = expiry_date,
                card_type = card_type,
                user = current_user,
                cvv = cvv
            )
        db.session.add(card_instance)
        db.session.commit()  # Create Card
        existing_card = Cards.query.filter_by(card_number=card_number).first()  
        card_id = existing_card.id
        get_card = Cards.query.get(card_id)
        card_schema = CardsSchema(only=['id','cvv','card_number','name_on_card','expiry_date','created_at','updated_at'])
        card = card_schema.dump(get_card)
        return make_response(jsonify({"success":"Card added successfully", "card":card}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in creating card at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":"Error adding a card"}),400)

#Get Card details
@enq_main_bp.route("/card/<id>", methods=['GET'])
@jwt_required
def getCardDetails(id):
    """Get Card"""
    try:
        current_user = get_jwt_identity()
        cards_list = []
        card_dict = {}
        try:
            card = Cards.query.get(id)
            if card == None:
                print('in if')
                cards_list = []
            else:
                card_dict['card_number'] = card.card_number
                card_dict['name_on_card'] = card.name_on_card
                card_dict['expiry_date'] = card.expiry_date
                card_dict['cvv'] = card.cvv
                card_dict['card_'] = card.card_type
                card_dict['status'] = card.is_active
                cards_list.append(card_dict)
            return make_response(jsonify({"card": cards_list}),200)
        except Exception as e:
            card_list = []
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in getting card details at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":"Error getting a card details"}),400)


#Change Password
@enq_main_bp.route("/apiChangePassword/", methods=['POST'])
@jwt_required
def changePassword():
    """Change Password"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        post_data = request.get_json()
        old_password = post_data['old_password']
        new_password = post_data['new_password']
        confirm_password = post_data['confirm_password']
        if ((old_password == '') or (new_password == '') or (confirm_password == '')):
            return make_response(jsonify({"error":"All fields are required"}),400)
        if ((new_password != confirm_password)):
            return make_response(jsonify({"error":"Your new password and confirm password do not match"}),400)
        if ((old_password == new_password == confirm_password )):
            return make_response(jsonify({"error":"Can not set same password"}),400)
        if user_instance and user_instance.check_password(password=old_password):
            user_instance.set_password(new_password)
            db.session.add(user_instance)
            db.session.commit()  # Create Card
            return make_response(jsonify({"success":"Password changed successfully"}),200)
        else:
            return make_response(jsonify({"error":"old passsword is not correct"}),400)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in change Password at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error":"Error adding a card"}),400)


#######Active Projects ####################
@enq_main_bp.route("/activeProjects/", methods=['GET'])
@jwt_required
def activeProjects():
    """Get Active Projects"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        active_projects = []
        jobs_list = []
        user_instance = User.query.get(current_user)
        active_projects_dict = {}
        jobs_exist = bool(Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=False).first())
        if jobs_exist:
            active_jobs = Jobs.query.filter_by(posted_by=current_user).filter_by(is_draft=False)
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
                                applicants = applicant_name + ' has applied'
                            city = job_instance.city 
                            if app_job_id in jobs_list:
                                pass
                            else:
                                active_projects_dict['job_id'] = job_id
                                active_projects_dict['business_name'] = business_name
                                active_projects_dict['days_remaining'] = days_remaining
                                active_projects_dict['company_name'] = user_instance.name
                                active_projects_dict['applicants'] = applicants
                                active_projects_dict['city'] = city
                                active_projects_dict['budget'] = budget
                                jobs_list.append(app_job_id)
                                active_projects.append(active_projects_dict.copy())
        else:
            active_projects = []
        return make_response(jsonify({"active_projects":active_projects}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in active projects list at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#######Active Job Details ####################
@enq_main_bp.route("/activeJobDetails/<job_id>/", methods=['GET'])
@jwt_required
def activeJobDetails(job_id):
    """Active Job Details"""
    try:
        job_details = {}
        active_member_dict = {}
        active_members_list = []
        inactive_member_dict = {}
        inactive_members_list = []
        complete_member_dict = {}
        complete_members_list = []
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        user_instance = User.query.get(current_user)
        #Job Details
        job_instance = Jobs.query.get(job_id)
        shift_start_date = job_instance.shift_start_date
        shift_end_date = job_instance.shift_end_date
        shift_start_time = job_instance.shift_start_time
        business_name = job_instance.business_name
        job_type = job_instance.job_type
        job_description = job_instance.job_description
        job_details['id'] = job_id
        job_details['company_name'] = user_instance.name
        job_details['shift_start_date'] = shift_start_date
        job_details['shift_end_date'] = shift_end_date
        job_details['job_description'] = job_description
        job_details['job_type'] = job_type
        job_details['business_name'] = business_name

        #Hired Members
        hired_members_exists = bool(AppliedJobs.query.filter_by(job_id=job_id).filter_by(is_active=True).first())
        if hired_members_exists:
            job_applications =  AppliedJobs.query.filter_by(job_id=job_id).filter_by(is_active=True)
            for application in job_applications:
                application_id = application.id
                # member_details_dict['application_id'] = application_id
                today_date = date.today()
                member_id = application.applied_by
                member_instance = User.query.get(member_id)
                member_name = member_instance.name
                profile_instance_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                if profile_instance_exists:
                    profile_instance = Profile.query.filter_by(user_id=member_id).first()
                    profile_pic = profile_instance.profile_pic
                    city = profile_instance.city
                    print('city',city)
                    city_list = city.split(' ')
                    print('>>>>>>>>>>>>',city_list)
                    city_name = city_list[0]
                    print('city_name',city_name)
                    if city:
                        try:
                            geolocator = Nominatim(user_agent="openarc")
                            location = geolocator.geocode(city_name)
                            latitude = location.latitude
                            longitude = location.longitude
                        except Exception as e:
                            latitude = ''
                            longitude = ''
                    else:
                        latitude = ''
                        longitude = ''
                else:
                    profile_pic = ''
                    latitude = ''
                    longitude = '' 
                ###Job Log###
                print('application_id',application_id,'today_date',today_date)
                job_logs_exists = bool(StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).first())
                if job_logs_exists:
                    complete_log_exists = bool(StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).filter_by(member_status='inactive').first())
                    if complete_log_exists:
                        job_log = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).filter_by(member_status='inactive').first()
                        member_status = 'clocked_out'
                        start_time = str(job_log.start_time)
                        end_time = str(job_log.end_time)
                        total_hours = job_log.hours
                        complete_member_dict['clock_in'] = start_time
                        complete_member_dict['clock_out'] = end_time
                        complete_member_dict['total_hours'] = total_hours
                        #review_exists
                        review_exists = bool(Reviews.query.filter_by(application_id=application_id).first())
                        if review_exists:
                            review = Reviews.query.filter_by(application_id=application_id).first()
                            stars = review.employer_stars
                            review_text = review.employer_review
                            complete_member_dict['stars'] = stars
                            complete_member_dict['review_text'] = review_text
                        else:
                            if (shift_end_date == today_date):
                                complete_member_dict['ask_review'] = True
                        complete_member_dict['member_id'] = member_id
                        complete_member_dict['today_date'] = today_date
                        complete_member_dict['profile_pic'] = profile_pic
                        complete_member_dict['member_name'] = member_name
                        complete_member_dict['member_status'] = member_status
                        complete_member_dict['today_date'] = today_date
                        complete_member_dict['application_id'] = application_id
                        complete_members_list.append(complete_member_dict.copy())
                    else:
                        job_log = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).first()
                        member_status =  job_log.member_status
                        if member_status == 'active':
                            start_time = str(job_log.start_time)
                            active_member_dict['member_name'] = member_name
                            active_member_dict['latitude'] = latitude
                            active_member_dict['longitude'] = longitude
                            active_member_dict['city'] = city
                            active_member_dict['member_status'] = member_status
                            active_member_dict['clock_in'] = start_time
                            active_member_dict['profile_pic'] = profile_pic
                            active_member_dict['member_id'] = member_id
                            active_member_dict['application_id'] = application_id
                            active_member_dict['today_date'] = today_date
                            active_members_list.append(active_member_dict.copy())
                else:
                    member_status = 'about_to_start'
                    inactive_member_dict['application_id'] = application_id
                    inactive_member_dict['member_id'] = member_id
                    inactive_member_dict['today_date'] = today_date
                    inactive_member_dict['profile_pic'] = profile_pic
                    inactive_member_dict['member_name'] = member_name
                    inactive_member_dict['member_status'] = member_status
                    inactive_members_list.append(inactive_member_dict.copy())
        return make_response(jsonify({"job_details":job_details,"active_members":active_members_list,
            'inactive_members':inactive_members_list,
            'completed_members':complete_members_list}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in active job_details at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400) 

#CREATE
@enq_main_bp.route("/review/", methods=['POST'])
@jwt_required
def createReview():
    """Add  Review."""
    try:
        current_user = get_jwt_identity()
        post_data = request.get_json()
        stars = post_data['stars']
        text = post_data['review_text']
        given_to = post_data['member_id']
        application_id = post_data['application_id']
        application_data = AppliedJobs.query.get(application_id)
        # if application_data.is_completed == False:
        #     return make_response(jsonify({"error":"This job is not completed yet"}),200)
        review = Reviews(
                employer_stars = stars,
                employer_review = text,
                member_id = given_to,
                employer_id = current_user,
                application_id = application_id
            )
        db.session.add(review)
        db.session.commit()  # Create user review
        return make_response(jsonify({"success":"Review added successfully"}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in saving review at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)  

#######Active Member Details ####################
@enq_main_bp.route("/activeMemberDetails/<application_id>/", methods=['GET'])
@jwt_required
def activeMemberDetails(application_id):
    """Active Member Details """
    try:
        member_details = {}
        work_details = {}
        today_date = date.today()
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        user_instance = User.query.get(current_user)
        #Job Details
        application_instance = AppliedJobs.query.get(application_id)
        member_id = application_instance.applied_by
        per_hour_rate = application_instance.pay_expected
        #Hired Member
        member_instance = User.query.get(member_id)
        member_name = member_instance.name
        profile_instance_exists = bool(Profile.query.filter_by(user_id=member_id).first())
        if profile_instance_exists:
            profile_instance = Profile.query.filter_by(user_id=member_id).first()
            profile_pic = profile_instance.profile_pic
        else:
            profile_pic = '' 
        member_details['profile_pic'] = profile_pic
        member_details['member_name'] = member_name
        member_details['per_hour_rate'] = '£'+str(per_hour_rate)+'/hr'
        #Review
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
            avg = 4
        member_details['rating'] = avg
        ###Job Log###
        job_logs_exists = bool(StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).first())
        if job_logs_exists:
            job_log = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(date=today_date).first()
            member_status =  job_log.member_status
            start_time = str(job_log.start_time)
            end_time = str(job_log.end_time)
            total_hours = job_log.hours
            extra_hours = job_log.after_hours
        else:
            member_status = 'about_to_start'
            start_time = ''
            end_time = ''
            total_hours = ''
            extra_hours = ''
        work_details['today_date'] = today_date
        work_details['start_time'] = start_time
        work_details['end_time'] = end_time
        work_details['total_hours'] = total_hours
        work_details['extra_hours'] = extra_hours
        return make_response(jsonify({"member_details":member_details,"work_details":work_details}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in active Member Details at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#######Past Projects ####################
@enq_main_bp.route("/pastProjects/", methods=['GET'])
@jwt_required
def pastProjects():
    """Get Past Projects"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        past_projects = []
        jobs_list = []
        user_instance = User.query.get(current_user)
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
                    print('employer',employer,'current_user',current_user)
                    if employer == current_user:
                        business_name = job_instance.business_name 
                        city = job_instance.city
                        applications = AppliedJobs.query.filter_by(job_id=job_id)
                        amounts_list = []
                        for app_instance in applications:
                            app_id = app_instance.id
                            pay_instance = JobPayments.query.filter_by(application_id=app_id).first()
                            amount = pay_instance.total_amount
                            amounts_list.append(int(amount))
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
                        if job_id in jobs_list:
                            pass
                        else:
                            past_projects_dict['total_amount'] = '£'+str(total_amount)
                            past_projects_dict['job_id'] = job_id
                            past_projects_dict['business_name'] = business_name
                            past_projects_dict['company_name'] = user_instance.name
                            past_projects_dict['applicants'] = applicants
                            past_projects_dict['city'] = city
                            past_projects_dict['status'] = 'completed'
                            jobs_list.append(job_id)
                            past_projects.append(past_projects_dict.copy())
        else:
            past_projects = []
        return make_response(jsonify({"past_projects":past_projects}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in past projects list at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#######Past Projects ####################
@enq_main_bp.route("/pastProjectsDetails/<job_id>", methods=['GET'])
@jwt_required
def pastProjectsDetails(job_id):
    """Get Past Project Details"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        user_instance = User.query.get(current_user)
        job_dict = {}
        user_dict = {}
        users_list = []
        job_details = Jobs.query.get(job_id)
        business_name = job_details.business_name
        job_type = job_details.job_type
        shift_start_date = job_details.shift_start_date
        shift_end_date = job_details.shift_end_date
        company_name = user_instance.name
        job_dict['id'] = job_id
        job_dict['business_name'] = business_name
        job_dict['company_name'] = company_name
        job_dict['job_type'] = job_type
        job_dict['shift_start_date'] = shift_start_date
        job_dict['shift_end_date'] = shift_end_date
        #Applications
        applications = AppliedJobs.query.filter_by(job_id=job_id).filter_by(is_active=False).filter_by(application_status=AppliedJobStatusEnum.approved)
        hours_list = []
        amount_list = []
        for application in applications:
            application_id = application.id
            application_instance=AppliedJobs.query.get(application_id)
            per_hour_rate = '£'+str(application_instance.pay_expected)
            member_id = application.applied_by
            member_instance = User.query.get(member_id)
            member_name = member_instance.name
            profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
            if profile_exists:
                profile_instance = Profile.query.filter_by(user_id=member_id).first()
                profile_pic = profile_instance.profile_pic
            else:
                profile_pic = ''
            payment_details_exists = bool(JobPayments.query.filter_by(application_id=application_id).first())
            if payment_details_exists:
                payment_details = JobPayments.query.filter_by(application_id=application_id).first()
                hours = payment_details.total_hours
                amount = payment_details.total_amount
                hours_list.append(float(hours))
                amount_list.append(float(amount))
                user_dict['application_id'] = application_id
                user_dict['member_name'] = member_name
                user_dict['member_id'] = member_id
                user_dict['profile_pic'] = profile_pic
                user_dict['hours'] = hours
                user_dict['amount'] = '£'+str(amount)
                user_dict['per_hour_rate'] = per_hour_rate+'/hr'
                users_list.append(user_dict.copy())
                total_amount = '£'+str(sum(amount_list))
                total_hours = sum(hours_list)
        return make_response(jsonify({"job_details":job_dict,'total_hours':total_hours,
            'total_amount':total_amount,'hired_members':users_list}),200)

    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in past projects list at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#######Member Work Details for Past Projects ####################
@enq_main_bp.route("/memberWorkDetails/<application_id>", methods=['GET'])
@jwt_required
def memberWorkDetails(application_id):
    """Get Past Project member work  Details"""
    try:
        member_details = {}
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        user_instance = User.query.get(current_user)
        application_instance = AppliedJobs.query.get(application_id)
        member_id = application_instance.applied_by
        member_instance = User.query.get(member_id)
        member_name = member_instance.name
        profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
        if profile_exists:
            profile_instance = Profile.query.filter_by(user_id=member_id).first()
            profile_pic = profile_instance.profile_pic
        else:
            profile_pic = ''
        #Review
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
            avg = 4
        member_details['rating'] = avg
        member_details['member_name'] = member_name
        member_details['member_id'] = member_id
        member_details['profile_pic'] = profile_pic
        #Review
        reviews_dict = {}
        reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).filter_by(application_id=application_id).first())
        if reviews_exist:
            review = Reviews.query.filter_by(member_id=member_id).filter_by(application_id=application_id).first()
            stars = review.employer_stars
            review_text = review.employer_review
            reviews_dict['stars'] = stars
            reviews_dict['employer_review'] = review_text
        ##Work Details
        work_details_list = []
        work_detail_dict ={}
        job_logs = StartedJobLogs.query.filter_by(application_id=application_id)
        for log in job_logs:
            day_date = log.date
            start_time = log.start_time
            end_time = log.end_time
            hours = log.hours
            after_hours = log.after_hours
            work_detail_dict['day_date'] = day_date
            work_detail_dict['start_time'] = str(start_time)
            work_detail_dict['end_time'] = str(end_time)
            work_detail_dict['hours'] = hours
            work_detail_dict['after_hours'] = after_hours
            work_details_list.append(work_detail_dict.copy())
        return make_response(jsonify({"member_details":member_details,'work_details':work_details_list,
            'review':reviews_dict}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in past projects work details at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#######Finances####################
@enq_main_bp.route("/finances/", methods=['GET'])
@jwt_required
def finances():
    """Get Finances"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
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
                    shift_start_time = job_instance.shift_start_date
                    shift_end_date = job_instance.shift_end_date
                    job_end_month = shift_end_date.strftime("%B")
                    job_id = job_instance.id
                    job_type= job_instance.job_type
                    employer = job_instance.posted_by
                    # print('employer',employer,'current_user',current_user)
                    if employer == current_user:
                        if job_id not in jobs_list:
                            jobs_list.append(job_id)
                        business_name = job_instance.business_name 
                        city = job_instance.city
                        applications = AppliedJobs.query.filter_by(job_id=job_id)
                        for app_instance in applications:
                            app_id = app_instance.id
                            pay_instance = JobPayments.query.filter_by(application_id=app_id).first()
                        member_id = application.applied_by
                        applicant_instance = User.query.get(member_id)
                        member_name = applicant_instance.name
                        profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
                        if profile_exists:
                            profile_instance = Profile.query.filter_by(user_id=member_id).first()
                            profile_pic = profile_instance.profile_pic
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
                            transaction_dict['amount_paid'] = '£'+str(amount)
                            transaction_dict['application_id'] = application_id
                            transaction_dict['member_name'] = member_name
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
                            transaction_dict['amount_paid'] = '£'+str(amount)
                            transaction_dict['application_id'] = application_id
                            transaction_dict['member_name'] = member_name
                            transaction_dict['job_type'] = job_type
                            transaction_dict['profile_pic'] = profile_pic
                            transaction_dict['job_id'] = job_id
                            transaction_dict['month'] = job_end_month
                            transaction_dict['payment_status'] = status
                            transaction_dict['business_name'] = business_name
                            transaction_dict['stars'] = stars
                            unpaid_transactions.append(transaction_dict.copy())
            wallet_exists = bool(Wallet.query.filter_by(user_id=current_user).first())
            if wallet_exists:
                wallet_instance = Wallet.query.filter_by(user_id=current_user).first()
                balance = '£'+str(wallet_instance.balance)
            else:
                balance = '£0'
            for d in paid_transactions:
                amount = d['amount_paid']
                amount = amount.replace('£','')
                amounts_list.append(float(amount))
            total_amount = '£'+str(sum(amounts_list))
            mydate = datetime.now()
            month_name = mydate.strftime("%B")
            current_year = mydate.year
            print('current_year',current_year)
            total_jobs = str(len(jobs_list)) + ' jobs completed till ' + month_name +' '+ str(current_year)
        return make_response(jsonify({"paid_transactions":paid_transactions,
            'unpaid_transactions':unpaid_transactions,'total_paid':total_amount,'total_jobs':total_jobs,'funded':balance}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in transactions  at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#######Invoice Details####################
@enq_main_bp.route("/invoiceDetails/<transaction_id>", methods=['GET'])
@jwt_required
def invoiceDetails(transaction_id):
    """Get invoice Details"""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        transaction_dict ={}
        transaction_instance = JobPayments.query.get(transaction_id)
        hours = transaction_instance.total_hours
        amount = transaction_instance.total_amount
        status = transaction_instance.payment_status
        payment_date = transaction_instance.updated_at
        application_id = transaction_instance.application_id
        application_instance = AppliedJobs.query.get(application_id)
        job_id = application_instance.job_id
        job_instance = Jobs.query.get(job_id)
        business_name = job_instance.business_name
        shift_start_date = job_instance.shift_start_date
        shift_end_date = job_instance.shift_end_date
        per_hour_rate = '£'+str(application_instance.pay_expected)+'/hr'
        member_id = application_instance.applied_by
        applicant_instance = User.query.get(member_id)
        member_name = applicant_instance.name
        profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
        if profile_exists:
            profile_instance = Profile.query.filter_by(user_id=member_id).first()
            profile_pic = profile_instance.profile_pic
        else:
            profile_pic = ''
        reviews_exist = bool(Reviews.query.filter_by(member_id=member_id).filter_by(application_id=application_id).first())
        if reviews_exist:
            review = Reviews.query.filter_by(member_id=member_id).filter_by(application_id=application_id).first()
            stars = review.employer_stars
        else:
            stars = 4
        if status == 'pending':
            pass
        else:
            transaction_dict['payment_date'] = payment_date
        transaction_dict['transaction_id'] = transaction_id 
        transaction_dict['payment_status'] = status 
        transaction_dict['total_invoice_amount'] = '£'+str(amount)
        transaction_dict['application_id'] = application_id
        transaction_dict['member_name'] = member_name
        transaction_dict['profile_pic'] = profile_pic
        transaction_dict['job_id'] = job_id
        transaction_dict['payment_status'] = status
        transaction_dict['business_name'] = business_name
        transaction_dict['stars'] = stars
        transaction_dict['per_hour_rate'] = per_hour_rate
        transaction_dict['hours'] = hours
        transaction_dict['shift_start_date'] = shift_start_date
        transaction_dict['shift_end_date'] = shift_end_date
        return make_response(jsonify({"business_name":business_name,
            'invoice_details':transaction_dict}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in transactions  at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)
#################################################ENQUIRER PROFILE CRUD ROUTES#########################################

#CREATE
@enq_main_bp.route("/enquirerProfile/", methods=['POST'])
@jwt_required
def createProfile():
    """Add Enquirer Profile."""
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        # post_data = request.get_json()
        post_data = request.form
        try:
            print('request.files',request.files)
            f = request.files['company_logo']
            if f:
                filename = secure_filename(f.filename)
                f.save(os.path.join(enquirer_uploads, filename))
                company_logo_name = filename
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lNumber = exc_tb.tb_lineno
            print('error in company_logo at line',lNumber,'eror>>',e)
            company_logo_name = ''
        try:
            acs_reference_number = post_data['acs_reference_number']
        except Exception as e:
            print('sis not found')
            acs_reference_number = ''
        about = post_data['about']
        registration_number = post_data['registration_number']
        contact = post_data['contact']
        company_contact = post_data['company_contact']
        address = post_data['address']
        city = post_data['city']
        postal_code = post_data['postal_code']
        existing_profile = EnquirerProfile.query.filter_by(enquirer_id=current_user).first()
        if existing_profile:
            return make_response(jsonify({"error": "Profile already added. Please update to make changes"}),400)
        profile = EnquirerProfile(
                about = about,
                acs_reference_number = acs_reference_number,
                registration_number = registration_number,
                company_logo = company_logo_name,
                contact = contact,
                company_contact = company_contact,
                address = address,
                city = city,
                postal_code = postal_code,
                enquirer_id = current_user,
            )
        db.session.add(profile)
        db.session.commit()  # Create Enquirer profile
        existing_profile = EnquirerProfile.query.filter_by(enquirer_id=current_user).first()
        profile_id = existing_profile.id
        get_profile = EnquirerProfile.query.get(profile_id)
        profile_schema = EnquirerProfileSchema(many=False)
        profile = profile_schema.dump(get_profile)
        profile['name'] = user_instance.name
        return make_response(jsonify({"success": "Profile created successfully","profile":profile}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in saving profile at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#READ Profile
@enq_main_bp.route('/enquirerProfile/', methods = ['GET'])
@jwt_required
def readProfile():
    current_user = get_jwt_identity()
    user_instance = User.query.get(current_user)
    if user_instance.user_type == 'enquirer':
        pass
    else:
        return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
    print('current_user',current_user)
    # profile_instance = EnquirerProfile.query.filter_by(enquirer_id=current_user).first()
    profile_instance_exists =  bool(EnquirerProfile.query.filter_by(enquirer_id=current_user).first())
    if profile_instance_exists:
        profile_instance = EnquirerProfile.query.filter_by(enquirer_id=current_user).first()
        profile_id = profile_instance.id
        get_profile = EnquirerProfile.query.get(profile_id)
        if get_profile == None:
            return make_response(jsonify({"profile": []}),200)
    else:
        return make_response(jsonify({"profile": []}),200)
    profile_schema = EnquirerProfileSchema(many=False)
    profile = profile_schema.dump(get_profile)
    profile['name'] = user_instance.name
    #get_reviews = Reviews.query.filter_by(given_to=current_user)
    #reviews_schema = ReviewsSchema(many=True)
    #reviews = reviews_schema.dump(get_reviews)
    return make_response(jsonify({"profile": profile}),200)

#UPDATE
@enq_main_bp.route("/enquirerProfile/", methods=['PUT'])
@jwt_required
def updateProfile():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'enquirer':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for Enquirer/Company"}),400)
        profile_data = EnquirerProfile.query.filter_by(enquirer_id=current_user)
        for profile in profile_data:
            profile_id = profile.id 
        # data = request.get_json()
        data = request.form
        get_profile = EnquirerProfile.query.get(profile_id)
        enquirer_id = get_profile.enquirer_id
        if not str(current_user) == str(enquirer_id):
            return make_response(jsonify({"error": "Not an authentic user"}),400)
        if get_profile == None:
            return make_response(jsonify({"error": "No such profile exists"}),400)
        if data.get('acs_reference_number'):
            get_profile.acs_reference_number = data['acs_reference_number']
        if data.get('registration_number'):
            get_profile.registration_number = data['registration_number']
        try:
            print('request.files',request.files)
            f = request.files['company_logo']
            if f:
                filename = secure_filename(f.filename)
                f.save(os.path.join(enquirer_uploads, filename))
                get_profile.company_logo = filename
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lNumber = exc_tb.tb_lineno
            print('error in company_logo at line',lNumber,'eror>>',e)
            company_logo_name = ''
            get_profile.company_logo = ''
        if data.get('company_contact'):
            get_profile.company_contact= data['company_contact']
        if data.get('contact'):
            get_profile.contact= data['contact'] 
        if data.get('address'):
            get_profile.address= data['address'] 
        if data.get('about'):
            get_profile.about= data['about'] 
        if data.get('city'):
            get_profile.city= data['city']
        if data.get('postal_code'):
            get_profile.postal_code= data['postal_code']
        if data.get('about'):
            get_profile.about= data['about']       
        db.session.add(get_profile)
        db.session.commit()
        existing_profile = EnquirerProfile.query.filter_by(enquirer_id=current_user)
        for profile in existing_profile:
            profile_id = profile.id
            print('profile_id',profile_id)
        profile_instance = EnquirerProfile.query.get(profile_id)
        profile_schema = EnquirerProfileSchema(many=False)
        profile = profile_schema.dump(profile_instance)
        profile['name'] = user_instance.name
        return make_response(jsonify({"success":"Update successfull","profile": profile}))
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in update enquirer profile at line number',lNumber,'error is:',e)



#READ
@enq_main_bp.route('/enquirerProfile/', methods = ['GET'])
def getProfile():
    get_profile = EnquirerProfile.query.all()
    profile_schema = EnquirerProfileSchema(many=True)
    profiles = profile_schema.dump(get_profile)
    return make_response(jsonify({"profile": profiles}),200)


#READ BY ID
@enq_main_bp.route('/enquirerProfile/<id>', methods = ['GET'])
def getProfileById(id):
    get_profile = EnquirerProfile.query.get(id)
    if get_profile == None:
        return make_response(jsonify({"profile": []}),200)
    profile_schema = EnquirerProfileSchema(many=False)
    profile = profile_schema.dump(get_profile)
    return make_response(jsonify({"profile": profile}),200)

#READ BY Enquirer ID
@enq_main_bp.route('/enquirerProfileDetails', methods = ['GET'])
@jwt_required
def getEnquirerProfile():
    current_user = get_jwt_identity()
    profile_instance = bool(EnquirerProfile.query.filter_by(enquirer_id=current_user).first())
    user_instance = User.query.get(current_user)
    name = user_instance.name
    if profile_instance:
        profile_data = EnquirerProfile.query.filter_by(enquirer_id=current_user)
        for profile in profile_data:
            # company_name = profile.company_name
            profile_id = profile.id
            get_profile = EnquirerProfile.query.get(profile_id)
            profile_schema = EnquirerProfileSchema(many=False)
            user_profile = profile_schema.dump(get_profile)
            user_profile['name'] = name
    else:
        user_profile={'id':'','name':'','sis_number':'','company_logo':'',
        'phone_number':'','company_phone':'','hq_address_1':'','hq_address_2':'','state':'',
        'city':'','zip_code':'','created_at':'','updated_at':'','escrow_email':'','profile_pic':''}
    active_projects = []
    user_jobs = bool(Jobs.query.filter_by(posted_by=current_user).first())
    if user_jobs:
        jobs_list = []
        jobs_instance = Jobs.query.filter_by(posted_by=current_user)
        for job in jobs_instance:
            jobs_list.append(job.id)
        print('jobs_list',jobs_list)
        active_projects_dict = {'days_remaining':'','job_title':'','company_name':'','applicants':'','city':'','location':''}
        applied_job_exist = bool(AppliedJobs.query.filter(Jobs.id.in_(jobs_list)).filter_by(is_active=True).first())
        if applied_job_exist:
            active_jobs = AppliedJobs.query.filter(Jobs.id.in_(jobs_list)).filter_by(is_active=True)
            for job in active_jobs:
                job_id = job.job_id
                job_instance = Jobs.query.get(job_id)
                start_date = job_instance.shift_start_date
                today_date = date.today()
                delta = start_date - today_date
                days_remaining = delta.days
                job_title = job_instance.business_name
                applicants = job_instance.interested_count
                enquirer_id = job_instance.posted_by
                enquirer_data = User.query.get(enquirer_id)
                company_name = enquirer_data.name
                location = job_instance.address 
                enquirer_profile_instance = bool(EnquirerProfile.query.filter_by(enquirer_id=enquirer_id).first())
                if enquirer_profile_instance:
                    profile_instance = EnquirerProfile.query.filter_by(enquirer_id=enquirer_id)
                    for profile in profile_instance:
                        # company_name = profile.company_name
                        city = profile.city
                else:
                    city = ''
                    name = ''
                active_projects_dict['job_title'] = job_title
                active_projects_dict['days_remaining'] = days_remaining
                active_projects_dict['company_name'] = company_name
                active_projects_dict['applicants'] = applicants
                active_projects_dict['city'] = city
                active_projects_dict['location'] = location
                active_projects.append(active_projects_dict.copy())
        else:
            active_projects = []
    else:
        active_projects = []
    finances = []
    current_user = get_jwt_identity()
    cards_list = []
    card_dict = {}
    try:
        existing_cards = Cards.query.filter_by(user=current_user)
        for card in existing_cards:
            card_dict['card_number'] = card.card_number
            card_dict['name_on_card'] = card.name_on_card
            card_dict['expiry_date'] = card.expiry_date
            card_dict['cvv'] = card.cvv
            card_dict['card_'] = card.card_type
            card_dict['status'] = card.is_active
            cards_list.append(card_dict.copy())
    except Exception as e:
        card_list = []
    finances_dict = {'job_title':'','completed_on':'','amount':'','paid_to':'','paid_by':'',
    'profile_pic':''}
    try:
        applied_job_exist = bool(AppliedJobs.query.filter(Jobs.id.in_(jobs_list)).filter_by(is_completed=True).first())
        if applied_job_exist:
            for job in jobs_list:
                completed_job = AppliedJobs.query.filter_by(job_id = job).filter_by(is_completed=True)
                for application in completed_job:
                    job_id = application.job_id
                    print('completed_job_id',job_id)
                    completed_on = application.completed_on
                    amount = application.payment_received
                    member_id = application.applied_by
                    user_instance = User.query.get(member_id)
                    user_id = user_instance.id
                    paid_to = user_instance.name
                    profile_instance_exists = bool(Profile.query.filter_by(user_id=user_id).first())
                    if profile_instance_exists:
                        profile_instance = Profile.query.filter_by(user_id=user_id).first()
                        profile_pic = profile_instance.profile_pic
                    else:
                        profile_pic = '' 
                    job_instance = Jobs.query.get(job_id)
                    job_title = job_instance.job_title
                    finances_dict['job_title'] = job_title
                    finances_dict['completed_on'] = completed_on
                    finances_dict['amount'] = amount
                    finances_dict['paid_to'] = paid_to
                    finances_dict['paid_by'] = company_name
                    finances_dict['profile_pic'] = profile_pic
                    finances.append(finances_dict.copy())
        else:
            finances = []
    except Exception as e:
        finances = []
    print('finances',finances)
    return make_response(jsonify({"about": user_profile,'saved_cards':cards_list,'dashboard':active_projects, 'finances':finances}),200)



#DELETE
@enq_main_bp.route('/enquirerProfile/<id>', methods = ['DELETE'])
def deleteProfile(id):
    get_profile = EnquirerProfile.query.get(id)
    if get_profile == None:
        return make_response(jsonify({"error": "No such profile exists"}),400)
    db.session.delete(get_profile)
    db.session.commit()
    return make_response(jsonify({"success":"Delete successfull"}),200)

#Get Member Location
@enq_main_bp.route('/memberLocation/<member_id>', methods = ['GET'])
def memberLocation(member_id):
    member_details_list = []
    member_details_dict = {}
    profile_instance_exists = bool(Profile.query.filter_by(user_id=member_id).first())
    user_instance = User.query.get(member_id)
    if profile_instance_exists:
        profile_instance = Profile.query.filter_by(user_id=member_id).first()
        profile_pic = profile_instance.profile_pic
        city = profile_instance.city
        state = profile_instance.state
        try:
            geolocator = Nominatim(user_agent="openarc")
            location = geolocator.geocode(city)
            latitude = location.latitude
            longitude = location.longitude
        except Exceptiona as e:
            latitude = ''
            longitude = ''
    else:
        latitude = ''
        longitude = ''
        profile_pic = ''
        city = ''
        state = ''
    name = user_instance.name
    member_id = member_id
    member_details_dict['member_id'] = member_id
    member_details_dict['name'] = name
    member_details_dict['profile_pic'] = profile_pic
    member_details_dict['latitude'] = latitude
    member_details_dict['longitude'] = longitude
    member_details_dict['city'] = city
    member_details_dict['state'] = state
    member_details_list.append(member_details_dict)
    return make_response(jsonify({"member_details": member_details_list}))

#Get OnSite Details
@enq_main_bp.route('/siteDetails/<job_id>', methods = ['GET'])
def siteDetails(job_id):
    #Job Details
    job_list = []
    job_dict = {}
    job_details = Jobs.query.get(job_id)
    posted_on = job_details.created_at
    job_title = job_details.job_title
    job_dict['job_id'] = job_id
    job_dict['job_title'] = job_title
    job_dict['posted_on'] = job_details.created_at
    job_list.append(job_dict)
    #On Site Team
    onsite_data_list = []
    onsite_data_dict={}
    job_members = AppliedJobs.query.filter_by(job_id=job_id).filter_by(is_active=True)
    for member in job_members:
        per_hour_rate = member.pay_expected
        if '$' in per_hour_rate:
            hourly_rate = per_hour_rate.replace('$','')
        member_id = member.applied_by
        user_instance = User.query.get(member_id)
        user_name = user_instance.name
        profile_exists = bool(Profile.query.filter_by(user_id=member_id).first())
        if profile_exists:
            profile_instance = Profile.query.filter_by(user_id=member_id).first()
            profile_pic = profile_instance.profile_pic
            city = profile_instance.city
            state = profile_instance.state
            try:
                geolocator = Nominatim(user_agent="openarc")
                location = geolocator.geocode(city)
                latitude = location.latitude
                longitude = location.longitude
            except Exceptiona as e:
                latitude = ''
                longitude = ''
        else:
            profile_pic = ''
            city = ''
            state = ''
        #Time Calculation
        application_details = AppliedJobs.query.filter_by(job_id=job_id).filter_by(applied_by=member_id).first()
        application_id = application_details.id
        print('id',application_id)
        payments_list = []
        requests_list = []
        hours_list = []
        job_logs_exists = bool(StartedJobLogs.query.filter_by(application_id=application_id).filter_by(amount_paid=False).first())
        print('job_logs_exists',job_logs_exists)
        if job_logs_exists:
            job_logs = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(amount_paid=False)
            for log in job_logs:
                print('inside for loop>>')
                shifts_count =  bool(StartedJobLogs.query.filter_by(application_id=application_id).filter_by(amount_paid=False))
                if shifts_count:
                    shifts_count = StartedJobLogs.query.filter_by(application_id=application_id).filter_by(amount_paid=False).count()
                else:
                    shifts_count = 0
                payment = log.amount
                hours = log.hours
                payment_requested = log.payment_requested
                payment_request = log.payment_requested
                hours_list.append(int(hours))
                requests_list.append(payment_request)
                payments_list.append(int(payment))
            total_payment = sum(payments_list)
            total_hours = sum(hours_list)
            print('requests_list',requests_list)
            if True in requests_list:
                requested = True
            else:
                requested = False
        else:
            total_payment = 0
            total_hours = 0
            shifts_count = 0
            requested = False
        onsite_data_dict['member_name'] = user_name
        onsite_data_dict['payment_requested'] = requested
        onsite_data_dict['profile_pic'] = profile_pic
        onsite_data_dict['shifts_count'] = shifts_count
        onsite_data_dict['total_payment'] = total_payment
        onsite_data_dict['total_hours'] = total_hours
        onsite_data_dict['latitude'] = latitude
        onsite_data_dict['longitude'] = longitude
        onsite_data_list.append(onsite_data_dict.copy())
    return make_response(jsonify({"job_details": job_list,"onsite_data":onsite_data_list}))
            
# ######################################################################################################

# ################################################Enquirers#################################################

#GET ALL Enquirers
@enq_main_bp.route('/enquirers/', methods = ['GET'])
def getUsers():
    get_users = User.query.filter_by(user_type='enquirer')
    user_schema = UserSchema(many=True)
    users = user_schema.dump(get_users)
    return make_response(jsonify({"enquirers": users}))

#READ BY ID
@enq_main_bp.route('/enquirer/<id>', methods = ['GET'])
def getUserById(id):
    get_user = User.query.filter_by(id=id).filter_by(user_type='enquirer').first()
    if get_user == None:
        return make_response(jsonify({"enquirer": '[]'}),200)
    user_schema = UserSchema(many=False)
    user = user_schema.dump(get_user)
    return make_response(jsonify({"enquirer": user}))

########################################################################################################

############################STRIPE######################################################################

#Create Session
@enq_main_bp.route("/createSession/", methods=['POST'])
@jwt_required
def createSession():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        email = user_instance.email
        ###############Sent Data######################
        post_data = request.form
        plan_id = post_data['plan_id']
        plan_cycle = post_data['plan_cycle']
        if ((plan_id == '' ) or (plan_cycle == '')):
            return make_response(jsonify({"error": 'plan_id and plan_cycle is required'}),200)
        #Get Plan Details
        plan_details = SubscriptionPlans.query.get(plan_id)
        if ((plan_cycle == 'monthly') or (plan_cycle == 'Monthly')):
            amount = plan_details.monthly_payment
            if "£" in amount:
                amount = amount.replace('£','')
        else:
            amount = plan_details.yearly_payment
            if "£" in amount:
                amount = amount.replace('£','')
        plan_price = int(float(amount))
        ###Make Stripe Session##########
        price = stripe.Price.create(
          unit_amount=plan_price*100,
          currency="gbp",
          product_data={'name':'payment'}
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
                  "name" : plan_details.plan_name,
                  "description" : plan_details.description,
                  "amount" : plan_price*100,
                  "currency" : 'gbp',
                },
              ],
              mode="payment"
        )
        print('session_id',session_obj.id)
        success_url = "https://18.188.166.194/checkout?sc_checkout=success&sc_sid="+session_obj.id
        cancel_url = "https://arcopen.space/checkout?sc_checkout=cancel"

        # success_url="https://arcopen.space/success/"+session_obj.id,
        # cancel_url="https://arcopen.space/cancel/"+session_obj.id,
        session_obj['success_url'] = success_url
        session_obj['cancel_url'] = cancel_url
        return make_response(jsonify({"session":session_obj}),200)  
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error creating session at line',lNumber,'error',e)
        return make_response(jsonify({"error in session":str(e)}),400)

#CREATE CONNECTED ACCOUNT FOR USER
@enq_main_bp.route("/stripeDetails/", methods=['POST'])
@jwt_required
def createConnectedAccount():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        acc_exists = StripeDetails.query.filter_by(user_id=current_user).first()
        if acc_exists:
            connected_account = acc_exists.connected_account
            if connected_account:
                return make_response(jsonify({"error": "Connecting Account already exists"}),400)
        post_data = request.form
        # print('post_data',post_data,'files',request.files)
        # post_files = request.files
        # identity_document_front = post_data['identity_document_front']
        # identity_document_back = post_data['identity_document_back']
        # additional_identity_document_front = post_data['additional_identity_document_front']
        # additional_identity_document_back = post_data['additional_identity_document_back']
        #Save images to folder
        #identity_document_front
        identity_document_front_string = post_data['identity_document_front']
        if 'base64' in identity_document_front_string:
            base64_data = re.sub('^data:image/.+;base64,', '', identity_document_front_string)
            logo_string = identity_document_front_string.split(';')[0]
            image_type = logo_string.split('/')[1]
        image_name = 'identity_document_front_'+str(current_user)+'.'+image_type
        identity_document_front = stripe_uploads+'/'+image_name
        with open(identity_document_front, "wb") as fh:
            fh.write(base64.b64decode(base64_data))
        #identity_document_back
        identity_document_back_string = post_data['identity_document_back']
        if 'base64' in identity_document_back_string:
            base64_data = re.sub('^data:image/.+;base64,', '', identity_document_back_string)
            logo_string = identity_document_back_string.split(';')[0]
            image_type = logo_string.split('/')[1]
        image_name = 'identity_document_back_'+str(current_user)+'.'+image_type
        identity_document_back = stripe_uploads+'/'+image_name
        with open(identity_document_back, "wb") as fh:
            fh.write(base64.b64decode(base64_data))
        #additional_identity_document_front
        additional_identity_document_front_string = post_data['additional_identity_document_front']
        if 'base64' in additional_identity_document_front_string:
            base64_data = re.sub('^data:image/.+;base64,', '', additional_identity_document_front_string)
            logo_string = additional_identity_document_front_string.split(';')[0]
            image_type = logo_string.split('/')[1]
        image_name = 'additional_identity_document_front_'+str(current_user)+'.'+image_type
        additional_identity_document_front = stripe_uploads+'/'+image_name
        with open(additional_identity_document_front, "wb") as fh:
            fh.write(base64.b64decode(base64_data))
        #additional_identity_document_back
        additional_identity_document_back_string = post_data['additional_identity_document_back']
        if 'base64' in additional_identity_document_back_string:
            base64_data = re.sub('^data:image/.+;base64,', '', additional_identity_document_back_string)
            logo_string = additional_identity_document_back_string.split(';')[0]
            image_type = logo_string.split('/')[1]
        image_name = 'additional_identity_document_back_'+str(current_user)+'.'+image_type
        additional_identity_document_back = stripe_uploads+'/'+image_name
        with open(additional_identity_document_back, "wb") as fh:
            fh.write(base64.b64decode(base64_data))
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
        (state == '') or (sort_number == '') or (account_number == '') or (account_number == '') 
        or (account_number == '') or (account_number == '') or (account_number == '')):
            return make_response(jsonify({"error":'All parameters are required'}),400)
        ##Get identity document front file token
        with open(identity_document_front, "rb") as fp:
            res = stripe.File.create(
                    purpose='identity_document',
                    file=fp
                )
            print('ress',res)
        identity_document_front_token = res['id']
        ##Get identity document back file token
        with open(identity_document_back, "rb") as fp:
            res = stripe.File.create(
                    purpose='identity_document',
                    file=fp
                )
            print('ress',res)
        identity_document_back_token = res['id']
        ##Get additional identity document front file token
        with open(additional_identity_document_front, "rb") as fp:
            res = stripe.File.create(
                    purpose='additional_verification',
                    file=fp
                )
            print('ress',res)
        additional_identity_document_front_token = res['id']
        ##Get additional identity document back file token
        with open(additional_identity_document_back, "rb") as fp:
            res = stripe.File.create(
                    purpose='additional_verification',
                    file=fp
                )
            print('ress',res)
        additional_identity_document_back_token = res['id']
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
                        "back": additional_identity_document_back_token,
                        "front": additional_identity_document_front_token
                    },
                    "document":{
                        "back": identity_document_front_token,
                        "front": identity_document_back_token 
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
            # tos_acceptance={
            #     'service_agreement': 'recipient',
            # },
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

#Fund A Wallet
@enq_main_bp.route("/fundWallet/", methods=['POST'])
@jwt_required
def addMoneyToWallet():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        ###############Card Token######################
        post_data = request.form
        amount = post_data['amount']
        card_number = post_data['card_number']
        exp_month = post_data['exp_month']
        exp_year = post_data['exp_year']
        cvv = post_data['cvv']
        if((card_number == '') or (exp_year=='') or (exp_month=='') or (cvv=='') or (amount=='')):
            return make_response(jsonify({"error":'All parameters are required'}),400)
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
        payable_amount = int(amount)*100
        charge = stripe.Charge.create(
          amount=payable_amount,
          currency=currency,
          description='Fund Wallet',
          source=token,
        )
        ##############################################Save to openarc db####################################
        funding_instance = UserPayments(
                reference = 'Wallet Funding',
                medium = 'card',
                amount = amount,
                user_id = current_user
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
            total_balance = int(balance)+int(amount)
            wallet_instance.balance = total_balance
        else:
            wallet_instance = Wallet(
                    balance = amount,
                    user_id = current_user
                )
        try:
            local_object = db.session.merge(wallet_instance)
            db.session.add(local_object)
        except Exception as e:
            print('error in commit',e)
            db.session.add(wallet_instance)
        db.session.commit()
        ############return updated record########################
        existing_wallet = Wallet.query.filter_by(user_id=current_user)
        for record in existing_wallet:
            wallet_id = record.id
            # print('profile_id',profile_id)
        record_instance = Wallet.query.get(wallet_id)
        record_schema = WalletSchema(many=False)
        record = record_schema.dump(record_instance)
        return make_response(jsonify({"status":"success","wallet":record}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('line',lNumber,'error',e)
        return make_response(jsonify({"error in payment":str(e)}),400)


#Get Wallet Details
@enq_main_bp.route("/getWalletDetails/", methods=['GET'])
@jwt_required
def getWallet():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        existing_wallet = bool(Wallet.query.filter_by(user_id=current_user).first())
        if existing_wallet:
            wallet_details = Wallet.query.filter_by(user_id=current_user).first()
            wallet_id = wallet_details.id
            record_instance = Wallet.query.get(wallet_id)
            record_schema = WalletSchema(many=False)
            record = record_schema.dump(record_instance)
            #payments
            existing_payments = bool(UserPayments.query.filter_by(user_id=current_user).first())
            if existing_payments:
                # payments_details = UserPayments.query.filter_by(user_id=current_user).first()
                # payment_id = payments_details.id
                record_inst = UserPayments.query.filter_by(user_id=current_user)
                record_schema = UserPaymentsSchema(many=True)
                payment_records = record_schema.dump(record_inst)
        else:
            record =  {
                "balance": "0",
                "created_at": "",
                "id": "",
                "updated_at": "",
                "user_id": current_user
            }
        return make_response(jsonify({"wallet":record,'payments':payment_records}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('line',lNumber,'error',e)
        return make_response(jsonify({"error in getting wallet":str(e)}),400)
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
  