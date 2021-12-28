"""Routes for user authentication."""
from flask import redirect, render_template, flash, Blueprint, request, url_for, jsonify, make_response
from flask_login import current_user, login_user
from .models import db, EnquirerProfile, EnquirerProfileSchema
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
from services.Users.Member.models import *


# Blueprint Configuration
enq_auth_bp = Blueprint(
    'enq_auth_bp', __name__,
)


def check_email(email):
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'   
    if(re.search(regex,email)):  
        return True  
    else:  
        return False  

#####################################################ENQUIRER AUTHENTICATION ROUTES############################

#SIGNUP
@enq_auth_bp.route('/enquirerSignup/', methods=['POST'])
def signup():
    """
    Enquirer sign-up.
    POST requests validate params & user creation.
    """
    try:
        post_data = request.get_json()
        organisation_name = post_data['organisation_name']
        email = post_data['email']
        password = post_data['password']
        device_type = post_data['device_type']
        device_id = post_data['device_id']
        if ((organisation_name == '') or (email == '') or (password == '') or (device_type == '') or (device_id == '')):
            return make_response(jsonify({"error": "please pass all parameters"}),400)
        is_valid = check_email(email)
        if not is_valid:
            return Response("{'error':'please pass a valid email address'}", status=400)
        existing_user = User.query.filter_by(email=email).first()
        print('existing_user',existing_user)
        if existing_user is None:
            user = User(
                name=organisation_name,
                email=email,
                user_type = 'enquirer',
                device_type = device_type,
                device_id = device_id
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()  # Create new user
            token = generate_confirmation_token(email)
            confirm_url = url_for('auth_bp.confirm_email', token=token, _external=True)
            subject = "Please confirm your email"
            send_email(email, organisation_name, subject, confirm_url)
            login_user(user)
            return make_response(jsonify({"success": "Enquirer registration successfull. An email is sent to you for account verification"}),200)
        else:
            user_type = existing_user.user_type  
            return make_response(jsonify({"error": "User with same email already exists as "+ user_type}),200)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in enquirer registartion at line number',lNumber,'filename is :',fname,'-----------error is:',e)
        return make_response(jsonify({"error": str(e)}),200)

#CONFIRM EMAIL
@enq_auth_bp.route('/confirmEnquirerAccount/<token>', methods=['GET','POST'])
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        return Response("{'error':'The confirmation link is invalid or has expired'}", status=400)
    enquirer = User.query.filter_by(email=email).first_or_404()
    if enquirer:
        if enquirer.is_verified:
            return Response("{'success':'Account already confirmed. Please login.'}", status=200)
        else:
            enquirer.is_verified = True
            db.session.add(enquirer)
            db.session.commit()
            return Response("{'success':'You have confirmed your account. Thanks!'}", status=200)


#LOGIN
@enq_auth_bp.route('/enquirerLogin/', methods=['POST'])
def enquirerlogin():
    """
    User Log-in
    POST requests validate and redirect user to dashboard.
    """
    # Bypass if user is logged in
    # if current_user.is_authenticated:
    #     return Response("{'success':'Enquirer is already loggedin'}", status=200)  

    try:
        post_data = request.get_json()
        email = post_data['email']
        password = post_data['password']
        if ((email == '') or (password == '')):
            return make_response(jsonify({"error": 'please pass both parameters'}),400)
        is_valid = check_email(email)
        if not is_valid:
            return make_response(jsonify({"error": 'please pass a valid email address'}),400)
        user_instance = User.query.filter_by(email=email).first()
        profile_instance = bool(EnquirerProfile.query.filter_by(enquirer_id=user_instance.id).first())  
        if user_instance and user_instance.check_password(password=password):
            if user_instance.is_verified:
                login_user(user_instance,remember=True)
            else:
                return make_response(jsonify({"error": 'please activate your account first'}),400)
            # Identity can be any data that is json serializable
            access_token = create_access_token(identity=user_instance.id,expires_delta=False)
            get_user = User.query.get(user_instance.id)
            user_schema = UserSchema(many=False)
            profile = user_schema.dump(get_user)
            return make_response(jsonify({"access_token":access_token,"user": profile,"profile_exists":profile_instance}),200)
        else:
            return make_response(jsonify({"error": 'invalid credentials'}),400)
    except Exception as e:
        print('error in login',e)
        return make_response(jsonify({"error": str(e)}),400)

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



