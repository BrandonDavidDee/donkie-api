import secrets

from app.admin.models.tenant_app import AppCreate, AppReadOnCreate
from app.services.database import Database, db


class AppCreateControl:
    def __init__(self):
        self.db: Database = db

    async def app_create(self, payload: AppCreate) -> AppReadOnCreate:
        webhook_secret = secrets.token_hex(32)
        query = "INSERT INTO apps (name, webhook_secret) VALUES ($1, $2) RETURNING *"
        row: dict = await self.db.insert(
            query,
            (
                payload.name,
                webhook_secret,
            ),
        )
        return AppReadOnCreate(
            id=row["id"],
            name=row["name"],
            webhook_secret=row["webhook_secret"],
            created_at=row["created_at"],
            revoked_at=row["revoked_at"],
        )
