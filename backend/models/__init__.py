from .notification import Notification
from .user import User
from sqlalchemy.orm import relationship


Notification.user = relationship(
    "User",
    back_populates="notifications",
    passive_deletes=True
)