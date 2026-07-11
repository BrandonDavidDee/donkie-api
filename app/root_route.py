from asyncpg import Record
from fastapi import APIRouter, HTTPException, Depends
import jwt

from app.db import db

router = APIRouter()


async def authenticate(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    kid = header["kid"]
    #
    row = await db.select_one("SELECT app_id, public_key FROM app_keys WHERE id = $1 AND revoked_at IS NULL", (kid,))
    if not row:
        raise HTTPException(401, "Unknown or revoked key")

    claims = jwt.decode(token, row["public_key"], algorithms=["ES256"])

    app_id = row["app_id"]
    if not claims["tenant_id"].startswith(f"{app_id}:"):
        raise HTTPException(403, "Token app/tenant mismatch")

    return claims

@router.get("/")
async def app_root() -> dict:
    query = "SELECT * FROM alembic_version"
    row: Record = await db.select_one(query, ())
    alembic_version = row[0]
    return {
        "api_name": "Donkie McBooger",
        "alembic_version": alembic_version,
    }


@router.get("/whoami")
async def whoami(claims = Depends(authenticate)):
    return claims
