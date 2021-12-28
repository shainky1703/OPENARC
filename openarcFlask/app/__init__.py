from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS

socketio = SocketIO()
db = SQLAlchemy()

def create_app(debug=True):
    """Create an application."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/openarc_chats_db'
    db = SQLAlchemy(app)
    db.init_app(app) 
    cors = CORS(app,resources={r"/*":{"origins":"*"}})
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'
    app.config["SQLALCHEMY_POOL_SIZE"] = 20
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

    #Swagger
    SWAGGER_URL = '/swagger'
    API_URL = '/static/swagger.yaml'
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': 'Open-Arc-ChatsHistory'
        }
    )

    with app.app_context():
        from .main import main as main_blueprint
        from app.main import models
        app.register_blueprint(main_blueprint)
        socketio.init_app(app)
        db.create_all()
        return app

