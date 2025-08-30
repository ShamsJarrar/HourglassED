from .notification import Notification
from .recurrence_series import RecurrenceSeries
from .user import User
from sqlalchemy.orm import relationship


Notification.user = relationship(
    "User",
    back_populates="notifications",
    passive_deletes=True
)

RecurrenceSeries.user = relationship(
    "User",
    back_populates="recurrence_series",
    passive_deletes=True
)
