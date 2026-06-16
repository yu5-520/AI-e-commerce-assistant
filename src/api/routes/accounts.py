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
    list_store_groups,
    list_stores,
    list_users,
    resolve_user_id,
    user_id_from_headers,
)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


@router.get("")
def accounts(request: Request) -> Dict[str, Any]:
    return account_summary(request_user_id(request))


@router.get("/me")
def me(request: Request) -> Dict[str, Any]:
    return current_user(request_user_id(request))


@router.post("/switch")
def switch_account(body: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    """Return a validated mock user context for frontend role switching.

    The server does not create a real session here. The frontend stores the
    returned user id locally and sends it back through `X-Mock-User-Id`.
    """
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


@router.get("/roles")
def roles() -> List[Dict[str, Any]]:
    return list_roles()


@router.get("/permissions")
def permissions() -> List[Dict[str, str]]:
    return list_permissions()


@router.get("/store-groups")
def store_groups() -> List[Dict[str, Any]]:
    return list_store_groups()


@router.get("/stores")
def stores() -> List[Dict[str, Any]]:
    return list_stores()
