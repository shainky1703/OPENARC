"""Database models."""
import datetime
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields
from services.Users.Member.models import *
from . import db
import enum



now = datetime.datetime.now()


#SubscriptionPlans Model
class SubscriptionPlans(db.Model):
    """SubscriptionPlans model."""

    __tablename__ = 'subscription_plans'
    __bind_key__  = 'subscriptions_db' 
    __table_args__ = {'schema': 'openarc_subscriptions_db'}
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    plan_name = db.Column(
        db.String(50),
        nullable=False
    )
    plan_type = db.Column(
        db.String(50),
        nullable=False
    )
    description = db.Column(
        db.String(200),
        nullable=True
    )
    discount = db.Column(
        db.String(200),
        nullable=True
    )
    monthly_price = db.Column(
        db.String(20),
        nullable=True
    )
    monthly_payment = db.Column(
        db.String(20),
        nullable=True
    )
    yearly_price = db.Column(
        db.String(200),
        nullable=True
    )
    yearly_payment = db.Column(
        db.String(20),
        nullable=True
    )
    reconnection_fees = db.Column(
        db.String(200),
        nullable=True
    )
    link_up_charge = db.Column(
        db.String(200),
        nullable=True
    )
    bidding_fees = db.Column(
        db.String(200),
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
    free_days = db.Column(
        db.String(20),
        nullable=True
    )



class PaymentStatusEnum(enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'

#Subscriptions Model
class Subscriptions(db.Model):
    """Subscriptions model."""

    __tablename__ = 'subscriptions'
    __bind_key__  = 'subscriptions_db' 
    __table_args__ = {'schema': 'openarc_subscriptions_db'}
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
    payment_date = db.Column(
        db.DateTime(timezone=True), 
        nullable=True
    )
    payment_status = db.Column(
        db.Enum(PaymentStatusEnum), 
        default=PaymentStatusEnum.pending,
        nullable=False
    )
    billing_cycle = db.Column(
        db.String(20),
        nullable=True
    )
    plan_id = db.Column(db.Integer, db.ForeignKey('openarc_subscriptions_db.subscription_plans.id', ondelete='SET NULL'), nullable=True)
    user = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id',ondelete='SET NULL'), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    is_cancelled = db.Column(db.Boolean, nullable=False, default=False)


        
class SubscriptionsSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = Subscriptions
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    plan = fields.String(required=True)
    billing_cycle = fields.String(required=True)
    payment_status = fields.String(required=True)
    created_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)
    is_active = fields.Boolean(required=True)
    is_cancelled = fields.Boolean(required=True)


#Cards Model
class Cards(db.Model):
    """Cards model."""

    __tablename__ = 'cards'
    __bind_key__  = 'subscriptions_db' 
    __table_args__ = {'schema': 'openarc_subscriptions_db'}
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
    card_number = db.Column(
        db.String(20),
        nullable=False
    )
    name_on_card = db.Column(
        db.String(20),
        nullable=False
    )
    expiry_date = db.Column(
        db.String(20),
        nullable=False
    )
    card_type = db.Column(
        db.String(20),
        nullable=False
    )
    cvv = db.Column(
        db.String(5),
        nullable=False
    )
    user = db.Column(db.Integer, db.ForeignKey('openarc_db.users.id',ondelete='SET NULL'), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


        
class CardsSchema(ModelSchema):
    class Meta(ModelSchema.Meta):
        model = Cards
        sqla_session = db.session
        include_fk = True
        load_instance = True
    id = fields.String(dump_only=True)
    user = fields.String(required=True)
    card_number = fields.String(required=True)
    cvv = fields.String(required=True)
    name_on_card = fields.String(required=True)
    expiry_date = fields.String(required=True)
    created_at = fields.DateTime(required=False)
    updated_at = fields.DateTime(required=False)
    is_active = fields.Boolean(required=True)


