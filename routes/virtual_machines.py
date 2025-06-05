from fastapi import APIRouter, Query
from services.vm_service import get_virtual_machines_handler, get_vm_runtime_hours_handler
from services.vm_service import get_vm_policy_compliance_handler
from services.vm_service import get_vm_advisor_recommendations_handler
from services.vm_service import get_vm_metrics_summary_handler, get_vm_metrics_timeseries_handler


router = APIRouter()

@router.get("/virtualmachines")
def get_vms(subscription_id: str = Query(...)):
    return get_virtual_machines_handler(subscription_id)

@router.get("/vm-runtimehours")
def get_vm_runtime_hours(subscription_id: str = Query(...), lookback_days: int = Query(7)):
    return get_vm_runtime_hours_handler(subscription_id, lookback_days)


@router.get("/vm-policy-compliance")
def get_compliance(subscription_id: str = Query(...)):
    return get_vm_policy_compliance_handler(subscription_id)


@router.get("/vm-advisor-recommendations")
def get_advisor(subscription_id: str = Query(...)):
    return get_vm_advisor_recommendations_handler(subscription_id)

@router.get("/vm-metrics")
def metrics_summary(subscription_id: str = Query(...), lookback_hours: int = Query(24)):
    return get_vm_metrics_summary_handler(subscription_id, lookback_hours)

@router.get("/vm-metrics-timeseries")
def metrics_timeseries(subscription_id: str = Query(...), lookback_hours: int = Query(24)):
    return get_vm_metrics_timeseries_handler(subscription_id, lookback_hours)
