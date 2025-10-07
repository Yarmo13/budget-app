from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    expenses = relationship('Expense', back_populates='user', cascade='all, delete-orphan')
    budgets = relationship('Budget', back_populates='user', cascade='all, delete-orphan')
    settings = relationship('Settings', back_populates='user', cascade='all, delete-orphan')
    savings = relationship('Saving', back_populates='user', cascade='all, delete-orphan')
    savings_goals = relationship('SavingsGoal', back_populates='user', cascade='all, delete-orphan')
    recurring_expenses = relationship('RecurringExpense', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship('User', back_populates='expenses')

class Budget(Base):
    __tablename__ = 'budgets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category = Column(String(100), nullable=False)
    monthly_limit = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship('User', back_populates='budgets')

class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship('User', back_populates='settings')

class Saving(Base):
    __tablename__ = 'savings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship('User', back_populates='savings')

class SavingsGoal(Base):
    __tablename__ = 'savings_goals'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(200), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationship
    user = relationship('User', back_populates='savings_goals')

class RecurringExpense(Base):
    __tablename__ = 'recurring_expenses'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    frequency = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # Optional, for subscriptions that will end
    day_of_month = Column(Integer)  # For monthly (1-31)
    day_of_week = Column(Integer)  # For weekly (0=Monday, 6=Sunday)
    last_generated = Column(Date)  # Track when we last created an expense from this
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship('User', back_populates='recurring_expenses')

# Database initialization
engine = create_engine('sqlite:///budget.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()
