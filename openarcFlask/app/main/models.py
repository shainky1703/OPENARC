"""Database models."""
import datetime
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields
from services.Users.Member.models import *
from app import db
import enum



now = datetime.datetime.now()


class Session(db.Model):
    """Chats model."""

    __tablename__ = 'sessions'
    __table_args__ = {'schema': 'openarc_chats_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    user = db.Column(
        db.Integer(),
        nullable=False)
    session_id = db.Column(
        db.String(15),
        nullable=False
    )

class SessionSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = Session
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    user = fields.String(required=True)

#Chats History Model
class ChatHistory(db.Model):
    """Chats model."""

    __tablename__ = 'chats_history'
    __table_args__ = {'schema': 'openarc_chats_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    message = db.Column(
        db.String(500),
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    sent_by = db.Column(
        db.Integer(),
        nullable=False)
    sent_to = db.Column(
        db.Integer(),
        nullable=False)
    document = db.Column(
        db.String(500),
        nullable=True
    )



class ChatHistorySchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = ChatHistory
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    message = fields.String(required=True)
    sent_by = fields.String(required=True)
    document = fields.String(required=True)
    sent_to = fields.String(required=True)
    created_at = fields.DateTime(required=False)


