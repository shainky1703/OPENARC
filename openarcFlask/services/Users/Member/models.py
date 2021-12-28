"""Database models."""
from services.Users import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields
from werkzeug.security import safe_str_cmp
from itsdangerous import URLSafeTimedSerializer
from services.Jobs.models import *

serializer = URLSafeTimedSerializer('serializer_secret')
#User Model
class User(UserMixin, db.Model):
    """User account model."""

    __tablename__ = 'users'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String(40),
        unique=False,
        nullable=False
    )
    email = db.Column(
        db.String(40),
        unique=True,
        nullable=False
    )
    password = db.Column(
        db.String(200),
        primary_key=False,
        unique=False,
        nullable=False
	)
    hashcode = db.Column(
        db.String(200),
        primary_key=False,
        unique=False,
        nullable=True
    )
    badge_number = db.Column(
        db.String(200),
        primary_key=False,
        unique=False,
        nullable=True
    )
    expiry_date = db.Column(
        db.Date()
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    user_type = db.Column(
        db.String(20),
        primary_key=False,
        unique=False,
        nullable=False
        )
    device_type = db.Column(
        db.String(20),
        primary_key=False,
        unique=False,
        nullable=False
        )
    device_id = db.Column(
        db.String(500),
        unique=False,
        nullable=False
        )
    is_verified = db.Column(db.Boolean, nullable=False, default=False)

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(
            password,
            method='sha256'
        )

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)


    def get_auth_token(self, email, password):
        data = [str(self.email), self.password]
        return serializer.dumps(data, salt='serializer_secret')

    def __repr__(self):
        return '<User {}>'.format(self.email)


class UserSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = User
        sqla_session = db.session
        load_instance = True
    id = fields.String(dump_only=True)
    email = fields.String(required=True)
    created_at = fields.String(required=True)
    updated_at = fields.String(required=True)
    user_type = fields.String(required=True)
    device_type = fields.String(required=True)
    device_id = fields.String(required=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    



#Profile Model
class Profile(db.Model):
    """User Profile model."""

    __tablename__ = 'usersProfile'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    profile_pic = db.Column(
        db.String(100),
        nullable=False
    )
    hourly_rate = db.Column(
        db.String(100),
        nullable=False
    )
    contact = db.Column(
        db.String(30),
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
        db.String(40),
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
    documents = db.Column(
        db.String(500),
        nullable=True
    )
    unavailability = db.Column(
        db.String(500),
        unique=True,
        nullable=True
    )
    about = db.Column(
        db.String(500),
        nullable=True
    )
    pin_location = db.Column(
        db.String(100),
        nullable=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
    drive = db.Column(db.Boolean, nullable=False, default=False)



class ProfileSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = Profile
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    documents = fields.String(required=True)
    profile_pic = fields.String(required=True)
    contact = fields.String(required=True)
    address = fields.String(required=True)
    city = fields.String(required=True)
    postal_code = fields.String(required=True)
    unavailability = fields.String(required=True)
    user_id = fields.String(required=False)
    created_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)
    about = fields.String(required=False)
    pin_location= fields.String(required=False)




#StripeDetails Model
class StripeDetails(db.Model):
    """Stripe Profile model."""

    __tablename__ = 'stripe_details'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    routing_number = db.Column(
        db.String(100),
        nullable=False
    )
    account_number = db.Column(
        db.String(100),
        nullable=False
    )
    first_name = db.Column(
        db.String(20),
        nullable=False
    )
    last_name = db.Column(
        db.String(20),
        nullable=False
    )
    phone = db.Column(
        db.String(15),
        nullable=False
    )
    dob_day = db.Column(
        db.String(5),
        nullable=False
    )
    dob_month = db.Column(
        db.String(5),
        nullable=False
    )
    dob_year = db.Column(
        db.String(5),
        nullable=False
    )
    address_line_1 = db.Column(
        db.String(100),
        nullable=False
    )
    address_line_2 = db.Column(
        db.String(100),
        nullable=False
    )
    city = db.Column(
        db.String(20),
        nullable=False
    )
    state = db.Column(
        db.String(20),
        nullable=False
    )
    zip_code = db.Column(
        db.String(40),
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
    account_id = db.Column(
        db.String(40),
        nullable=True
    )
    connected_account = db.Column(db.Boolean, nullable=False, default=False)


#Payments Model
class Payments(db.Model):
    """Payments model."""

    __tablename__ = 'payments'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    amount_paid = db.Column(
        db.String(100),
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
    application_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.job_applications.id'))

#SavedMembers Model
class SavedMembers(db.Model):
    """SavedMembers model."""

    __tablename__ = 'saved_members'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    member_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
    saved_by = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))


#Member Disputes Model
class MemberDisputes(db.Model):
    """MemberDisputes model."""

    __tablename__ = 'member_disputes'
    __table_args__ = {'schema': 'openarc_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
        )
    title = db.Column(
        db.String(30),
        nullable=False
    )
    details = db.Column(
        db.String(100),
        nullable=False
    )
    images = db.Column(
        db.String(100),
        nullable=True
    )
    documents = db.Column(
        db.String(100),
        nullable=True
    )
    status = db.Column(
        db.String(20),
        nullable=False
    )
    job_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.jobs.id'))
    submitted_by = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
    