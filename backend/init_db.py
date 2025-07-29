from database import Base, engine
from models.user import User
from models.event import Event
from models.event_class import EventClass
from models.shared_event import SharedEvent
from models.event_invitation import EventInvitation
from models.friend import Friend
from models.friend_request import FriendRequest

def create_tables():
    Base.metadata.create_all(bind=engine)