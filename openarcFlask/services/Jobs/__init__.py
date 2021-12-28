from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from flask_mail import Mail
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from services.Users import db
from services.Users import secret_key
import datetime
from flask_jwt_extended import JWTManager
import datetime
from os import environ, path
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, make_response, Response

expires = datetime.timedelta(days=365)

login_manager = LoginManager()

mail = Mail()


def create_app():
    """Construct the core app object."""
    app = Flask(__name__, instance_relative_config=False, static_url_path='/static', template_folder="../../templates")
    app.config.update(
    DEBUG=True,
    #EMAIL SETTINGS
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME = 'arcopenspace@gmail.com',
    MAIL_PASSWORD = '20OpenArc20'
    )
    app.secret_key = secret_key
    mail.init_app(app)
    cors = CORS(app)
    JWT_SECRET_KEY = environ.get('JWT_SECRET_KEY')
    JWT_TOKEN_LOCATION = environ.get('JWT_TOKEN_LOCATION')
    JWT_ACCESS_TOKEN_EXPIRES = False
    jwt = JWTManager(app)

    #Swagger
    SWAGGER_URL = '/swagger'
    API_URL = '/static/swagger.yaml'
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': 'Open-Arc-Jobs'
        }
    )
    
    # @jwt.invalid_token_loader
    # def invalid_token_loader(callback):
    #     """
    #     This decorator sets the callback function that will be called if an
    #     invalid JWT attempts to access a protected endpoint. The default
    #     implementation will return a 422 status code with the JSON:

    #     {"msg": "<error description>"}

    #     *HINT*: The callback must be a function that takes only **one** argument, which is
    #     a string which contains the reason why a token is invalid, and returns
    #     a *Flask response*.
    #     """
    #     invalid_token_callback = callback
    #     return make_response(jsonify({"error":"Please Login Again"}),400)

    # def callback(reason):
    #     response = 'app restarts'
    #     return response

    # Application Configuration
    app.config.from_object('config.config.Config')

    # Initialize Plugins
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from . import job_routes

        # Register Blueprints
        app.register_blueprint(job_routes.jobs_main_bp)
        app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

        # Create Database Models
        from .models import Jobs, MemberFees,EnquirerFees
        db.create_all(bind=['jobs_db'])
        try:
            member_fee_exists = bool(MemberFees.query.all())
            if not member_fee_exists:
                print('not exists')
                member_fee_profile = MemberFees(
                        aos_standard_addition_per_hour = '0',
                        aos_arrears_payments = '0',
                        aos_one_off_deductions = '0',
                        admin_charges_per_hour_pence = '25'
                    )
                db.session.add(member_fee_profile)
                db.session.commit()
            else:
                pass
        except Exception as e:
            print('error occurs in member fee model',e)
        try:
            enquirer_fee_exists = bool(EnquirerFees.query.all())
            if not enquirer_fee_exists:
                print('not exists11111')
                enquirer_fee_profile = EnquirerFees(
                        aos_standard_addition_per_hour = '0',
                        aos_one_off_misc_payment = '0',
                        bidding_fees_per_hour_pence = '10',
                        admin_charges_per_hour_pounds = '1.5',
                        vat = '20'
                    )
                db.session.add(enquirer_fee_profile)
                db.session.commit()
            else:
                pass
            
        except Exception as e:
            print('error occurs in enquirer fee model',e)
        return app