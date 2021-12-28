"""Logged-in page routes."""
from flask import Blueprint, request, jsonify, make_response, render_template
from flask_login import current_user, login_required, logout_user
from flask import Response
from .models import User, Profile, ProfileSchema, UserSchema
from services.Users import db
import shutil 
from os import environ, path
from dotenv import load_dotenv
import sys, os
from flask_jwt_extended import jwt_required , get_jwt_identity
from services.Users.Enquirer.models import *
from services.Jobs.models import *
import base64, re
from werkzeug.utils import secure_filename
import ast
from pyfcm import FCMNotification
from werkzeug.utils import secure_filename

basedir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', '..'))
load_dotenv(path.join(basedir, '.env'))

# Blueprint Configuration
main_bp = Blueprint(
    'main_bp', __name__,
)

enquirer_uploads = environ.get('ENQUIRER_UPLOADS')
member_uploads = environ.get('MEMBER_UPLOADS')
# member_uploads = '/var/www/Projects/OpenArc/Push/openarc-flask/media/uploads/member/'

# enquirer_uploads = 'http://164.90.186.255/Openarc/images/uploads/enquirer/'
# member_uploads = 'http://164.90.186.255/Openarc/images/uploads/member/'



# Add Device FCM Token
@main_bp.route('/addFCMToken/', methods=['POST'])
@jwt_required
def addFCMToken():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        post_data = request.get_json()    
        fcm_token = post_data.get('fcm_token')
        if fcm_token == '':
            return make_response(jsonify({"error": 'Please pass device fcm token '}),400)
        user_instance.device_id = fcm_token
        db.session.add(user_instance)
        db.session.commit()  #
        return make_response(jsonify({"success": 'device_fcm_token added'}),400)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in addingFCM token at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#HomePage
@main_bp.route('/', methods=['GET','POST'])
def index():
    return render_template('home.html')

#CREATE
@main_bp.route("/profile/", methods=['POST'])
@jwt_required
def createProfile():
    """Add Member Profile."""
    try:
        unavailability_array = []
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
            return Response("{'error':'No such profile exists'}", status=400)
        try:
            # post_data = request.get_json()
            post_data = request.form    
            contact = post_data.get('contact')
            address = post_data.get('address')
            about = post_data.get('about')
            drive = post_data.get('drive')
            hourly_rate = post_data.get('hourly_rate')
            try:
                f = request.files['profile_pic']
                if f:
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(member_uploads, filename))
                    profile_pic_name = filename
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                lNumber = exc_tb.tb_lineno
                print('error in profile_pic at line',lNumber,'eror>>',e)
                profile_pic_name = ''
            try:
                f = request.files['cv']
                if f:
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(member_uploads, filename))
                    cv_file = filename
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                lNumber = exc_tb.tb_lineno
                print('error in cv at line',lNumber,'error>>',e)
                cv_file = ''
            city = post_data.get('city')
            postal_code = post_data.get('postal_code')
            try:
                existing_profile = Profile.query.filter_by(user_id=current_user).first()
            except Exception as e:
                pass
            if drive == 'Yes':
                drive = True
            else:
                drive = False
            ####Unavailability Dates
            unavailable_dates = post_data.get('unavailable_dates',None)
            if existing_profile:
                return make_response(jsonify({"error": "Profile already added. Please update to make changes"}),400)
            profile = Profile(
                    contact = contact,
                    documents = cv_file,
                    address = address,
                    city = city,
                    drive = drive,
                    postal_code = postal_code,
                    user_id = current_user,
                    profile_pic = profile_pic_name,
                    about = about,
                    hourly_rate = hourly_rate,
                    unavailability = str(unavailable_dates)
                )
            ####Ends Here
            db.session.add(profile)
            # db.session.add(profile_instance)
            db.session.commit()  # Create user profile
            existing_profile = Profile.query.filter_by(user_id=current_user).first()
            profile_id = existing_profile.id
            get_profile = Profile.query.get(profile_id)
            profile_schema = ProfileSchema(many=False)
            profile = profile_schema.dump(get_profile)
            profile['badge_number'] = user_instance.badge_number
            # profile['document_name'] = get_profile.documents
            # profile['unavailable_dates'] = ast.literal_eval(get_profile.unavailability)
            return make_response(jsonify({"success": "Profile created successfully","profile":profile}),200)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lNumber = exc_tb.tb_lineno
            print('error in profile at line',lNumber,'error>>',e)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in saving profile at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)


#READ BY ID
@main_bp.route('/memberProfile', methods = ['GET'])
@jwt_required
def getMemberProfile():
    current_user = get_jwt_identity()
    profile_instance = bool(Profile.query.filter_by(user_id=current_user).first())
    user_instance = User.query.get(current_user)
    name = user_instance.name
    #Rating
    stars_list = []
    reviews_exist = bool(Reviews.query.filter_by(member_id=current_user).first())
    if reviews_exist:
        reviews = Reviews.query.filter_by(member_id=current_user)
        for review in reviews:
            stars = review.employer_stars
            stars_list.append(int(stars))
            total = sum(stars_list)
            count = len(stars_list)
            avg = total/count
    else:
        avg = 2
    if profile_instance:
        profile_data = Profile.query.filter_by(user_id=current_user)
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
            print('unavailability',unavailability,type(unavailability))
            try:
                unavailability = unavailability.strip()
            except Exception as e:
                print('error',e)
            if ((unavailability == '') or (unavailability == None)):
                user_profile['unavailable_dates'] = []
            else:
                user_profile['unavailable_dates'] = ast.literal_eval(unavailability)
    else:
        user_profile={'id':'','name':'','document_name':'','profile_pic':'','about':'','contact':'','address':'',
        'city':'','hourly_rate':'','created_at':'','updated_at':'','availability_dates':'','postal_code':'',
        'drive':'','name':'','badge_number':''}
    #Reviews
    reviews_list = []
    review_dict = {}
    reviews_exist = bool(Reviews.query.filter_by(member_id=current_user).first())
    if reviews_exist:
        reviews = Reviews.query.filter_by(member_id=current_user)
        for review in reviews:
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
            review_dict['text'] = text
            review_dict['rating'] = stars
            review_dict['profile_pic'] = employer_profile_pic
            reviews_list.append(review_dict.copy())
    return make_response(jsonify({"profile": user_profile,'reviews':reviews_list}),200)


#UPDATE
@main_bp.route("/profile/", methods=['PUT'])
@jwt_required
def updateProfile():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance.user_type == 'member':
            pass
        else:
            return make_response(jsonify({"error": "Function only allowed for member"}),400)
        exists = bool(Profile.query.filter_by(user_id=current_user).first())
        if exists:
            profile_data = Profile.query.filter_by(user_id=current_user)
            for profile in profile_data:
                profile_id = profile.id
        else:
             return make_response(jsonify({"error": "No profile exists for this member"}),400)
        # data = request.get_json()
        data = request.form
        print('data---->>>>>here',data,request.files)
        get_profile = Profile.query.get(profile_id)
        if get_profile == None:
            return Response("{'error':'No such profile exists'}", status=400)
        if data:
            if data.get('contact'):
                get_profile.contact = data['contact']
            if data.get('address'):
                get_profile.address = data['address']
            if data.get('drive'):
                drive = data.get('drive')
                if drive == 'Yes' or drive == 'yes':
                    drive = True
                else:
                    drive = False
                get_profile.drive= drive
            ####Unavailability Dates
            if data.get('unavailable_dates'):
                unavailable_dates = data['unavailable_dates']
                get_profile.unavailability= str(unavailable_dates)
            if data.get('city'):
                get_profile.city= data['city']
            if data.get('badge_number'):
                user_instance.badge_number= data['badge_number']
            if data.get('hourly_rate'):
                print('here',data['hourly_rate'])
                get_profile.hourly_rate= data['hourly_rate']   
            if data.get('about'):
                get_profile.about= data['about'] 
            if data.get('postal_code'):
                get_profile.postal_code= data['postal_code']  
        try:
            print('request.files',request.files)
            f = request.files['profile_pic']
            if f:
                filename = secure_filename(f.filename)
                print('filename>>',member_uploads)
                f.save(os.path.join(member_uploads, filename))
                get_profile.profile_pic = filename
                print('saved')
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lNumber = exc_tb.tb_lineno
            print('error in profile_pic at line',lNumber,'eror>>',e)
            profile_pic_name = ''
            get_profile.profile_pic = ''
        try:
            print('request.files',request.files)
            f = request.files['cv']
            if f:
                filename = secure_filename(f.filename)
                f.save(os.path.join(member_uploads, filename))
                get_profile.documents = filename
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lNumber = exc_tb.tb_lineno
            print('error in cv at line',lNumber,'eror>>',e)
            profile_pic_name = ''
            get_profile.documents = ''   
        db.session.add(get_profile)
        db.session.add(user_instance)
        db.session.commit()
        profile_schema = ProfileSchema(many=False)
        profile = profile_schema.dump(get_profile)
        profile['badge_number'] = user_instance.badge_number
        # profile['document_name'] = get_profile.documents
        # profile['document_string'] = get_profile.documents
        # profile['unavailable_dates'] = ast.literal_eval(get_profile.unavailability)
        return make_response(jsonify({"success":"Update successfull","profile": profile}))
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in update profile at line number',lNumber,'error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#Get All Members
@main_bp.route('/getGuardsList', methods = ['GET'])
def getGuardsList():
    guards_list = []
    guards_dict = {}
    stars_list = []
    get_guards = User.query.filter_by(user_type='member')
    for guard in get_guards:
        name = guard.name
        guard_id=guard.id
        complete_job_applications = AppliedJobs.query.filter_by(applied_by=guard_id).filter_by(is_funded=True).filter_by(is_active=False).count()
        guards_dict['id']=guard_id
        guards_dict['name']=name
        guards_dict['completed_jobs']=complete_job_applications
        reviews_exist = bool(Reviews.query.filter_by(member_id=guard_id).first())
        if reviews_exist:
            reviews = Reviews.query.filter_by(member_id=guard_id)
            for review in reviews:
                stars = review.employer_stars
                stars_list.append(int(stars))
                total = sum(stars_list)
                count = len(stars_list)
                avg = total/count
        else:
            avg = 4
        exists = bool(Profile.query.filter_by(user_id=guard_id).first())
        if exists:
            profile_data = Profile.query.filter_by(user_id=guard_id).first()
            hourly_rate = profile_data.hourly_rate
            profile_pic = profile_data.profile_pic
        else:
            hourly_rate = '£0'
            profile_pic = ''
        guards_dict['hourly_rate']=hourly_rate
        guards_dict['profile_pic']=profile_pic
        guards_dict['rating']=avg
        guards_list.append(guards_dict.copy())        
    return make_response(jsonify({"guards":guards_list}),200)
######################################################################################################




