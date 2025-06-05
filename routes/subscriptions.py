from fastapi import APIRouter, Query
from services.subscription_service import get_subscriptions_by_mgmt

router = APIRouter()

@router.get("/subscriptions")
def get_subscriptions(mgmt: str = Query(...)):
    return get_subscriptions_by_mgmt(mgmt)