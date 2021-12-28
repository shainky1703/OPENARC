"""Database models."""
from services.Users import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields


#Profile Model
class EnquirerProfile(db.Model):
    """Enquirer Profile model."""

    __tablename__ = 'enquirerProfile'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    about = db.Column(
        db.String(400),
        nullable=True
    )
    registration_number = db.Column(
        db.String(20),
        nullable=True
    )
    acs_reference_number = db.Column(
        db.String(20),
        nullable=True
    )
    company_logo = db.Column(
        db.String(50),
        nullable=False
    )
    contact = db.Column(
        db.String(25),
        nullable=False
    )
    company_contact = db.Column(
        db.String(25),
        nullable=False
    )
    address = db.Column(
        db.String(100),
        nullable=False
    )
    city = db.Column(
        db.String(50),
        nullable=False
    )
    postal_code = db.Column(
        db.String(10),
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
        )
    enquirer_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))

    def __repr__(self):
        return '<EnquirerProfile {}>'.format(self.id)

class EnquirerProfileSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = EnquirerProfile
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    about = fields.String(required=True)
    registration_number = fields.String(required=True)
    acs_reference_number = fields.String(required=True)
    company_logo = fields.String(required=True)
    contact = fields.String(required=True)
    company_contact = fields.String(required=True)
    address = fields.String(required=True)
    address = fields.String(required=True)
    city = fields.String(required=True)
    postal_code = fields.String(required=False)
    created_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)

#Funds Model
class Fundings(db.Model):
    """User Fundings model."""

    __tablename__ = 'usersFundings'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    reference = db.Column(
        db.String(200),
        nullable=False
    )
    amount = db.Column(
        db.String(50),
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
        )
    user_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))

    def __repr__(self):
        return '<EnquirerProfile {}>'.format(self.id)

#Wallet Model
class Wallet(db.Model):
    """User Wallet model."""

    __tablename__ = 'usersWallet'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    balance = db.Column(
        db.String(50),
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
        )
    user_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))



class WalletSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = Wallet
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    balance = fields.String(required=True)
    created_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)

#Payments Model
class UserPayments(db.Model):
    """User Payments model."""

    __tablename__ = 'usersPayments'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    amount = db.Column(
        db.String(50),
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
        )
    medium = db.Column(
            db.String(50),
            nullable=False
    )
    reference = db.Column(
            db.String(50),
            nullable=False
    )
    session_id = db.Column(
            db.String(100),
            nullable=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.jobs.id'))


class UserPaymentsSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = UserPayments
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    amount = fields.String(required=True)
    created_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)
    medium = fields.String(required=True)
    reference = fields.String(required=True)


#Enquirer Notification Model
class EnquirerNotification(db.Model):
    """Enquirer Notification model."""

    __tablename__ = 'employerNotifications'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    body = db.Column(
        db.String(500),
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    status = db.Column(
        db.String(50),
        nullable=False
    ) 
    employer_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
