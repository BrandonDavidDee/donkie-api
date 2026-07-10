from asyncpg import Record
from fastapi import APIRouter

from app.db import db

router = APIRouter()


@router.get("/")
async def app_root() -> dict:
    query = "SELECT * FROM alembic_version"
    row: Record = await db.select_one(query, ())
    alembic_version = row[0]
    return {
        "api_name": "Donkie McBooger",
        "alembic_version": alembic_version,
    }
