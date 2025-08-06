from fastapi import FastAPI
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Depends
from dependencies import get_db
from init_db import create_tables
from routers import auth, friends, events, event_invitations, notifications
from logger import logger


create_tables()

app = FastAPI()
app.include_router(auth.router)
app.include_router(friends.router)
app.include_router(events.router)
app.include_router(event_invitations.router)
app.include_router(notifications.router)


logger.info("HourglassED API starting!")


# API test
@app.get("/")
def root():
    return {"message":"HourglassEd API test"}


# database connection test
# @app.get("/db-test")
# def test_db(db: Session = Depends(get_db)):
#     try:
#         db.execute(text("SELECT 1"))
#         return {"status" : "success"}
#     except Exception as e:
#         return {"status": "error", "detail": str(e)}

