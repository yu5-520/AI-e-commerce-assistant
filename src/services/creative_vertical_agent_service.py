"""V4.3+ vertical category creative Agent service.

This Agent turns product facts, category profiles, platform expression rules,
competitor signals, and RAG memory into ready-to-test title / main-image
packages. It is advisory-only: it creates creative strategies and optional test
tasks, but it never publishes products or changes live marketplace content.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from src.services.account_service import current_user
from src.services.experience_memory_service import list_category_profiles, search_cases
from src.services.module_data_service import COMPETITORS, LISTINGS, PRODUCTS, find_by_id
from src.services.module_task_service import create_task

CREATIVE_AGENT_VERSION = "4.4.0"
FORBIDDEN_ACTIONS = ["不直接发布商品", "不直接改价", "不直接投放", "不直接生成夸大承诺", "不直接回写 ERP / CRM / 店铺后台"]
DEFAULT_CATEGORY_ID = "home_living_goods"
DEFAULT_SUBMIT_METRICS = ["曝光", "点击率", "转化率", "收藏加购", "退款率", "客服咨询关键词"]

PLATFORM_RULES: Dict[str, Dict[str, Any]] = {
    "淘宝": {
        "titleFocus": ["搜索关键词覆盖", "材质", "场景", "规格可信度"],
        "imageFocus": ["容量可视化", "尺寸参照", "使用前后对比"],
        "trafficTypes": ["搜索流量", "推荐流量"],
        "avoid": ["标题堆砌无关词", "主图夸大容量", "承诺超出商品事实"],
    },
    "拼多多": {
        "titleFocus": ["到手价值", "套装数量", "价格带", "耐用"],
        "imageFocus": ["数量对比", "家庭囤货场景", "材质耐用展示"],
        "trafficTypes": ["搜索流量", "活动流量", "推荐流量"],
        "avoid": ["只强调便宜不解释价值", "过度低价暗示", "忽略售后预期"],
    },
    "抖音小店": {
        "titleFocus": ["场景痛点", "短句卖点", "人群需求", "即时改善"],
        "imageFocus": ["首屏冲击", "前后对比", "真实使用场景"],
        "trafficTypes": ["内容推荐", "直播承接", "短视频引流"],
        "avoid": ["静态堆字", "无场景抽象卖点", "过度医疗或功效承诺"],
    },
    "通用": {
        "titleFocus": ["商品事实", "核心卖点", "使用场景", "风险边界"],
        "imageFocus": ["真实展示", "对比表达", "证据可视化"],
        "trafficTypes": ["搜索流量", "推荐流量"],
        "avoid": ["夸大承诺", "无证据卖点", "平台敏感词"],
    },
}


def _viewer(user_id: str | None) -> Dict[str, Any]:
    user = current_user(user_id)
    return {"userId": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")}


def _product(product_id: str, body: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    body = body or {}
    if body.get("productFacts"):
        item = deepcopy(body["productFacts"])
        item.setdefault("id", product_id)
        return item
    found = find_by_id(PRODUCTS, product_id)
    return deepcopy(found) if found else None


def _category_profile(category_id: str) -> Dict[str, Any]:
    profiles = list_category_profiles()
    for profile in profiles:
        if profile.get("categoryId") == category_id:
            return deepcopy(profile)
    return {
        "profileId": f"CAT-{category_id}",
        "memoryType": "category_profile",
        "categoryId": category_id,
        "categoryName": "通用商品类目",
        "riskFocus": ["承诺可信度", "价格带", "售后预期"],
        "creativeFocus": ["场景", "卖点", "证据"],
        "platformHints": {},
        "qualityScore": 0.5,
    }


def _related_competitors(product: Dict[str, Any], body: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    body = body or {}
    manual = body.get("competitorSignals") or []
    if manual and isinstance(manual[0] if manual else None, dict):
        return deepcopy(manual)
    names = {str(product.get("shortName") or ""), str(product.get("title") or ""), str(product.get("id") or "")}
    results: List[Dict[str, Any]] = []
    for item in COMPETITORS:
        target = str(item.get("targetProduct") or item.get("title") or "")
        if any(name and (name in target or target in name) for name in names):
            results.append(deepcopy(item))
    if manual:
        for signal in manual:
            results.append({"id": f"manual-{len(results) + 1}", "badReview": str(signal), "opportunity": str(signal), "source": "manual"})
    return results[:5]


def _related_listings(product: Dict[str, Any]) -> List[Dict[str, Any]]:
    names = {str(product.get("shortName") or ""), str(product.get("title") or ""), str(product.get("id") or "")}
    results: List[Dict[str, Any]] = []
    for item in LISTINGS:
        source_name = str(item.get("sourceName") or item.get("title") or "")
        if any(name and (name in source_name or source_name in name) for name in names):
            results.append(deepcopy(item))
    return results[:5]


def _platform_rule(platform: str) -> Dict[str, Any]:
    return deepcopy(PLATFORM_RULES.get(platform) or PLATFORM_RULES["通用"])


def _core_facts(product: Dict[str, Any]) -> List[str]:
    facts = []
    for key in ["shortName", "title", "price", "grossMargin", "inventoryStatus", "afterSales", "suggestion"]:
        if product.get(key) is not None:
            facts.append(str(product[key]))
    return facts


def _selling_points(product: Dict[str, Any], category_profile: Dict[str, Any], competitors: List[Dict[str, Any]]) -> List[str]:
    text = " ".join(_core_facts(product) + [str(item.get("badReview") or item.get("opportunity") or "") for item in competitors])
    points = []
    if any(word in text for word in ["收纳", "置物", "整理", "容量"]):
        points.extend(["容量", "空间整理", "尺寸可信", "安装 / 使用说明"])
    if any(word in text for word in ["防晒", "遮阳", "晴雨"]):
        points.extend(["防晒场景", "便携收纳", "材质可信", "晴雨两用"])
    if any(word in text for word in ["护腰", "坐垫", "靠垫"]):
        points.extend(["支撑感", "久坐场景", "材质说明", "适用人群"])
    if any(word in text for word in ["清洁", "刷", "缝隙"]):
        points.extend(["清洁场景", "缝隙效果", "组合价值", "耐用材质"])
    points.extend(category_profile.get("creativeFocus") or [])
    deduped: List[str] = []
    for point in points:
        if point and point not in deduped:
            deduped.append(point)
    return deduped[:6] or ["商品事实", "核心卖点", "使用场景", "风险边界"]


def _title_variants(product: Dict[str, Any], platform: str, selling_points: List[str], task_goal: str) -> List[Dict[str, Any]]:
    short = product.get("shortName") or product.get("title") or product.get("id") or "商品"
    base_points = selling_points[:3]
    platform_rule = _platform_rule(platform)
    variants = [
        {
            "title": f"{short} {' '.join(base_points[:2])} {platform_rule['titleFocus'][0]}",
            "angle": "搜索关键词型",
            "fitPlatform": platform,
            "risk": "覆盖搜索词较稳，但内容爆点偏弱。",
        },
        {
            "title": f"{short} 解决{base_points[0]}问题 {'提升' if '提升' in task_goal else '日常好用'}",
            "angle": "场景痛点型",
            "fitPlatform": platform,
            "risk": "更适合内容流量，需避免夸大效果。",
        },
        {
            "title": f"{short} {base_points[0]}可视化 {base_points[1] if len(base_points) > 1 else '真实展示'}",
            "angle": "证据可信型",
            "fitPlatform": platform,
            "risk": "强调可信度，转化依赖主图证据。",
        },
    ]
    return variants


def _image_directions(product: Dict[str, Any], platform: str, selling_points: List[str], competitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    short = product.get("shortName") or product.get("title") or "商品"
    bad_reviews = [item.get("badReview") for item in competitors if item.get("badReview")]
    avoid_text = "；".join(_platform_rule(platform).get("avoid") or [])
    return [
        {
            "direction": "使用前后对比图",
            "layout": f"左侧展示未使用{short}前的痛点，右侧展示使用后的结果。",
            "coreText": f"{selling_points[0]}更直观",
            "evidence": "用真实场景表达，不做超出商品事实的承诺。",
            "avoid": avoid_text,
        },
        {
            "direction": "卖点证据图",
            "layout": f"把{selling_points[0]}、{selling_points[1] if len(selling_points) > 1 else '商品事实'}做成可视化证据。",
            "coreText": "看得见的卖点",
            "evidence": "用尺寸、容量、材质或场景对照增强可信度。",
            "avoid": "不要堆满小字，不要虚标规格。",
        },
        {
            "direction": "竞品差评反向图",
            "layout": f"围绕竞品痛点：{bad_reviews[0] if bad_reviews else '承诺不清晰'}，展示自家解决方式。",
            "coreText": "把差评变成说明点",
            "evidence": "只表达自家已具备的事实，不攻击竞品品牌。",
            "avoid": "不要直接点名竞品，不要使用无法证明的对比。",
        },
    ]


def _creative_patterns(product: Dict[str, Any], category_id: str, platform: str) -> Dict[str, Any]:
    rag = search_cases(
        query="标题 主图 转化 竞品 差评 卖点",
        category_id=category_id,
        platform=platform,
        store_id=product.get("storeId") or "global",
        problem_type="low_ctr_low_conversion",
        effective_only=False,
        limit=5,
    )
    if not rag.get("items"):
        rag = search_cases(
            query="竞品 差评 测试 卖点",
            category_id=category_id,
            platform=platform,
            store_id=product.get("storeId") or "global",
            problem_type="competitor_signal_to_test",
            effective_only=False,
            limit=5,
        )
    return rag


def _fit_traffic(angle: str, platform: str) -> str:
    if "搜索" in angle:
        return "搜索流量"
    if "场景" in angle or platform == "抖音小店":
        return "内容推荐 / 场景流量"
    if "差评" in angle or "证据" in angle:
        return "转化承接流量"
    return (_platform_rule(platform).get("trafficTypes") or ["推荐流量"])[0]


def _first_image_text(angle: str, selling_points: List[str]) -> str:
    if "搜索" in angle:
        return f"{selling_points[0]}更清楚"
    if "场景" in angle:
        return f"解决{selling_points[0]}问题"
    if "证据" in angle:
        return "看得见的卖点"
    return f"{selling_points[0]}可视化"


def _test_packages(
    *,
    product: Dict[str, Any],
    platform: str,
    task_goal: str,
    title_variants: List[Dict[str, Any]],
    main_image_directions: List[Dict[str, Any]],
    selling_points: List[str],
    patterns: Dict[str, Any],
) -> List[Dict[str, Any]]:
    packages: List[Dict[str, Any]] = []
    for index, title in enumerate(title_variants):
        image = main_image_directions[index % len(main_image_directions)]
        angle = title.get("angle") or f"方案 {index + 1}"
        package_name = f"方案 {chr(65 + index)}：{angle}"
        packages.append(
            {
                "packageId": f"PKG-{product.get('id') or product.get('productId') or 'product'}-{index + 1}",
                "packageName": package_name,
                "targetMetric": "点击率" if index < 2 else "点击率 + 转化承接",
                "taskGoal": task_goal,
                "title": title.get("title"),
                "titleAngle": angle,
                "mainImageDirection": image.get("direction"),
                "mainImageLayout": image.get("layout"),
                "firstImageText": _first_image_text(angle, selling_points),
                "sellingPointOrder": selling_points[:4],
                "fitPlatform": platform,
                "fitTraffic": _fit_traffic(angle, platform),
                "ragReferences": [case.get("caseId") for case in patterns.get("items") or []],
                "risk": title.get("risk") or image.get("avoid") or "必须避免夸大承诺。",
                "testDuration": "24-48 小时",
                "submitMetrics": DEFAULT_SUBMIT_METRICS,
                "operatorAction": [
                    "复制标题版本到测试商品或测试计划",
                    "按主图方向制作或选择对应图片",
                    "小流量测试 24-48 小时",
                    "记录曝光、点击率、转化率、收藏加购、退款率",
                    "提交胜出方案和异常说明",
                ],
                "reviewRule": "总管复核点击率是否提升，转化率是否同步下滑，退款率是否异常升高。",
            }
        )
    return packages


def _build_task_draft(
    *,
    product_id: str,
    product: Dict[str, Any],
    platform: str,
    category_profile: Dict[str, Any],
    category_id: str,
    task_goal: str,
    selling_points: List[str],
    patterns: Dict[str, Any],
    test_packages: List[Dict[str, Any]],
    selected_package: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    selected = selected_package or (test_packages[0] if test_packages else {})
    package_name = selected.get("packageName") or "标题主图测试包"
    title = f"上架测试{product.get('shortName') or product_id}{package_name}"
    return {
        "title": title,
        "task": f"运营不再自行想标题主图，直接选择 Agent 生成的{package_name}上架小流量测试。",
        "reason": f"当前目标：{task_goal}。平台：{platform}。类目：{category_profile.get('categoryName')}。",
        "priority": "中",
        "priorityLevel": "warning",
        "deadline": selected.get("testDuration") or "24-48 小时后复盘",
        "riskDomain": "标题主图",
        "actionType": "上架测试",
        "taskType": "V4.3 垂直类目创意测试",
        "taskSignal": "类目 Profile + 平台规则 + RAG 召回 + 竞品信号 + 测试包",
        "entityType": "商品",
        "entityId": product_id,
        "source": "V4.3 Creative Vertical Agent",
        "sourceModule": "标题主图垂直类目 Agent",
        "sourceRoute": "business-products",
        "productRoute": "business-products",
        "storeIds": [product.get("storeId")] if product.get("storeId") else [],
        "visibleStoreIds": [product.get("storeId")] if product.get("storeId") else [],
        "productId": product_id,
        "productTitle": product.get("title") or product_id,
        "productShort": product.get("shortName") or product_id,
        "platform": platform,
        "store": product.get("store") or "经营单元",
        "judgmentTags": ["creative_vertical", category_id, platform, *selling_points[:3]],
        "selectedPackage": selected,
        "testPackages": test_packages,
        "executionSteps": selected.get("operatorAction") or ["选择测试包", "上架小流量测试", "提交数据"],
        "evidenceRequired": selected.get("submitMetrics") or DEFAULT_SUBMIT_METRICS,
        "acceptanceCriteria": ["点击率是否提升", "转化率是否同步下滑", "退款率是否异常升高", "是否形成可复用标题 / 主图经验"],
        "agentJudgment": {
            "status": "advisory",
            "version": CREATIVE_AGENT_VERSION,
            "ragReferences": [case.get("caseId") for case in patterns.get("items") or []],
            "boundary": "Agent 生成测试包，运营负责上架测试和反馈结果，不直接发布到真实店铺。",
            "forbiddenActions": FORBIDDEN_ACTIONS,
        },
    }


def run_creative_vertical_agent(
    product_id: str,
    *,
    body: Dict[str, Any] | None = None,
    user_id: str | None = None,
) -> Dict[str, Any] | None:
    body = body or {}
    product = _product(product_id, body)
    if not product:
        return None
    category_id = body.get("categoryId") or product.get("categoryId") or DEFAULT_CATEGORY_ID
    platform = body.get("platform") or product.get("platform") or "通用"
    task_goal = body.get("taskGoal") or body.get("goal") or "提升点击率、转化率，并降低退款预期偏差"
    profile = _category_profile(category_id)
    platform_rule = _platform_rule(platform)
    competitors = _related_competitors(product, body)
    listings = _related_listings(product)
    selling_points = _selling_points(product, profile, competitors)
    patterns = _creative_patterns(product, category_id, platform)
    title_variants = _title_variants(product, platform, selling_points, task_goal)
    main_image_directions = _image_directions(product, platform, selling_points, competitors)
    test_packages = _test_packages(
        product=product,
        platform=platform,
        task_goal=task_goal,
        title_variants=title_variants,
        main_image_directions=main_image_directions,
        selling_points=selling_points,
        patterns=patterns,
    )
    selected_index = int(body.get("packageIndex", body.get("package_index", 0)) or 0)
    selected_package = test_packages[selected_index] if 0 <= selected_index < len(test_packages) else test_packages[0]
    test_plan = {
        "packages": [item.get("packageName") for item in test_packages],
        "metrics": DEFAULT_SUBMIT_METRICS,
        "sampleRule": "运营直接选择测试包上架小流量测试，不再从零想标题和主图。",
        "stopRule": "若退款率或违规风险升高，停止放大并回到任务复核。",
    }
    task_draft = _build_task_draft(
        product_id=product_id,
        product=product,
        platform=platform,
        category_profile=profile,
        category_id=category_id,
        task_goal=task_goal,
        selling_points=selling_points,
        patterns=patterns,
        test_packages=test_packages,
        selected_package=selected_package,
    )
    return {
        "version": CREATIVE_AGENT_VERSION,
        "agentName": "标题主图垂直类目 Agent",
        "viewer": _viewer(user_id),
        "productId": product_id,
        "taskGoal": task_goal,
        "productFacts": product,
        "categoryProfile": profile,
        "platformRule": platform_rule,
        "competitorSignals": competitors,
        "relatedListingTests": listings,
        "historicalCreativePatterns": patterns.get("items") or [],
        "ragReferences": [case.get("caseId") for case in patterns.get("items") or []],
        "categoryStrategy": f"{profile.get('categoryName')}优先表达：{'、'.join(selling_points[:4])}。{platform}侧重：{'、'.join(platform_rule.get('titleFocus') or [])}。",
        "titleVariants": title_variants,
        "mainImageDirections": main_image_directions,
        "sellingPointOrder": selling_points,
        "testPackages": test_packages,
        "selectedPackage": selected_package,
        "testPlan": test_plan,
        "taskDraft": task_draft,
        "humanDecision": ["选择要测试的方案", "确认是否需要补充竞品差评样本", "确认测试周期和复核指标"],
        "forbiddenActions": FORBIDDEN_ACTIONS,
        "boundary": "Agent 生成可复制上架的测试包，运营负责测试和反馈结果。",
    }


def create_creative_task(product_id: str, *, body: Dict[str, Any] | None = None, user_id: str | None = None) -> Dict[str, Any] | None:
    body = body or {}
    result = run_creative_vertical_agent(product_id, body=body, user_id=user_id)
    if not result:
        return None
    package_index = int(body.get("packageIndex", body.get("package_index", 0)) or 0)
    packages = result.get("testPackages") or []
    selected_package = packages[package_index] if 0 <= package_index < len(packages) else result.get("selectedPackage")
    task_draft = deepcopy(result["taskDraft"])
    task_draft["selectedPackage"] = selected_package
    task_draft["executionSteps"] = selected_package.get("operatorAction") if selected_package else task_draft.get("executionSteps")
    task_draft["evidenceRequired"] = selected_package.get("submitMetrics") if selected_package else task_draft.get("evidenceRequired")
    task = create_task(task_draft)
    return {"agent": result, "task": task, "selectedPackage": selected_package}
