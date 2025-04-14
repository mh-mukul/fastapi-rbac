import os
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from src.auth.exceptions import APIKeyException, JWTException, UnauthorizedException
from src.exception_handles import (
    validation_exception_handler, general_exception_handler, api_key_exception_handler,
    jwt_exception_handler, unauthorized_exception_handler)

from src.permission import routes as permission_routes
from src.auth import routes as auth_routes
from src.department import routes as department_routes
from src.role import routes as role_routes
from src.user import routes as user_routes

load_dotenv()

DEBUG = bool(int(os.getenv("DEBUG", 1)))

app = FastAPI(
    title="Fast API Backend",
    description="This is Fast API Backend API Documentation",
    version="2.0.0",
    docs_url="/docs" if DEBUG else None,  # Disable Swagger UI
    redoc_url="/redoc" if DEBUG else None,  # Disable ReDoc
    openapi_url="/openapi.json" if DEBUG else None,  # Disable OpenAPI
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the custom exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(APIKeyException, api_key_exception_handler)
app.add_exception_handler(JWTException, jwt_exception_handler)
app.add_exception_handler(UnauthorizedException,
                          unauthorized_exception_handler)


# Include routes
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(permission_routes.router, prefix="/api/v1")
app.include_router(department_routes.router, prefix="/api/v1")
app.include_router(role_routes.router, prefix="/api/v1")
app.include_router(user_routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": 200, "message": "Server is up and running!", "data": "Made with ❤️"}
