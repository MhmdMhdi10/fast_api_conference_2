from datetime import datetime, timedelta

from fastapi import APIRouter, status, Depends
from database.database import SessionLocal, engine
from fastapi.exceptions import HTTPException

from fastapi_jwt_auth import AuthJWT
from fastapi.encoders import jsonable_encoder

from database.models import Conferences
from database.models import ConferenceRooms

from database.schema import CreateConferenceModel
from database.schema import CreateConferenceRoomModel

import cpmpy as cp
from cpmpy.solvers import CPM_ortools

import requests

conference_router = APIRouter(
    prefix="/conferences",
    tags=["conferences"]
)

session = SessionLocal(bind=engine)


def datetime_to_minutes(dt):
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((dt - midnight).total_seconds() / 60)


def minutes_to_datetime(minutes):
    return datetime.min + timedelta(minutes=minutes)


def create_constraints(existing_meetings, new_meeting_start, new_meeting_end):
    # Convert datetime values to minutes from midnight
    existing_start_times = [datetime_to_minutes(meeting.start_time) for meeting in existing_meetings]
    existing_end_times = [datetime_to_minutes(meeting.end_time) for meeting in existing_meetings]
    new_start_time = datetime_to_minutes(new_meeting_start)
    new_end_time = datetime_to_minutes(new_meeting_end)

    # Create integer variables for the CSP
    existing_start_vars = cp.intvar(0, 1440, shape=len(existing_meetings), name="existing_start_times")
    existing_end_vars = cp.intvar(0, 1440, shape=len(existing_meetings), name="existing_end_times")
    new_start_var = cp.intvar(0, 1440, name="new_start_time")
    new_end_var = cp.intvar(0, 1440, name="new_end_time")

    # Constraints
    constraints = []

    # Constraints to handle meetings that go over midnight

    for existing_end_time in existing_end_times:
        constraints.append(existing_end_time <= new_start_time)

    cp_model = cp.Model(constraints)

    solution = cp_model.solve()

    print(new_start_var.value())

    # If a solution is found, the new meeting can be scheduled without overlapping

    print(solution, "solution")

    return solution


def validate_token(token):
    resp = requests.post("http://localhost:8000/auth/validate", headers={"Authorization": f"Bearer {token}"})
    return {
        'valid': resp.json()["valid"],
        "token": token
            }


# CRUD METHODS FOR CONFERENCE_ROOMS


@conference_router.post("/conference_room", status_code=status.HTTP_201_CREATED)
async def create_conference_room(conference_room: CreateConferenceRoomModel, token: dict = Depends(validate_token)):
    """
    ## create new conference_room
    this requires the following:
    - name: str
    - capacity: int
    """

    if not token["valid"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    username = requests.get("http://localhost:8000/auth/me",
                            headers={"Authorization": f"Bearer {token['token']}"}).json()['username']

    new_conference_room = ConferenceRooms(
        name=conference_room.name,
        capacity=conference_room.capacity,
    )

    new_conference_room.user_username = username

    print(username)

    session.add(new_conference_room)

    session.commit()

    response = {
        "name": new_conference_room.name,
        "capacity": new_conference_room.capacity,
        "username": username
    }

    return jsonable_encoder(response)


@conference_router.get("/conferences_room", status_code=status.HTTP_200_OK)
async def list_all_conferences_room(token: str = Depends(validate_token)):
    """
        ## listing all conference rooms
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    conference_rooms = session.query(ConferenceRooms).all()

    return jsonable_encoder(conference_rooms)


@conference_router.put("/conferences_rooms/{conference_room_id}", status_code=status.HTTP_200_OK)
async def update_conference_room(conference_room_id: int, conference_room: CreateConferenceRoomModel,
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
async def delete_conference_room(conference_room_id: int, token: dict = Depends(validate_token)):
    """
        ## deleting a conference room
        this deletes a conference room
    """

    if not token["valid"]:
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
async def create_conference(conference: CreateConferenceModel, token: dict = Depends(validate_token)):
    """
    ## create new conference
    this requires the following:
    - title: str
    - description: str
    - start_time: datetime = datetime.now()
    - end_time: Optional[datetime]
    - conference_room_id: int
    """
    if not token["valid"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    username = requests.get("http://localhost:8000/auth/me",
                            headers={"Authorization": f"Bearer {token['token']}"}).json()["username"]

    try:
        conference_room = session.query(ConferenceRooms).filter(
            ConferenceRooms.id == conference.conference_room_id).first()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conference room not found")

    # checks if the conference room is occupied or not

    if conference_room.capacity < conference.needed_seats:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="conference room doesn't have enough capacity")

    # existing conferences in the conference_room
    existing_meetings = session.query(Conferences).filter(
            Conferences.conference_room_id == conference.conference_room_id).all()

    print(existing_meetings)

    if len(existing_meetings) != 0:

        # New meeting data
        new_meeting_start = conference.start_time
        new_meeting_end = conference.end_time

        # solves overlapping problem
        solution = create_constraints(existing_meetings, new_meeting_start, new_meeting_end)

        print(solution)

    else:
        solution = True

    if solution:

        new_conference = Conferences(
            title=conference.title,
            description=conference.description,
            start_time=conference.start_time,
            end_time=conference.end_time,
            needed_seats=conference.needed_seats
        )

        new_conference.user_username = username

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

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="conference room is occupied")


@conference_router.get("/conferences", status_code=status.HTTP_200_OK)
async def list_all_conferences(token: dict = Depends(validate_token)):
    """
        ## listing all conferences
    """
    if not token["valid"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    conferences = session.query(Conferences).all()

    return jsonable_encoder(conferences)
