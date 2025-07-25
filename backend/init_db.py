from database import Base, engine
from models.user import User
from models.event import Event
from models.event_classes import EventClass
from models.shared_event import SharedEvent

def create_tables():
    Base.metadata.create_all(bind=engine)