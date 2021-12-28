"""Initialize app."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from flask_mail import Mail
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import datetime
from os import environ, path
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, make_response, Response
from flask_migrate import Migrate

expires = datetime.timedelta(days=365)
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
secret_key = os.urandom(24)


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
    MAIL_PASSWORD = '20OpenArc20',
    MAIL_DEFAULT_SENDER = 'validation@arcopenspace.com'
    )
    app.static_folder = 'static'
    mail = Mail(app)
    app.secret_key = secret_key
    mail.init_app(app)
    cors = CORS(app)
    login_manager.init_app(app)
    JWT_SECRET_KEY = environ.get('JWT_SECRET_KEY')
    JWT_TOKEN_LOCATION = environ.get('JWT_TOKEN_LOCATION')
    JWT_ACCESS_TOKEN_EXPIRES = False
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    jwt = JWTManager(app)
    migrate = Migrate(app, db)



    @jwt.token_in_blacklist_loader
    def check_if_token_in_blacklist(decrypted_token):
        jti = decrypted_token['jti']
        return jti in blacklist


    #Swagger
    SWAGGER_URL = '/swagger'
    API_URL = '/static/swagger.yaml'
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': 'Open-Arc-Users'
        }
    )
    


    # Application Configuration
    app.config.from_object('config.config.Config')

    # Initialize Plugins
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from services.Users.Member import routes
        from services.Users.Member import auth
        from services.Users.Enquirer import enq_auth
        from services.Users.Enquirer import web_routes
        from services.Users.Enquirer import enq_routes 
        from services.Users.Admin import admin_routes
        from services.Users.Member import models

        # Register Blueprints
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(enq_auth.enq_auth_bp)
        app.register_blueprint(web_routes.web_routes_bp)
        app.register_blueprint(enq_routes.enq_main_bp)
        app.register_blueprint(admin_routes.admin_main_bp)
        app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

        # Create Database Models
        # db.create_all()

        return app