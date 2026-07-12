from abc import ABC
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.authorization.claims import TokenClaims
from app.db import Database, db


class BaseController(ABC):
    def __init__(self, claims: TokenClaims) -> None:
        self.tenant_id = claims["tenant_id"]
        self.user_id = claims["user_id"]
        self.scope = claims["scope"]
        self.db: Database = db
        self.now = datetime.now(tz=timezone.utc)

    @staticmethod
    def create_403(detail: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    @staticmethod
    def create_404(detail: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    @staticmethod
    def create_422(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail
        )

    @staticmethod
    def create_500(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )
