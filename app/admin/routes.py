from fastapi import APIRouter

router = APIRouter()


@router.post("/apps")
async def app_create():
    pass


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
