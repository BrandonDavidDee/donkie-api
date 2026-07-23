from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin.routes import router as admin
from app.conf import ALLOW_ORIGIN_REGEX, ALLOW_ORIGINS
from app.conversations.routes import router as conversations
from app.db import db
from app.root_route import router as root_router


@asynccontextmanager
async def lifespan(event_run_api: FastAPI):
    await db.open_conn_pool()
    event_run_api.state.lifecycle_events = ["startup"]
    event_run_api.state.startup_checks = {
        "origin_regex_configured": bool(ALLOW_ORIGIN_REGEX),
    }
    yield
    await db.close_pool()
    event_run_api.state.lifecycle_events.append("shutdown")


def configure_middleware(event_run_api: FastAPI) -> None:
    event_run_api.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOW_ORIGINS,
        allow_origin_regex=ALLOW_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def register_routers(event_run_api: FastAPI) -> None:
    event_run_api.include_router(root_router, prefix="")
    event_run_api.include_router(admin, prefix="/admin")
    event_run_api.include_router(conversations, prefix="/v1/conversations")


def create_app() -> FastAPI:
    event_run_api = FastAPI(lifespan=lifespan)
    configure_middleware(event_run_api)
    register_routers(event_run_api)
    return event_run_api


app = create_app()
