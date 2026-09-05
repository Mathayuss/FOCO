from fastapi import APIRouter
router = APIRouter(tags=["saúde"])

@router.get("/health")
def health():
    return {"status": "ok", "service": "foco-api"}
