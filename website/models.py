from . import db
from sqlalchemy import Numeric

from flask_login import UserMixin

from datetime import datetime, timedelta

from decimal import Decimal, InvalidOperation
def to_decimal_3(value):
    try:
        return Decimal(value).quantize(Decimal('0.001'))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0.000')

def current_utc_time():
    return datetime.utcnow() + timedelta(hours=3)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), unique=True)
    last_name = db.Column(db.String())
    first_name = db.Column(db.String())
    patronymic_name = db.Column(db.String())
    post = db.Column(db.String())
    phone = db.Column(db.String(), unique=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    password = db.Column(db.String())
    is_admin = db.Column(db.Boolean, default=False)
    is_auditor = db.Column(db.Boolean, default=False)
    last_active = db.Column(db.DateTime, nullable=False, default=current_utc_time)
    begin_time = db.Column(db.DateTime, nullable=False, default=current_utc_time)
    
    organization = db.relationship('Organization', backref='users')
    plans = db.relationship('Plan', backref='user', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")
    
    
    
class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    okpo = db.Column(db.String, unique=True, nullable=False)
    ynp = db.Column(db.String(), nullable=True)
    ministry = db.Column(db.String()) 
    is_active = db.Column(db.Boolean, default=True)

class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True)
    
    okpo = db.Column(db.String, default=None)
    name_org = db.Column(db.String, default=None)
    
    year = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(), nullable=False)
    fio = db.Column(db.String(), nullable=False)
    phone = db.Column(db.String(), nullable=False)
    
    begin_time = db.Column(db.DateTime, nullable=False, default=current_utc_time)
    change_time = db.Column(db.DateTime, nullable=False, default=current_utc_time)
    sent_time = db.Column(db.DateTime)
    audit_time = db.Column(db.DateTime)
    
    energy_saving = db.Column(Numeric(scale=3))
    share_fuel = db.Column(Numeric(scale=3))
    saving_fuel = db.Column(Numeric(scale=3))
    share_energy = db.Column(Numeric(scale=3))
    
    is_draft = db.Column(db.Boolean, default=True)
    is_control = db.Column(db.Boolean, default=False)
    is_sent = db.Column(db.Boolean, default=False)
    is_error = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    
    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))  
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  

    afch = db.Column(db.Boolean, default=False)

    tickets = db.relationship('Ticket', back_populates='plan', lazy=True, cascade="all, delete-orphan")
    econ_measures = db.relationship('EconMeasure', back_populates='plan', lazy=True, cascade="all, delete-orphan")
    econ_execes = db.relationship('EconExec', back_populates='plan', lazy=True, cascade="all, delete-orphan")
    indicators_usage = db.relationship('IndicatorUsage', back_populates='plan', lazy=True, cascade="all, delete-orphan")

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    begin_time = db.Column(db.DateTime, default=current_utc_time)
    luck = db.Column(db.Boolean, default=False)
    is_owner = db.Column(db.Boolean, default=False)
    note = db.Column(db.String(500), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))
    plan = db.relationship("Plan", back_populates="tickets")

class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(400), unique=True, nullable=False)
    name = db.Column(db.String(400), unique=True, nullable=False)
 
class Direction(db.Model):
    __tablename__ = 'directions'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(400))
    name = db.Column(db.String(400))
    id_unit = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    
    is_local = db.Column(db.Boolean)
    DateStart = db.Column(db.DateTime)
    DateEnd = db.Column(db.DateTime)
    unit = db.relationship('Unit', backref='directions')

class EconMeasure(db.Model):
    __tablename__ = 'econ_measures'
    id = db.Column(db.Integer, primary_key = True)
    id_plan = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    id_direction = db.Column(db.Integer, db.ForeignKey('directions.id'), nullable=False)
    
    year_econ = db.Column(Numeric(scale=3))
    estim_econ = db.Column(Numeric(scale=3))
        
    order = db.Column(db.Integer, default = None)

    plan = db.relationship("Plan", back_populates="econ_measures")
    direction = db.relationship('Direction', backref='econ_measures')
    econ_execes = db.relationship('EconExec', back_populates='econ_measures', lazy=True, cascade="all, delete-orphan")

    def as_dict(self):
        return {
            'id': self.id,
            'id_plan': self.id_plan,
            'id_direction': self.id_direction,
            'year_econ': self.year_econ,
            'estim_econ': self.estim_econ
        }


class EconExec(db.Model):
    __tablename__ = 'econ_execes'
    id = db.Column(db.Integer, primary_key = True)
    id_measure = db.Column(db.Integer, db.ForeignKey('econ_measures.id'), nullable=False)
    id_plan = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)

    name = db.Column(db.String(4000), nullable=False)
    Volume = db.Column(db.Integer)
    EffTut = db.Column(Numeric(scale=3))
    EffRub = db.Column(Numeric(scale=3))
    ExpectedQuarter = db.Column(db.Integer)
    EffCurrYear = db.Column(Numeric(scale=3))
    Payback = db.Column(db.Integer)
    VolumeFin = db.Column(Numeric(scale=3))
    BudgetState = db.Column(Numeric(scale=3))
    BudgetRep = db.Column(Numeric(scale=3))
    BudgetLoc = db.Column(Numeric(scale=3))
    BudgetOther = db.Column(Numeric(scale=3))
    MoneyOwn = db.Column(Numeric(scale=3))
    MoneyLoan = db.Column(Numeric(scale=3))
    MoneyOther = db.Column(Numeric(scale=3))
 
    is_local = db.Column(db.Boolean)
    is_corrected = db.Column(db.Boolean)
    order = db.Column(db.Integer, default = None)

    plan = db.relationship("Plan", back_populates="econ_execes")
    econ_measures = db.relationship("EconMeasure", back_populates="econ_execes")
    
    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'Volume': self.Volume,
            'EffTut': self.EffTut,
            'EffRub': self.EffRub,
            'ExpectedQuarter': self.ExpectedQuarter,
            'EffCurrYear': self.EffCurrYear,
            'Payback': self.Payback,
            'VolumeFin': self.VolumeFin,
            'BudgetState': self.BudgetState,
            'BudgetRep': self.BudgetRep,
            'BudgetLoc': self.BudgetLoc,
            'BudgetOther': self.BudgetOther,
            'MoneyOwn': self.MoneyOwn,
            'MoneyLoan': self.MoneyLoan,
            'MoneyOther': self.MoneyOther
        }

class Indicator(db.Model):
    __tablename__ = 'indicators' 
    id = db.Column(db.Integer, primary_key=True)
    id_unit = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    code = db.Column(db.String(400))
    name = db.Column(db.String(400))
    CoeffToTut = db.Column(Numeric(scale=3))

    IsMandatory = db.Column(db.Boolean)
    IsSummary = db.Column(db.Boolean)
    IsSendRealUnit = db.Column(db.Boolean)
    IsSelfProd = db.Column(db.Boolean)
    IsLocal = db.Column(db.Boolean)
    IsRenewable = db.Column(db.Boolean)

    Group = db.Column(db.Integer)
    RowN = db.Column(db.Integer)

    DateStart = db.Column(db.DateTime)
    DateEnd = db.Column(db.DateTime)
    id_indicator_parent = db.Column(db.Integer)
    unit = db.relationship('Unit', backref='indicators')
    indicators_usage = db.relationship("IndicatorUsage", back_populates="indicator")

class IndicatorUsage(db.Model):
    __tablename__ = 'indicators_usage'
    id = db.Column(db.Integer, primary_key=True)
    id_indicator = db.Column(db.Integer, db.ForeignKey('indicators.id'), nullable=False)
    id_plan = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    QYearPrev = db.Column(Numeric(scale=3))
    QYearCurr = db.Column(Numeric(scale=3))
    QYearNext = db.Column(Numeric(scale=3))

    indicator = db.relationship("Indicator", back_populates="indicators_usage")
    plan = db.relationship("Plan", back_populates="indicators_usage")

    def as_dict(self):
        return {
            'id': self.id,
            'id_indicator': self.id_indicator,
            'id_plan': self.id_plan,
            'QYearPrev': self.QYearPrev,
            'QYearCurr': self.QYearCurr,
            'QYearNext': self.QYearNext,
            'CoeffToTut': self.indicator.CoeffToTut
        }
        
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True, nullable=False)
    message = db.Column(db.String(140), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=current_utc_time)
