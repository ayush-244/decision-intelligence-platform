"""Aggregate router for API v1.

Individual feature routers register here. Keeping a single aggregation point
means ``app.main`` mounts one router and version wiring stays in one place.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.v1.routers.auth import router as auth_router
from app.presentation.api.v1.routers.datasets import router as datasets_router
from app.presentation.api.v1.routers.health import router as health_router
from app.presentation.api.v1.routers.meta import router as meta_router
from app.presentation.api.v1.routers.organizations import router as organizations_router
from app.presentation.api.v1.routers.projects import router as projects_router
from app.presentation.api.v1.routers.causal import router as causal_router
from app.presentation.api.v1.routers.statistics import router as statistics_router
from app.presentation.api.v1.routers.simulations import router as simulations_router
from app.presentation.api.v1.routers.scenarios import router as scenarios_router
from app.presentation.api.v1.routers.roi import router as roi_router
from app.presentation.api.v1.routers.risk import router as risk_router
from app.presentation.api.v1.routers.decisions import router as decisions_router
from app.presentation.api.v1.routers.recommendations import router as recommendations_router
from app.presentation.api.v1.routers.tradeoffs import router as tradeoffs_router
from app.presentation.api.v1.routers.priorities import router as priorities_router
from app.presentation.api.v1.routers.objectives import router as objectives_router
from app.presentation.api.v1.routers.reports import router as reports_router
from app.presentation.api.v1.routers.executive import router as executive_router
from app.presentation.api.v1.routers.sessions import router as sessions_router
from app.presentation.api.v1.routers.workspace import router as workspace_router
from app.presentation.api.v1.routers.jobs import router as jobs_router
from app.presentation.api.v1.routers.infrastructure import router as infrastructure_router
from app.presentation.api.v1.routers.governance import router as governance_router
from app.presentation.api.v1.routers.copilot import router as copilot_router
from app.presentation.api.v1.routers.workspaces import router as workspaces_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(meta_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(organizations_router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(statistics_router)
api_v1_router.include_router(causal_router)
api_v1_router.include_router(simulations_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(roi_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(decisions_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(tradeoffs_router)
api_v1_router.include_router(priorities_router)
api_v1_router.include_router(objectives_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(executive_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(workspace_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(infrastructure_router)
api_v1_router.include_router(governance_router)
api_v1_router.include_router(copilot_router)
