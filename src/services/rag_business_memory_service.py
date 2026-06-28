"""V12.6 RAG-style business memory facade.

Demo implementation: returns deterministic policy and memory context so the task
chain can attach clear permission/baseline information before a real vector/RAG
backend is connected.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.action_authorization_gate_service import infer_action_type

RAG_BUSINESS_MEMORY_VERSION = "12.6.0"

BASELINES = {
    "default": {
        "minRoi": 2.0,
        "minGrossMarginRate": 0.28,
        "minSellableDays": 7,
        "refundRateCeiling": 0.12,
        "operatorActivityBudgetRange": [3000, 8000],
        "operatorWeightPermission": "middle",
    }
}

HISTORICAL_ACTION_MEMORY = {
    "activity_participation": {
        "trafficLiftRange": "1.15x-1.90x",
        "gmvLiftRange": "+12%-+70%",
        "roiChangeRange": "-8%-+12%",
        "inventoryConsumptionRange": "平日 1.3x-1.75x",
        "memoryRule": "真实活动复盘写入后，按平台、类目、价格带、资源位继续缩小估算范围。",
    },
    "title_test": {
        "clickRateLiftRange": "+3%-+15%",
        "conversionChangeRange": "-2%-+5%",
        "testWindowDays": 3,
        "memoryRule": "标题测试复盘后记录关键词、人群、平台和点击率变化。",
    },
    "main_image_test": {
        "clickRateLiftRange": "+3%-+15%",
        "conversionChangeRange": "-2%-+5%",
        "testWindowDays": 3,
        "memoryRule": "主图测试复盘后记录画面方向、卖点顺序和点击率/转化变化。",
    },
}


def business_memory_context(task: Dict[str, Any]) -> Dict[str, Any]:
    action_type = infer_action_type(task)
    return {
        "version": RAG_BUSINESS_MEMORY_VERSION,
        "mode": "rag_business_policy_and_memory_context",
        "actionType": action_type,
        "companyBaseline": BASELINES["default"],
        "historicalMemory": HISTORICAL_ACTION_MEMORY.get(action_type, {}),
        "approvalPolicy": {
            "autoConfirmUsesConservativeFloor": True,
            "operatorProvidesFactsOnly": True,
            "managerApprovesWhenOverPermissionOrBelowBaseline": True,
        },
        "memoryWriteback": {
            "afterDays": 3,
            "targets": ["周报", "商品策略记录", "RAG记忆候选"],
            "metrics": ["ROI", "GMV/支付金额", "访客数", "点击率", "转化率", "广告消耗", "库存消耗", "退款率", "毛利率"],
        },
    }


def apply_rag_business_memory(task: Dict[str, Any]) -> Dict[str, Any]:
    context = business_memory_context(task)
    return {**task, "ragBusinessMemory": context, "v126RagMemory": context}
