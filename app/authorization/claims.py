import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWTError
from pydantic import ValidationError
from typing_extensions import TypedDict
from pydantic import BaseModel

from app.db import db


class TokenClaims(TypedDict):
    tenant_id: str
    user_id: str
    display_name: str
    scope: list[str]
    exp: int


class TokenUser(BaseModel):
    tenant_id: str
    user_id: str
    display_name: str
    scope: list[str]
    webhook_secret: str


def create_401(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def parse_auth_header(authorization: str = Header(None)) -> str | None:
    try:
        token = authorization.partition(" ")[2]
    except (AttributeError, IndexError):
        raise create_401("Missing Auth Header")
    return token


async def get_token_user(token: str = Depends(parse_auth_header)) -> TokenUser:
    header = jwt.get_unverified_header(token)
    kid = header["kid"]

    query = ("SELECT ak.app_id, ak.public_key, apps.webhook_secret "
             "FROM app_keys ak INNER JOIN apps ON apps.id = ak.app_id "
             "WHERE ak.id = $1 AND ak.revoked_at IS NULL")
    row = await db.select_one(
        query,
        (kid,),
    )
    if not row:
        raise HTTPException(401, "Unknown or revoked key")

    try:
        claims: dict = jwt.decode(token, row["public_key"], algorithms=["ES256"])

        app_id = row["app_id"]
        if not claims["tenant_id"].startswith(f"{app_id}:"):
            raise HTTPException(403, "Token app/tenant mismatch")

        return TokenUser(
            tenant_id=claims["tenant_id"],
            user_id=claims["user_id"],
            display_name=claims["display_name"],
            scope=claims["scope"],
            webhook_secret=row["webhook_secret"]
        )

    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(401, "Expired Token")

    except (PyJWTError, ValidationError):
        raise create_401("Could not validate credentials")


async def get_token_claims(token: str = Depends(parse_auth_header)) -> TokenClaims:
    header = jwt.get_unverified_header(token)
    kid = header["kid"]

    row = await db.select_one(
        "SELECT app_id, public_key FROM app_keys WHERE id = $1 AND revoked_at IS NULL",
        (kid,),
    )
    if not row:
        raise HTTPException(401, "Unknown or revoked key")

    try:
        claims: TokenClaims = jwt.decode(token, row["public_key"], algorithms=["ES256"])

        app_id = row["app_id"]
        if not claims["tenant_id"].startswith(f"{app_id}:"):
            raise HTTPException(403, "Token app/tenant mismatch")

        return claims

    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(401, "Expired Token")

    except (PyJWTError, ValidationError):
        raise create_401("Could not validate credentials")
