"""Routes for user authentication."""
from flask import redirect, render_template, flash, Blueprint, request, url_for, jsonify, make_response
from flask_login import current_user, login_user
from .models import User, Profile, UserSchema
from services.Users.Enquirer.models import *
from services.Users import login_manager
from flask import Response
from .token import generate_confirmation_token, confirm_token
from .email import *
import sys,os
from flask_login import current_user, login_required
from os import environ, path
from dotenv import load_dotenv
from services.Users import db
from flask_jwt_extended import create_access_token, jwt_required, get_raw_jwt
import re
from flask_jwt_extended import jwt_required , get_jwt_identity

   

blacklist = set()

# Blueprint Configuration
auth_bp = Blueprint(
    'auth_bp', __name__,
)


def check_email(email):
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'   
    if(re.search(regex,email)):  
        return True  
    else:  
        return False  


#####################################################MEMBER AUTHENTICATION ROUTES############################

#SIGNUP
@auth_bp.route('/signup/', methods=['POST'])
def signup():
    """
    User sign-up.
    POST requests validate params & user creation.
    """
    try:
        post_data = request.get_json()
        email = post_data['email']
        name = post_data['name']
        password = post_data['password']
        device_type = post_data['device_type']
        device_id = post_data['device_id']
        badge_number = post_data['badge_number']
        expiry_date = post_data['expiry_date']
        if ((name == '') or (email == '') or (password == '') or (device_type == '') 
            or (badge_number == '') or (expiry_date == '')):
            return make_response(jsonify({"error": "please pass all parameters"}),400)
        is_valid = check_email(email)
        if not is_valid:
            return make_response(jsonify({"error": "please pass a valid email address"}),400)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is None:
            user = User(
                email=email,
                user_type = 'member',
                device_type = device_type,
                device_id = device_id,
                name = name,
                badge_number=badge_number,
                expiry_date = expiry_date
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()  # Create new user
            token = generate_confirmation_token(email)
            confirm_url = url_for('auth_bp.confirm_email', token=token, _external=True)
            subject = "Account Activation email"
            try:
                send_email(email, name, subject, confirm_url)
            except Exception as e:
                pass
            login_user(user)
            return make_response(jsonify({"success": "Member registration successfull. An email is sent to you for account verification.Please complete your profile first."}),200)
        else:
            user_type = existing_user.user_type  
            return make_response(jsonify({"error": "User with same email already exists as a " + user_type}),400)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in registartion at line number',lNumber,'filename is :',fname,'-----------error is:',e)
        return make_response(jsonify({"error": str(e)}),400)

#FORGOT PASSWORD
@auth_bp.route('/forgotpassword/', methods=['POST'])
def forgotPassword():
    """
    User Forgot Password
    POST requests validate user email
    """
    try:
        post_data = request.get_json()
        email = post_data['email']
        if (email == ''):
            return make_response(jsonify({"error": "please pass email"}),400)
        is_valid = check_email(email)
        if not is_valid:
            return make_response(jsonify({"error": "please pass a valid email"}),400)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            name = existing_user.name
            token = generate_confirmation_token(email)
            confirm_url = url_for('auth_bp.reset_token', token=token, _external=True)
            subject = "Reset password email"
            send_password_reset_email(email, name, subject, confirm_url)
            existing_user.hashcode = token
            db.session.add(existing_user)
            db.session.commit()
            return make_response(jsonify({"success": "An email is sent to you for password reset.Please check your email"}),200)
        else:
            return make_response(jsonify({"error": "No such user exists"}),400)
    except Exception as e:
        #catch error and print line number where error occurs
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('Error occurs in forgot password at line number',lNumber,'filename is :',fname,'-----------error is:',e)
        return make_response(jsonify({"error": str(e)}),400)



#CONFIRM EMAIL
@auth_bp.route('/confirm/<token>', methods=['GET','POST'])
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        return make_response(jsonify({"error": 'The confirmation link is invalid or has expired'}),400)
    user_data = User.query.filter_by(email=email).first_or_404()
    if user_data:
        if user_data.is_verified:
            return make_response(jsonify({"error": 'Account already confirmed. Please login'}),400)
        else:
            user_data.is_verified = True
            db.session.add(user_data)
            db.session.commit()
            return make_response(jsonify({'success':'You have confirmed your account. Thanks!.Please login'}),200)


#RESET TOKEN CONFIRM
@auth_bp.route('/resetpassword/<token>', methods=['GET','POST'])
def reset_token(token):
    if request.method == 'POST':
        try:
            email = confirm_token(token)
        except:
            return make_response(jsonify({"error": "The confirmation link is invalid or has expired"}),400)
        try:
            user_exists = User.query.filter_by(hashcode=token).first()
            if user_exists:
                #valid token
                password = request.form.get('password')
                user_exists.set_password(password)
                user_exists.hashcode = ''
                db.session.add(user_exists)
                db.session.commit()
                flash('Password reset successfull')
                return redirect(request.url)
                # return make_response(jsonify({"success": 'Password Updated.You can Login now!'}),200)  
            else:
                return make_response(jsonify({"error": "no such user"}),400)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            lNumber = exc_tb.tb_lineno
            print('error at line',lNumber,'error is',e)
            return make_response(jsonify({"error": str(e)}),400)
    else:
        return render_template('password_reset.html')
        return make_response(jsonify({"success": "Please render form and post password "}),400)


#LOGIN
@auth_bp.route('/login/', methods=['POST'])
def login():
    """
    User Log-in
    POST requests validate and redirect user to dashboard.
    """
    # Bypass if user is logged in
    # if current_user.is_authenticated:
    #     return Response("{'success':'Member is already loggedin'}", status=200)  

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
        if user_instance is None:
            return make_response(jsonify({"error": 'please provide valid credentials'}),400)
        profile_instance = bool(Profile.query.filter_by(user_id=user_instance.id).first())
        if profile_instance == True:
            profile_exists = True
        if profile_instance == False:
            enq_profile_instance = bool(EnquirerProfile.query.filter_by(enquirer_id=user_instance.id).first())
            if enq_profile_instance == True:
                profile_exists = True
            else:
                profile_exists = False
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
            return make_response(jsonify({"access_token":access_token,"user": profile,"profile_exists":profile_exists}),200)
        else:
            return make_response(jsonify({"error": 'invalid credentials'}),400)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in login at line',lNumber,'error is',e)
        return make_response(jsonify({"error": str(e)}),400)


#LOGIN
@auth_bp.route('/getLoggedInUser/', methods=['GET'])
@jwt_required
def getLoggedInUser():
    try:
        current_user = get_jwt_identity()
        user_instance = User.query.get(current_user)
        if user_instance is None:
            return make_response(jsonify({"error": 'invalid token'}),400)
        profile_instance = bool(Profile.query.filter_by(user_id=user_instance.id).first())
        if profile_instance == True:
            profile_exists = True
        print('>>>>>>>>>>>>>',profile_instance)
        if profile_instance == False:
            enq_profile_instance = bool(EnquirerProfile.query.filter_by(enquirer_id=user_instance.id).first())
            if enq_profile_instance == True:
                profile_exists = True
            else:
                profile_exists = False
        get_user = User.query.get(user_instance.id)
        user_schema = UserSchema(many=False)
        profile = user_schema.dump(get_user)
        return make_response(jsonify({"user": profile,"profile_exists":profile_exists}),200)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lNumber = exc_tb.tb_lineno
        print('error in login at line',lNumber,'error is',e)
        return make_response(jsonify({"error": str(e)}),400)

# Endpoint for revoking the current users access token
@auth_bp.route('/logout/', methods=['DELETE'])
@jwt_required
def logout():
    jti = get_raw_jwt()['jti']
    blacklist.add(jti)
    return make_response(jsonify({"success": "logged out successfully"}),400)

######################################################################################################



