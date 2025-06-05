from fastapi import APIRouter, Query
from services.management_groups_service import get_child_management_groups_handler

router = APIRouter()

@router.get("/managementGroups/children")
def get_children(mgmt: str = Query(default=None)):
    return get_child_management_groups_handler(mgmt)