"""Database models."""
import datetime
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields
from services.Users.Member.models import *
from . import db
import enum
from datetime import date


now = datetime.datetime.now()


#Jobs Model
class Jobs(db.Model):
    """Jobs model."""

    __tablename__ = 'jobs'
    __bind_key__  = 'jobs_db' # read from database 'test1'
    __table_args__ = {'schema': 'openarc_jobs_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    business_name = db.Column(
        db.String(50),
        nullable=False
    )
    job_category = db.Column(
        db.String(20),
        nullable=False
    )
    job_description = db.Column(
        db.String(500),
        nullable=False
    )
    address = db.Column(
        db.String(100),
        nullable=False
    )
    city = db.Column(
        db.String(100),
        nullable=False
    )
    vacancies = db.Column(
        db.String(4),
        nullable=False
    )
    interested_count = db.Column(
        db.String(4),
        nullable=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    shift_start_date = db.Column(
        db.Date()
    )
    shift_end_date = db.Column(
        db.Date()
    )
    shift_start_time = db.Column(
        db.String(20)
    )
    shift_end_time = db.Column(
        db.String(20) 
    )      
    job_type = db.Column(
        db.String(20),
        nullable=True
    )
    shift_type = db.Column(
        db.String(20),
        nullable=True
    )
    budget = db.Column(
        db.String(20),
        nullable=True
    )
    emergency_rate = db.Column(
        db.String(20),
        nullable=True
    )
    contract = db.Column(
        db.String(50),
        nullable=True
    )
    posted_by = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
    bidding_started = db.Column(db.Boolean, nullable=False, default=False)
    is_draft = db.Column(db.Boolean, nullable=False, default=False)


class JobsSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = Jobs
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    business_name = fields.String(required=True)
    job_category = fields.String(required=True)
    job_type = fields.String(required=True)
    shift_type = fields.String(required=True)
    budget = fields.String(required=True)
    contract = fields.String(required=True)
    emergency_rate = fields.String(required=True)
    job_description = fields.String(required=True)
    vacancies = fields.String(required=True)
    interested_count = fields.String(required=False)
    created_at = fields.DateTime(required=False)
    shift_start_date = fields.Date(required=False)
    shift_end_date = fields.Date(required=False)
    shift_start_time = fields.String(required=False)
    shift_end_time = fields.String(required=False)
    updated_at = fields.DateTime(required=False)
    bidding_started = fields.Boolean(required=True)
    is_draft = fields.Boolean(required=True)
    city = fields.String(required=False)
    address = fields.String(required=False)


class AppliedJobStatusEnum(enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'
    interested = 'interested'

#Jobs Model
class AppliedJobs(db.Model):
    """Applied Jobs model."""

    __tablename__ = 'job_applications'
    __bind_key__  = 'jobs_db' # read from database 'test1'
    __table_args__ = {'schema': 'openarc_jobs_db'}
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
    pay_expected = db.Column(
        db.String(20),
        nullable=False
    )
    message = db.Column(
        db.String(500),
        nullable=False
    )
    application_status = db.Column(
        db.Enum(AppliedJobStatusEnum), 
        default=AppliedJobStatusEnum.pending,
        nullable=False
    )
    member_status = db.Column(
        db.String(50),
        nullable=True
    )
    funded_on = db.Column(
        db.DateTime(timezone=True), 
        default="1010-01-01 00:00:00",
    )
    funded_amount = db.Column(
        db.String(50),
        nullable=True
    )
    brokerage = db.Column(
        db.String(50),
        nullable=True
    )
    is_funded = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    job_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.jobs.id'))
    applied_by = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))


class AppliedJobsSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = AppliedJobs
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    pay_expected = fields.String(required=True)
    application_status = fields.String(required=True)
    message = fields.String(required=True)
    is_active = fields.Boolean(required=True)
    job_id = fields.String(required=True)
    applied_by = fields.String(required=True)
    created_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)
    member_status = fields.String(required=True)


    
#Started Jobs Logs Model
class StartedJobLogs(db.Model):
    """Started Jobs Logs  model."""

    __tablename__ = 'started_job_logs'
    __bind_key__  = 'jobs_db' # read from database 'test1'
    __table_args__ = {'schema': 'openarc_jobs_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    date = db.Column(
        db.Date(), 
        default=datetime.datetime.now
    )
    start_time = db.Column(
        db.Time(timezone=True), 
        nullable=True
    )
    end_time = db.Column(
        db.Time(timezone=True),
        nullable=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    hours = db.Column(
        db.String(20),
        nullable=True
    )
    after_hours = db.Column(
        db.String(20),
        nullable=True
    )
    amount = db.Column(
        db.String(20),
        nullable=True
    )
    member_status = db.Column(
        db.String(20),
        nullable=True
    )
    after_hours_reason = db.Column(
        db.String(200),
        nullable=True
    )
    amount = db.Column(
        db.String(20),
        nullable=True
    )
    after_hours_amount = db.Column(
        db.String(20),
        nullable=True
    )
    application_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.job_applications.id'))

#Payments Model
class JobPayments(db.Model):
    """Payments model."""

    __tablename__ = 'job_payments'
    __table_args__ = {'schema': 'openarc_jobs_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    work_status = db.Column(
        db.String(100),
        nullable=True
    )
    total_hours = db.Column(
        db.String(10),
        nullable=True
    )
    total_amount = db.Column(
        db.String(10),
        nullable=True
    )
    payment_status = db.Column(
        db.String(10),
        nullable=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
        )
    application_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.job_applications.id'))

#Reviews Model
class Reviews(db.Model):
    """Enquirer Reviews model."""

    __tablename__ = 'reviews'
    __bind_key__  = 'jobs_db' # read from database 'test1'
    __table_args__ = {'schema': 'openarc_jobs_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    member_review = db.Column(
        db.String(200),
        nullable=True
    )
    member_stars = db.Column(
        db.String(10),
        nullable=True
    )
    employer_review = db.Column(
        db.String(200),
        nullable=True
    )
    employer_stars = db.Column(
        db.String(10),
        nullable=True
    )
    application_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.job_applications.id'))
    member_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
    employer_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))

class ReviewsSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = Reviews
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    member_review = fields.String(required=True)
    member_stars = fields.String(required=True)
    employer_review = fields.String(required=True)
    employer_stars = fields.String(required=True)
    application_id = fields.String(required=True)
    member_id = fields.String(required=True)
    employer_id = fields.String(required=True)

#Disputes Model
class Disputes(db.Model):
    """Complaints model."""

    __tablename__ = 'disputes'
    __bind_key__  = 'jobs_db' # read from database 'test1'
    __table_args__ = {'schema': 'openarc_jobs_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    dispute_type = db.Column(
        db.String(30),
        nullable=False
    )
    amount = db.Column(
        db.String(300),
        nullable=False
    )
    description = db.Column(
        db.String(200),
        nullable=False
    )
    status = db.Column(
        db.String(10),
        nullable=False,
        default='Active'
    )
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), 
        default=datetime.datetime.now
    )
    submitted_by = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.jobs.id'))
    member_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))

class DisputesSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = Disputes
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    description = fields.String(required=True)
    title = fields.String(required=True)
    images = fields.String(required=True)
    submitted_by = fields.String(required=True)
    member_id = fields.String(required=True)
    job_id = fields.String(required=True)
    created_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)
    status = fields.String(required=True)

#Invites Model
class JobInvites(db.Model):
    """Invites model."""

    __tablename__ = 'JobInvites'
    __bind_key__  = 'jobs_db' # read from database 'test1'
    __table_args__ = {'schema': 'openarc_jobs_db'}
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
    status = db.Column(
        db.String(10),
        nullable=False,
        default='Pending'
    )
    guard_id = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.jobs.id'))


class JobInvitesSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = JobInvites
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    guard_id = fields.String(required=True)
    status = fields.String(required=True)
    job_id = fields.String(required=True)
    created_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)

#Enquirer Fee
class EnquirerFees(db.Model):
    """Enquirer Fee model."""

    __tablename__ = 'enquirerFee'
    __bind_key__  = 'jobs_db' # read from database 'test1'
    __table_args__ = {'schema': 'openarc_jobs_db'}
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
    aos_standard_addition_per_hour = db.Column(
        db.String(5),
        nullable = False
    )
    aos_one_off_misc_payment = db.Column(
        db.String(5),
        nullable = False
    )
    admin_charges_per_hour_pounds = db.Column(
        db.String(5),
        nullable = False
    )
    bidding_fees_per_hour_pence = db.Column(
        db.String(5),
        nullable = False
    )
    vat = db.Column(
        db.String(5),
        nullable = False
    )


#Member Fee
class MemberFees(db.Model):
    """Member Fee model."""

    __tablename__ = 'memberFee'
    __bind_key__  = 'jobs_db' # read from database 'test1'
    __table_args__ = {'schema': 'openarc_jobs_db'}
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
    aos_standard_addition_per_hour = db.Column(
        db.String(5),
        nullable = False
    )
    aos_arrears_payments = db.Column(
        db.String(5),
        nullable = False
    )
    aos_one_off_deductions = db.Column(
        db.String(5),
        nullable = False
    )
    admin_charges_per_hour_pence = db.Column(
        db.String(5),
        nullable = False
    )
    
#Saved Jobs
class SavedJobs(db.Model):
    """Save Jobs model."""

    __tablename__ = 'savedJobs'
    __bind_key__  = 'jobs_db' # read from database 'test1'
    __table_args__ = {'schema': 'openarc_jobs_db'}
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
    saved_by = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('openarc_jobs_db.jobs.id'))


