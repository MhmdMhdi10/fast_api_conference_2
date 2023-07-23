import inspect
import re

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from fastapi_jwt_auth import AuthJWT

from database.auth.schema import Setting
from database.database import Base, engine
from routes.auth.auth_routes import auth_router

Base.metadata.create_all(bind=engine)

users_app = FastAPI()


def custom_openapi():
    if users_app.openapi_schema:
        return users_app.openapi_schema

    openapi_schema = get_openapi(
        title="conference maker users microservice",
        version="1.0",
        description="a microservice api for auth",
        routes=users_app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter: **'Bearer &lt;JWT&gt;'**, where JWT is the access token"
        }
    }

    # Get all routes where jwt_optional() or jwt_required
    api_router = [route for route in users_app.routes if isinstance(route, APIRoute)]

    for route in api_router:
        path = getattr(route, "path")
        endpoint = getattr(route, "endpoint")
        methods = [method.lower() for method in getattr(route, "methods")]

        for method in methods:
            # access_token
            if (
                    re.search("jwt_required", inspect.getsource(endpoint)) or
                    re.search("fresh_jwt_required", inspect.getsource(endpoint)) or
                    re.search("jwt_optional", inspect.getsource(endpoint))
            ):
                openapi_schema["paths"][path][method]["security"] = [
                    {
                        "Bearer Auth": []
                    }
                ]

    users_app.openapi_schema = openapi_schema
    return users_app.openapi_schema


users_app.openapi = custom_openapi


@AuthJWT.load_config
def get_config():
    return Setting()


@AuthJWT.load_config
def get_config():
    return Setting()


users_app.include_router(auth_router)
