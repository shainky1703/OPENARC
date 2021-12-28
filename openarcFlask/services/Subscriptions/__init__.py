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
import braintree
from flask import Blueprint, request, jsonify, make_response, Response


expires = datetime.timedelta(days=365)

login_manager = LoginManager()

mail = Mail()

def create_app():
    """Construct the core app object."""
    app = Flask(__name__, instance_relative_config=False, static_url_path='/static')
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
            'app_name': 'Open-Arc-Subscriptions'
        }
    )
    

    @jwt.invalid_token_loader
    def invalid_token_loader(callback):
        """
        This decorator sets the callback function that will be called if an
        invalid JWT attempts to access a protected endpoint. The default
        implementation will return a 422 status code with the JSON:

        {"msg": "<error description>"}

        *HINT*: The callback must be a function that takes only **one** argument, which is
        a string which contains the reason why a token is invalid, and returns
        a *Flask response*.
        """
        invalid_token_callback = callback
        return make_response(jsonify({"error":"Please Login Again"}),400)

    def callback(reason):
        response = 'app restarts'
        return response
        
    # Application Configuration
    app.config.from_object('config.config.Config')

    # Initialize Plugins
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from . import subscription_routes

        #Register Blueprints
        app.register_blueprint(subscription_routes.subscription_main_bp)
        app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

        # Create Database Models
        from .models import SubscriptionPlans
        db.create_all(bind=['subscriptions_db'])
        try:
            tables_exists = bool(SubscriptionPlans.query.filter_by(plan_name='Basic').first())
            if tables_exists == False:
                print('will create tables now')
                plan_profile_1 = SubscriptionPlans(
                        plan_name = "Enquirer",
                        plan_type = "Enquirer",
                        description = "Basic Plan for Enquirer",
                        discount = "SAVE 54%",
                        monthly_price = "£10+VAT",
                        monthly_payment = "£12",
                        yearly_price = "£100+VAT",
                        yearly_payment = "£120",
                        reconnection_fees = "None",
                        link_up_charge = "25p per hour",
                        bidding_fees = "10p extra per hour",
                        free_days = 'None'
                    )
                plan_profile_2 = SubscriptionPlans(
                        plan_name = "Gold Enquirer",
                        plan_type = "Enquirer",
                        description = "Gold Plan for Enquirer",
                        discount = "SAVE 42%",
                        monthly_price = "£12+VAT",
                        monthly_payment = "£14.4",
                        yearly_price = "£120+VAT",
                        yearly_payment = "£144",
                        reconnection_fees = "None",
                        link_up_charge = "27.5p",
                        bidding_fees = "10p extra per hour",
                        free_days = 'None'
                    )
                plan_profile_3 = SubscriptionPlans(
                        plan_name = "Basic",
                        plan_type = "Member",
                        description = "Basic Plan for Member",
                        discount = "SAVE 54%",
                        monthly_price = "£12.50 Flat",
                        monthly_payment = "£12.50",
                        yearly_price = "First year £105 2nd year £150",
                        yearly_payment = "£105,£150",
                        reconnection_fees = "£5 after 3 months of none use",
                        link_up_charge = "None",
                        bidding_fees = "None",
                        free_days = 'None'
                    )
                plan_profile_4 = SubscriptionPlans(
                        plan_name = "Dove",
                        plan_type = "Member",
                        description = "Dove Plan for Member",
                        discount = "SAVE 42%",
                        monthly_price = "£15",
                        monthly_payment = "£15",
                        yearly_price = "£150",
                        yearly_payment = "£150",
                        reconnection_fees = "None",
                        link_up_charge = "None",
                        bidding_fees = "None",
                        free_days = 'None'
                    )
                plan_profile_5 = SubscriptionPlans(
                        plan_name = "Free",
                        plan_type = "All",
                        description = "Free Trial Plan for Users",
                        discount = "FREE TRIAL",
                        monthly_payment = "£00.0 Flat",
                        yearly_price = "None",
                        yearly_payment = "first 3 mos.",
                        reconnection_fees = "None",
                        link_up_charge = "None",
                        bidding_fees = "None",
                        free_days = '90'
                    )
                db.session.add(plan_profile_1)
                db.session.add(plan_profile_2)
                db.session.add(plan_profile_3)
                db.session.add(plan_profile_4)
                db.session.add(plan_profile_5)
                db.session.commit()
            else:
                pass
        except Exception as e:
            print('error ocurs',e)

        return app