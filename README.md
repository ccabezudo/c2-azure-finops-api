# Azure VM Monitoring API

This FastAPI project provides a RESTful interface for querying Azure virtual machines and their related metadata, including:
- Subscription and Management Group structure
- VM availability and performance metrics (CPU & Memory)
- Policy compliance status
- Azure Advisor recommendations

The project follows SOLID principles and separates routes, services, and utility functions for maintainability and testability.

---

## 🚀 How to Run This Project

### 1. Set up your virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install "fastapi[standard]"
python3 -m pip install azure.identity azure.mgmt.resource azure.mgmt.resourcegraph azure.mgmt.managementgroups azure.monitor.query azure.mgmt.policyinsights azure.mgmt.advisor fastapi
```

---

## ▶️ Run the API Server

```bash
fastapi dev main.py
```

This will start the FastAPI server with hot-reloading enabled (requires `fastapi[standard]` for the `dev` command).

---

## 📁 Project Structure

```text
.
├── main.py                          # Main FastAPI entrypoint
├── routes/                         # API route declarations (routers)
│   ├── management_groups.py
│   ├── subscriptions.py
│   ├── virtual_machines.py
├── services/                       # Business logic and Azure SDK integration
│   ├── management_groups_service.py
│   ├── subscription_service.py
│   ├── vm_service.py
└── utils/                          # Optional shared helpers
    └── metrics.py
```

---

## 📌 Notes

- Ensure your Azure identity (CLI, VSCode login, or Managed Identity) has at least `Reader` and `Monitoring Reader` roles on the subscriptions.
- Metrics like `Available Memory Bytes` require Azure Monitor Agent or legacy Diagnostics extension to be enabled.
- This project is designed to scale modularly—easily extend with new routes or swap credentials using dependency injection.

---

## ✅ TODO (Optional Enhancements)

- Add async support and parallel execution for metric-heavy endpoints
- Add test suite (e.g., `pytest`)
- Add caching or Redis layer for repeated Resource Graph queries
- Enable OAuth2-based authentication middleware (e.g., Azure AD B2C or MSAL)

---