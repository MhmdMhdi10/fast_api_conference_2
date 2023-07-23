from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UUID, Boolean
from sqlalchemy_utils.types import ChoiceType
from sqlalchemy.orm import relationship
from database.database import Base


class ConferenceRooms(Base):
    __tablename__ = "conference_rooms"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    capacity = Column(Integer)
    is_active = Column(Boolean)
    conference = relationship("Conferences", back_populates="conference_room")


class Conferences(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    user_username = Column(String)
    conference_room_id = Column(Integer, ForeignKey("conference_rooms.id"))
    conference_room = relationship("ConferenceRooms", back_populates="conference")

    def __repr__(self):
        return f"Order : {self.id}"
