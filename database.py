# Direct code to connect to database. Anywhere 'user' is a parameter,
# it means the user's email as a string.

from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, Column, String, Text, JSON, ARRAY, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TIMESTAMP
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
    id = Column(UUID(as_uuid=True), primary_key=True)
    owner = Column(String(255), nullable=False)
    name = Column(Text)
    viewers = Column(ARRAY(Text), default=[])
    editors = Column(ARRAY(Text), default=[])
    trip_data = Column(JSON)

class Preference(Base):
    __tablename__ = 'preference'
    email = Column(String(255), nullable=False, primary_key=True)
    preferences_data = Column(JSON)

class UserInfo(Base):
    __tablename__ = 'userinfo'
    token = Column(String, primary_key=True)
    data = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

def db_get_shared_trips(authenticated_user):
    """
    Retrieves a list of trip IDs and names for trips where the authenticated user
    is a viewer or an editor.

    Returns:
    - A list of tuples (trip_id, trip_name).
    """
    with session_scope() as session:
        trips = (
            session.query(Trip.id, Trip.name)
            .filter(
                (Trip.viewers.any(authenticated_user)) |
                (Trip.editors.any(authenticated_user))
            )
            .all())
        return trips

def db_get_owned_trips(authenticated_user):
    """
    Retrieves a list of trip IDs and names for trips owned by the authenticated user.

    Returns:
    - A list of tuples (trip_id, trip_name).
    """
    with session_scope() as session:
        trips = (
            session.query(Trip.id, Trip.name)
            .filter(Trip.owner == authenticated_user)
            .all())
        return trips

def db_save_trip(authenticated_user, trip_id=None,trip_name=None, trip_data=None, view=None, edit=None, ):
    """
    Saves the trip data structure to the database.
    Parameters:
    - authenticated_user: The email of the authenticated user.
    - trip_id: (Optional) The unique and valid trip ID.
    - view: (Optional) New list of emails of users (besides the owner) who can access the trip to *view*.
    - edit: (Optional) New list of emails of users (besides the owner) who can access the trip to *edit*.
    - trip_data: (Optional) The data structure representing the trip.

    The authenticated_user will be marked as 'owner' of the trip if it's a new trip.
    """

    with session_scope() as session:
        trip = None
        if trip_id:
            trip = session.query(Trip).filter_by(id=trip_id).one_or_none()

        if trip:
            # Check if authenticated user is allowed to edit
            if (trip.owner != authenticated_user and authenticated_user not in trip.editors):
                raise PermissionError("Authenticated user does not have permission to edit this trip.")

            # Only owner can update editors and viewers
            if trip.owner == authenticated_user:
              trip.viewers = view if view is not None else trip.viewers
              trip.editors = edit if edit is not None else trip.editors

            # editor and owner can both change trip_data and name
            trip.name = trip_name if trip_name is not None else trip.name
            trip.trip_data = trip_data if trip_data is not None else trip.trip_data

        # frontend cannot choose the trip id
        if not trip and trip_id:
          raise PermissionError("Invalid trip ID")

        # If no trip is found and we don't have a trip_id, create a
        # new one
        if not trip and not trip_id:
            trip = Trip(owner=authenticated_user,
                        name=trip_name,
                        viewers=view,
                        editors=edit,
                        trip_data=trip_data,
                        id = uuid.uuid4())

        session.add(trip)
        return trip.id

def db_get_trip(authenticated_user, trip_id):
    """
    Retrieves the trip data structure from the database.

    Parameters:
    - authenticated_user: The email of the authenticated user.
    - trip_id: The ID of the trip.

    Returns:
    - The JSON trip structure if the authenticated user has permissions to view the trip.
    """

    with session_scope() as session:
        trip = session.query(Trip).filter_by(id=trip_id).one_or_none()

        # check permissions
        if trip:
            if (
                trip.owner == authenticated_user or
                authenticated_user in trip.editors or
                authenticated_user in trip.viewers
            ):
                return trip.trip_data
            else:
                raise PermissionError("Authenticated user does not have permission to view this trip.")
        else:
            raise ValueError("Trip not found.")

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
    preference = session.query(Preference).filter_by(email=user).one_or_none()
    if preference is not None:
        return preference.preferences_data
    else:
        return None

# "userinfo" is simply some json data about the user that we get from
# the Auth0 API. Since there is a rate limit, we need to cache it
# after retrieving it for the first time for a token.
def db_cache_userinfo(token, data):
    """
    Adds a new record to the 'userinfo' table.

    Parameters:
    - token: The authentication token for the user.
    - data: The JSON data representing the user's information.
    """
    with session_scope() as session:
        user_info = UserInfo(token=token, data=data)
        session.add(user_info)

# Check for, and return, cached userinfo for a token. Tokens expire
# after 10 hours, so we also clear old cache data here.
def db_check_userinfo(token):
  with session_scope() as session:
    # Delete records older than 10 hours
    threshold_time = datetime.now(timezone.utc) - timedelta(hours=10)
    session.query(UserInfo).filter(UserInfo.created_at < threshold_time).delete()

    # Check for userinfo
    userinfo = session.query(UserInfo).filter_by(token=token).one_or_none()
    if userinfo is not None:
        return userinfo.data
    else:
        return None

def db_delete_trip(authenticated_user, trip_id):
    """
    Deletes a trip if the authenticated user is the owner.

    Parameters:
    - authenticated_user: The email of the authenticated user.
    - trip_id: The ID of the trip to be deleted.
    """
    with session_scope() as session:
        trip = session.query(Trip).filter_by(id=trip_id).one_or_none()
        if trip:
            if trip.owner == authenticated_user:
                session.delete(trip)
            else:
                raise PermissionError("Authenticated user does not have permission to delete this trip.")
        else:
            raise ValueError("Trip not found.")


def db_get_trip_name(authenticated_user, trip_id):
    """
    Retrieves the name of the trip if the authenticated user has permission.

    Parameters:
    - authenticated_user: The email of the authenticated user.
    - trip_id: The ID of the trip.

    Returns:
    - The name of the trip.
    """
    with session_scope() as session:
        trip = session.query(Trip).filter_by(id=trip_id).one_or_none()
        if trip:
            if (
                trip.owner == authenticated_user or
                authenticated_user in trip.viewers or
                authenticated_user in trip.editors
            ):
                return trip.name
            else:
                raise PermissionError("Authenticated user does not have permission to view the trip name.")
        else:
            raise ValueError("Trip not found.")


def db_get_viewers(authenticated_user, trip_id):
    """
    Retrieves the list of viewers for a trip if the authenticated user is the owner.

    Parameters:
    - authenticated_user: The email of the authenticated user.
    - trip_id: The ID of the trip.

    Returns:
    - List of viewers' emails.
    """
    with session_scope() as session:
        trip = session.query(Trip).filter_by(id=trip_id).one_or_none()
        if trip:
            if trip.owner == authenticated_user:
                return trip.viewers
            else:
                raise PermissionError("Authenticated user does not have permission to view trip viewers.")
        else:
            raise ValueError("Trip not found.")


def db_get_editors(authenticated_user, trip_id):
    """
    Retrieves the list of editors for a trip if the authenticated user is the owner.

    Parameters:
    - authenticated_user: The email of the authenticated user.
    - trip_id: The ID of the trip.

    Returns:
    - List of editors' emails.
    """
    with session_scope() as session:
        trip = session.query(Trip).filter_by(id=trip_id).one_or_none()
        if trip:
            if trip.owner == authenticated_user:
                return trip.editors
            else:
                raise PermissionError("Authenticated user does not have permission to view trip editors.")
        else:
            raise ValueError("Trip not found.")

def db_is_owner(authenticated_user, trip_id):
    """
    Returns true if the authenticated user is the trip owner.

    Parameters:
    - authenticated_user: The email of the authenticated user.
    - trip_id: The ID of the trip.
    """
    with session_scope() as session:
        trip = session.query(Trip).filter_by(id=trip_id).one_or_none()
        if trip:
            if trip.owner == authenticated_user:
              return True;
            else:
              return False;

def db_can_edit(authenticated_user, trip_id):
    """
    Returns true if the authenticated user has permissions to edit the trip.

    Parameters:
    - authenticated_user: The email of the authenticated user.
    - trip_id: The ID of the trip.
    """
    with session_scope() as session:
        trip = session.query(Trip).filter_by(id=trip_id).one_or_none()
        if trip:
            if trip.owner == authenticated_user or authenticated_user in trip.editors:
              return True;
            else:
              return False;
