"""Operating unit module route.

经营单元是共同业务空间；店铺责任权限决定进入后能看到哪些店铺切片。
老板 / 总管看经营单元全量，运营只看自己负责店铺。
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request

from src.services.account_service import current_user, list_store_groups, list_stores, user_id_from_headers, visible_store_ids_for_user

router = APIRouter()


@router.get("/operating-unit")
def operating_unit(request: Request) -> Dict[str, Any]:
    user_id = user_id_from_headers(request.headers)
    user = current_user(user_id)
    group = list_store_groups()[0]
    all_stores = [store for store in list_stores() if store.get("groupId") == group["id"]]
    visible_ids = set(visible_store_ids_for_user(user_id))
    visible_stores = [store for store in all_stores if store["id"] in visible_ids]
    role_id = user.get("roleId")
    can_see_all = role_id in {"owner", "manager", "finance"}
    scope_label = "经营单元全量" if can_see_all else "我的店铺切片"
    return {
        "unitId": group["id"],
        "unitName": group["name"],
        "viewer": user,
        "scopeLabel": scope_label,
        "canSeeAllUnitStores": can_see_all,
        "allStoreCount": len(all_stores),
        "visibleStoreCount": len(visible_stores),
        "platforms": sorted({store["platform"] for store in visible_stores}),
        "stores": visible_stores,
        "allStores": all_stores if can_see_all else [],
        "dataSources": ["ERP", "CRM", "报表上传"],
        "pendingSources": ["聚水潭", "广告后台"],
        "permissionRule": "总管看经营单元全量；运营进入同一经营单元，但商品、报表、预警、待办只返回自己负责店铺。",
    }
