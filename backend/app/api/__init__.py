"""
API Router (Phase 8).

Consolidates all v1 REST API sub-routers.
"""

from fastapi import APIRouter

from app.api.agent import router as agent_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.financial_snapshot import router as financial_snapshot_router
from app.api.lifecycle import router as lifecycle_router
from app.api.reconciliation import router as reconciliation_router
from app.api.tax_report import router as tax_report_router
from app.api.upload import router as upload_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(upload_router)
api_router.include_router(financial_snapshot_router)
api_router.include_router(reconciliation_router)
api_router.include_router(agent_router)
api_router.include_router(catalog_router)
api_router.include_router(tax_report_router)
api_router.include_router(lifecycle_router)

__all__ = ["api_router"]
