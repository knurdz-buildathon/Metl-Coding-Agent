from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.services.resource_catalog import ResourceCatalog

router = APIRouter(prefix="/resources", tags=["resources"])

_catalog = ResourceCatalog()


@router.get("")
async def list_available_resources():
    """List all resources the agent can request from the control panel."""
    resources = _catalog.list_all()
    return {
        "resources": [
            {
                "type": r.resource_type,
                "name": r.name,
                "description": r.description,
                "env_vars": r.env_vars,
            }
            for r in resources
        ]
    }


@router.get("/{resource_type}")
async def list_resources_by_type(resource_type: str):
    resources = _catalog.list_by_type(resource_type)
    if not resources:
        raise HTTPException(status_code=404, detail=f"No resources found for type: {resource_type}")
    return {
        "type": resource_type,
        "resources": [
            {
                "name": r.name,
                "description": r.description,
                "env_vars": r.env_vars,
            }
            for r in resources
        ],
    }