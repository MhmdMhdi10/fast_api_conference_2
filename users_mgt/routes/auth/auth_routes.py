from fastapi import APIRouter, status, Depends
from database.database import SessionLocal, engine
from database.auth.schema import SignUpModel, LoginModel
from database.auth.models import User
from fastapi.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi_jwt_auth import AuthJWT
from fastapi.encoders import jsonable_encoder


auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


session = SessionLocal(bind=engine)


# signup route


@auth_router.post('/users', status_code=status.HTTP_201_CREATED)
async def signup(user: SignUpModel):
    """
        ## SignUP
        this Creates a user and requires the following list:
        - id: Optional[int]
        - username: str
        - password: str
    """
    db_username = session.query(User).filter(User.username == user.username).first()

    if db_username is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with the username already exists")

    new_user = User(
        username=user.username,
        password=generate_password_hash(user.password),
    )

    session.add(new_user)
    session.commit()

    return new_user


# login route


@auth_router.post('/login')
async def login(user: LoginModel, authorize: AuthJWT = Depends()):
    """
        ## Login
        this returns a Token requires the following list:
        - username: str
        - password: str
    """
    db_user = session.query(User).filter(User.username == user.username).first()

    if db_user and check_password_hash(db_user.password, user.password):
        access_token = authorize.create_access_token(subject=db_user.username)
        refresh_token = authorize.create_refresh_token(subject=db_user.username)

        response = {
            "access": access_token,
            "refresh": refresh_token,
        }

        return jsonable_encoder(response)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Username or password")


# refreshing token


@auth_router.post("/refresh")
async def refresh(authorize: AuthJWT = Depends()):
    """
        ## Create a fresh token
        This creates a fresh token. it requires a refresh token.
    """
    try:
        authorize.jwt_refresh_token_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please Provide a valid refresh token")

    current_user = authorize.get_jwt_subject()

    access_token = authorize.create_access_token(subject=current_user)

    return jsonable_encoder({"access": access_token})


@auth_router.post("/validate")
async def validate(authorize: AuthJWT = Depends()):
    """
        ## Validates tokens
        This creates a fresh token. it requires a refresh token.
    """
    try:
        authorize.jwt_required()
        response = {
            "valid": True
        }
    except Exception as e:
        response = {
            "valid": False
        }

    return jsonable_encoder(response)


@auth_router.get("/users/me")
async def get_user_info(authorize: AuthJWT = Depends()):
    """
        ## Returns username
    """
    username = authorize.get_jwt_subject()

    response = {
        "username": username
    }

    return jsonable_encoder(response)



