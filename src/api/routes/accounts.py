"""Account, role, and permission routes for the v2 collaboration layer."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.services.account_service import (
    account_summary,
    current_user,
    get_user,
    list_permissions,
    list_roles,
    list_store_groups,
    list_stores,
    list_users,
)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("")
def accounts() -> Dict[str, Any]:
    return account_summary()


@router.get("/me")
def me() -> Dict[str, Any]:
    return current_user()


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
