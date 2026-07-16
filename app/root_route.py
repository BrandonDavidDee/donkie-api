from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def app_root() -> dict:
    return {
        "api_name": "Donkie McBooger",
    }
