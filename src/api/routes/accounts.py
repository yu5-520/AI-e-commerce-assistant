"""Account, role, and permission routes for the v2 collaboration layer."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException, Request

from src.services.account_service import (
    account_summary,
    current_user,
    get_user,
    list_permissions,
    list_roles,
    list_role_change_logs,
    list_store_groups,
    list_stores,
    list_users,
    resolve_user_id,
    update_role_permissions,
    update_user_role,
    update_user_stores,
    user_has_permission,
    user_id_from_headers,
)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def require_role_manager(request: Request) -> str:
    user_id = request_user_id(request)
    if not user_has_permission(user_id, "manage_roles"):
        user = current_user(user_id)
        raise HTTPException(status_code=403, detail=f"{user['roleName']} cannot manage account permissions")
    return user_id


@router.get("")
def accounts(request: Request) -> Dict[str, Any]:
    return account_summary(request_user_id(request))


@router.get("/me")
def me(request: Request) -> Dict[str, Any]:
    return current_user(request_user_id(request))


@router.post("/switch")
def switch_account(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """Return a validated mock user context for frontend role switching."""
    user_id = resolve_user_id(body.get("user_id") or body.get("userId"))
    return {"currentUser": current_user(user_id), "account": account_summary(user_id)}


@router.get("/users")
def users() -> List[Dict[str, Any]]:
    return list_users()


@router.get("/users/{user_id}")
def user_detail(user_id: str) -> Dict[str, Any]:
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@router.post("/users/{user_id}/role")
def change_user_role(request: Request, user_id: str, body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    operator_id = require_role_manager(request)
    user = update_user_role(user_id, body.get("role_id") or body.get("roleId"), operator_id=operator_id)
    if not user:
        raise HTTPException(status_code=400, detail="cannot update user role")
    return {"user": user, "account": account_summary(operator_id)}


@router.post("/users/{user_id}/stores")
def change_user_stores(request: Request, user_id: str, body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    operator_id = require_role_manager(request)
    user = update_user_stores(user_id, body.get("store_ids") or body.get("storeIds") or [], operator_id=operator_id)
    if not user:
        raise HTTPException(status_code=400, detail="cannot update user stores")
    return {"user": user, "account": account_summary(operator_id)}


@router.get("/roles")
def roles() -> List[Dict[str, Any]]:
    return list_roles()


@router.post("/roles/{role_id}/permissions")
def change_role_permissions(request: Request, role_id: str, body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    operator_id = require_role_manager(request)
    role = update_role_permissions(role_id, body.get("permissions") or [], operator_id=operator_id)
    if not role:
        raise HTTPException(status_code=400, detail="cannot update role permissions")
    return {"role": role, "account": account_summary(operator_id)}


@router.get("/permissions")
def permissions() -> List[Dict[str, str]]:
    return list_permissions()


@router.get("/store-groups")
def store_groups() -> List[Dict[str, Any]]:
    return list_store_groups()


@router.get("/stores")
def stores() -> List[Dict[str, Any]]:
    return list_stores()


@router.get("/role-change-logs")
def role_logs() -> List[Dict[str, Any]]:
    return list_role_change_logs()
