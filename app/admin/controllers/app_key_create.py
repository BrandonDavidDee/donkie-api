import base64
from uuid import UUID

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.admin.models.app_key import AppKeyCreate, AppKeyRead
from app.services.database import Database, db


class DevAppKeyCreate:
    """
    Dev version for generating and storing keys
    """

    def __init__(self, app_id: UUID):
        self.db: Database = db
        self.app_id = app_id

    async def app_key_pair_create(self) -> dict:
        private_encoded_key, decoded_public_pem = self._generate_keys()
        query = "INSERT INTO app_keys (app_id, public_key) VALUES ($1, $2) RETURNING *"
        row: dict = await self.db.insert(
            query,
            (
                self.app_id,
                decoded_public_pem,
            ),
        )
        return {
            "app_id": self.app_id,
            "app_key_id": row["id"],
            "private_key": private_encoded_key,
        }

    @staticmethod
    def _generate_keys() -> tuple[str, str]:
        private_key = ec.generate_private_key(ec.SECP256R1())

        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),  # see docstring
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        private_encoded_key = base64.b64encode(private_pem).decode()
        # ^^ store this as an env variable in the consuming application.

        decoded_public_pem = public_pem.decode()
        # ^^ this is what gets stored in app_keys.public_key
        return private_encoded_key, decoded_public_pem


class AppKeyCreateControl:
    """
    In this version, the user would be supplying the public key
    """

    def __init__(self, app_id: UUID):
        self.db: Database = db
        self.app_id = app_id

    async def app_key_create(self, payload: AppKeyCreate) -> AppKeyRead:
        query = "INSERT INTO app_keys (app_id, public_key) VALUES ($1, $2) RETURNING *"
        row: dict = await self.db.insert(
            query,
            (
                self.app_id,
                payload.public_key,
            ),
        )
        return AppKeyRead(
            id=row["id"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
        )
