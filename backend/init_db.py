from database import Base, engine
from models.user import User
from models.event import Event
from models.event_class import EventClass
from models.event_invitation import EventInvitation
from models.friend import Friend
from models.friend_request import FriendRequest
from models.notification import Notification
from models.recurrence_series import RecurrenceSeries
from models.agent_proposal import AgentProposal
from models.agent_audit_log import AgentAuditLog
from models.agent_user_prefs import AgentUserPrefs

def create_tables():
    Base.metadata.create_all(bind=engine)