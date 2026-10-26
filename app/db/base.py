import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime

def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

class Base(DeclarativeBase):
    pass
