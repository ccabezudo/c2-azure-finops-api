from fastapi import FastAPI
from routes import (
    management_groups,
    subscriptions,
    virtual_machines,
)

app = FastAPI()

app.include_router(management_groups.router)
app.include_router(subscriptions.router)
app.include_router(virtual_machines.router)
