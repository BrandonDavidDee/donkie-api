from abc import ABC
from enum import Enum

from fastapi import HTTPException, status

from app.authorization.claims import TokenClaims
from app.db import Database, db


class PermissionAction(str, Enum):
    CREATE = "create"
    READ = "read"
    WRITE = "write"
    MANAGE_PARTICIPANTS = "manage_participants"
    TAG = "tag"


class BaseController(ABC):
    def __init__(self, claims: TokenClaims) -> None:
        self.tenant_id = claims["tenant_id"]
        self.user_id = claims["user_id"]
        self.display_name = claims["display_name"]
        self.scope = claims["scope"]
        self.db: Database = db

    def can_create_with_tags(self, tags: list[str]) -> bool:
        """
        ALL tags must have 'create' permission. Used when a request is
        ATTACHING multiple tags to one new object — no partial matches allowed.
        """
        granted = set(self.scope)
        for tag in tags:
            if f"*:{PermissionAction.CREATE.value}" in granted:
                continue
            if f"{tag}:{PermissionAction.CREATE.value}" not in granted:
                return False
        return True

    def has_permission_any(self, tags: list[str], action: PermissionAction) -> bool:
        """
        ANY tag having the permission is enough. Used when checking access
        to something that already exists via one or more paths (tags).
        """
        granted = set(self.scope)
        if f"*:{action.value}" in granted:
            return True
        for tag in tags:
            if f"{tag}:{action.value}" in granted:
                return True
        return False

    def can_add_tag(self, existing_convo_tags: list[str], new_tag: str):
        """
        for adding tags to existing conversation:
        - The caller must already have write access to the conversation
        - The caller must also have permission on the tag being added
        """
        return self.has_permission_any(
            existing_convo_tags, PermissionAction.WRITE
        ) and self.has_permission_any([new_tag], PermissionAction.TAG)

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
