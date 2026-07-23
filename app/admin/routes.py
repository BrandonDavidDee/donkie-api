from fastapi import APIRouter
from app.admin.controllers.app_create import AppCreateControl
from app.admin.models.tenant_app import AppCreate, AppReadOnCreate

router = APIRouter()


@router.post("/apps")
async def app_create(payload: AppCreate) -> AppReadOnCreate:
    return await AppCreateControl().app_create(payload)


@router.get("/apps")
async def app_list():
    pass


@router.get("/apps/{app_id}")
async def app_detail():
    pass


@router.put("/apps/{app_id}")
async def app_update():
    pass


@router.post("/apps/{app_id}/keys")
async def app_key_create():
    pass


@router.post("/apps/{app_id}/webhooks")
async def webhook_create():
    pass
