from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, Column, String, Text, JSON, ARRAY, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
import uuid

from config import db_connector, db_name, environment

connector = None
db = None

def init_pool(connector):
  def getconn():
      connection = connector.connect(db_connector,
      "pg8000",
      user="dayscape-backend@moonlit-mesh-437320-t8.iam.gserviceaccount.com",
      db=db_name,                                   
      enable_iam_auth=True,
      ip_type=IPTypes.PUBLIC,
    )
      return connection

  # create connection pool
  engine = create_engine("postgresql+pg8000://", creator=getconn)
  return engine

# Sqlalchemy ORM ( https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping )
Base = declarative_base()

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
    
def hello_world():
  global connector, db
  if not db:
    connector = Connector()
    db = init_pool(connector)

  Session = sessionmaker(bind=db)
  session = Session()

  # example trip
  new_trip = Trip(
       owner='example@example.com',
       name='My Trip',
       viewers=['viewer1@example.com', 'viewer2@example.com'],
       editors=['editor1@example.com'],
       trip_data={"destination": "Wonderland", "duration": 7}
   )

  # Example preference. NOTE: this part will fail if you don't change
  # the email because of the email primary key, we need code to update
  # preferences after creating them for a user
  new_preference = Preference(
      email = "example@example.com",
      preferences_data = ["family fun", "public transportation"]
  )

  try:
      session.add(new_trip)
      session.add(new_preference)
      session.commit()
      print("Trip added successfully.")
      # print("Preference added successfully.")
  except Exception as e:
      session.rollback()
      print(f"Error adding trip: {e}")
  finally:
      session.close()

if __name__ == '__main__':
    hello_world()
