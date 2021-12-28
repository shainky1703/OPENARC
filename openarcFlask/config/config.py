"""Flask app configuration."""
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class Config:
    """Set Flask configuration from environment variables."""

    FLASK_APP = 'app.py'
    FLASK_ENV = environ.get('FLASK_ENV')

    # Flask-Assets
    LESS_BIN = environ.get('LESS_BIN')
    ASSETS_DEBUG = environ.get('ASSETS_DEBUG')
    LESS_RUN_IN_DEBUG = environ.get('LESS_RUN_IN_DEBUG')

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost/openarc_db"
    SQLALCHEMY_BINDS = {
    "jobs_db": "mysql+pymysql://root:root@localhost/openarc_jobs_db",
    "subscriptions_db" : "mysql+pymysql://root:root@localhost/openarc_subscriptions_db",
    "chats_db" : "mysql+pymysql://root:root@localhost/openarc_chats_db"
    }



    
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_POOL_TIMEOUT=300
    SQLALCHEMY_MAX_OVERFLOW = 100


    # Static Assets
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
