from fastapi import FastAPI
from routes import (
    management_groups,
    subscriptions,
    virtual_machines,
    vm_compliance,
    vm_advisor,
    vm_metrics
)

app = FastAPI()

app.include_router(management_groups.router)
app.include_router(subscriptions.router)
app.include_router(virtual_machines.router)
app.include_router(vm_compliance.router)
app.include_router(vm_advisor.router)
app.include_router(vm_metrics.router)
