import datetime

from fastapi import APIRouter, status, Depends
from database.database import SessionLocal, engine
from fastapi.exceptions import HTTPException

from fastapi_jwt_auth import AuthJWT
from fastapi.encoders import jsonable_encoder

from database.models import Conferences
from database.models import ConferenceRooms

from database.schema import CreateConferenceModel
from database.schema import CreateConferenceRoomModel

from cpmpy import *
from cpmpy.solvers import CPM_ortools

import requests

conference_router = APIRouter(
    prefix="/conferences",
    tags=["conferences"]
)

session = SessionLocal(bind=engine)


def is_conference_room_available(existing_conferences, end_time_var):
    pass


def validate_token(token):
    resp = requests.post("http://localhost:8000/auth/validate", headers={"Authorization": f"Bearer {token}"})
    return resp.json()["valid"]


# CRUD METHODS FOR CONFERENCE_ROOMS


@conference_router.post("/conference_room", status_code=status.HTTP_201_CREATED)
async def create_conference(conference_room: CreateConferenceRoomModel, token: str = Depends(validate_token)):
    """
    ## create new conference_room
    this requires the following:
    - name: str
    - capacity: int
    """

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user = requests.get("http://localhost:8000/auth/users/me")

    new_conference_room = ConferenceRooms(
        name=conference_room.name,
        capacity=conference_room.capacity,
    )

    new_conference_room.user_username = user

    session.add(new_conference_room)

    session.commit()

    response = {
        "name": new_conference_room.name,
        "capacity": new_conference_room.capacity,

    }

    return jsonable_encoder(response)


@conference_router.get("/conferences_room", status_code=status.HTTP_200_OK)
async def list_all_conferences(token: str = Depends(validate_token)):
    """
        ## listing all conference rooms
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    conference_rooms = session.query(ConferenceRooms).all()

    return jsonable_encoder(conference_rooms)


@conference_router.put("/conferences_rooms/{conference_room_id}", status_code=status.HTTP_200_OK)
async def update_conference(conference_room_id: int, conference_room: CreateConferenceRoomModel,
                            token: str = Depends(validate_token)):
    """
        ## Updating a conference room
        this updates a conference room requires the following list:
        - name: str
        - capacity: int
        - is_active: bool = False
    """

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    try:
        conference_to_update = session.query(ConferenceRooms).filter(ConferenceRooms.id == conference_room_id).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conference Room not found")

    conference_to_update.name = conference_room.name
    conference_to_update.capacity = conference_room.capacity
    conference_to_update.is_active = conference_room.is_active

    session.commit()

    response = {
        "name": conference_to_update.name,
        "capacity": conference_to_update.capacity,
        "is_active": conference_to_update.is_active,
    }

    return jsonable_encoder(response)


@conference_router.delete("/conference_rooms/{conference_room_id}", status_code=status.HTTP_200_OK)
async def delete_conference(conference_room_id: int, token: str = Depends(validate_token)):
    """
        ## deleting a conference room
        this deletes a conference room
    """

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    conference_room_to_delete = session.query(ConferenceRooms).filter(ConferenceRooms.id == conference_room_id).first()

    try:
        session.delete(conference_room_to_delete)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conference Room not found")
    session.commit()
    return conference_room_to_delete


# METHODS FOR CONFERENCES

@conference_router.post("/conference/", status_code=status.HTTP_201_CREATED)
async def create_conference(conference: CreateConferenceModel, token: str = Depends(validate_token)):
    """
    ## create new conference
    this requires the following:
    - title: str
    - description: str
    - start_time: datetime = datetime.now()
    - end_time: Optional[datetime]
    - conference_room_id: int
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user = requests.get("http://localhost:8000/auth/users/me")

    try:
        conference_room = session.query(ConferenceRooms).filter(
            ConferenceRooms.id == conference.conference_room_id).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conference room not found")

    if conference_room.is_active is True:
        existing_conference = session.query(Conferences).filter(
            Conferences.conference_room_id == conference.conference_room_id).first()
        if existing_conference.end_time > datetime.datetime.now():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="conference room is occupied")

    new_conference = Conferences(
        title=conference.title,
        description=conference.description,
        start_time=conference.start_time,
        end_time=conference.end_time,
    )

    new_conference.user_username = user.json()['username']

    print(user.json()["username"])

    new_conference.conference_room = conference_room

    conference_room.is_active = True

    session.add(conference_room)
    session.add(new_conference)

    session.commit()

    response = {
        "title": new_conference.title,
        "description": new_conference.description,
        "start_time": new_conference.start_time,
        "end_time": new_conference.end_time,
        "conference_room_id": new_conference.conference_room_id,
    }

    return jsonable_encoder(response)


@conference_router.get("/conferences", status_code=status.HTTP_200_OK)
async def list_all_conferences(token: str = Depends(validate_token)):
    """
        ## listing all conferences
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    conferences = session.query(Conferences).all()

    return jsonable_encoder(conferences)
