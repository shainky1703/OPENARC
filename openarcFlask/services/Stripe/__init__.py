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
    app = Flask(__name__, instance_relative_config=False, static_url_path='/static')
    app.config.update(
    DEBUG=True,
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
            'app_name': 'Open-Arc-Stripe'
        }
    )
    
    @jwt.invalid_token_loader
    def invalid_token_loader(callback):
        
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
        from . import stripe_routes

        # Register Blueprints
        app.register_blueprint(stripe_routes.stripe_main_bp)
        app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

        # Create Database Models
        db.create_all()

        return app