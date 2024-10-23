# Direct code to connect to database. Anywhere 'user' is a parameter,
# it means the user's email as a string.

from sqlalchemy import create_engine, Column, String, Text, JSON, ARRAY, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
import requests
import uuid

from config import db_connector, db_name, environment

from google_secrets import get_secret

db_ip = get_secret("db_ip")
db_password = get_secret("db_password")
db_user = "dayscape"

db_url = f'postgresql://{db_user}:{db_password}@{db_ip}/{db_name}'

# SQLAlchemy setup code
# Create an engine
engine = create_engine(db_url)
# Sqlalchemy ORM ( https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping )
Base = declarative_base()
# Bind the engine to the Base class to start using it
Base.metadata.bind = engine
# https://docs.sqlalchemy.org/en/20/orm/session_basics.html
Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
# variable to hold session. In SQLAlchemy, the session keeps track of
# all changes, acts as a staging area for pending changes to objects.
  session = Session()
  try:
    yield session
    session.commit()
  except Exception as e:
    session.rollback()
    raise
  finally:
    session.close()

class Trip(Base):
    __tablename__ = 'trip'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner = Column(String(255), nullable=False)
    name = Column(Text)
    viewers = Column(ARRAY(Text), default=[])
    editors = Column(ARRAY(Text), default=[])
    trip_data = Column(JSON)

class Preference(Base):
    __tablename__ = 'preference'
    email = Column(String(255), nullable=False, primary_key=True)
    preferences_data = Column(JSON)

def db_save_preferences(user, data):
  with session_scope() as session:
    preference = session.query(Preference).filter_by(email=user).one_or_none()
    if preference is None:
      preference = Preference(email=user, preferences_data=data)
      session.add(preference)
    else:
      preference.preferences_data = data

def db_get_preferences(user):
  with session_scope() as session:
    # Query the preference table using the user's email
    preference = session.query(Preference).filter_by(email=user).one_or_none()
    if preference is not None:
        return preference.preferences_data
    else:
        return None
