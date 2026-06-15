# Product Docs

本目录只保存当前产品本体相关文档，不放简历、面试、HR 展示、旧 demo 规划或未来多页面蓝图。

## 当前文档结构

```text
CHANGELOG.md                         产品更新日志：产品定位、主链路、页面/API 边界变更
mvp-scope.md                         当前 MVP 范围与验收标准
module-boundary.md                   当前模块边界与不做什么
product-decision-log.md              重大产品决策日志
product-structure-cleanup-log.md     产品结构清理日志
```

## 当前产品主线

```text
ERP / CRM Mock 数据
↓
经营单元识别
↓
循环频率策略
↓
商品体检、竞品机会、上新建议、流量复盘
↓
经营循环总控
↓
/api/business/* 产品接口
↓
web_demo/index.html + web_demo/app-v2.js
```

## 当前原则

- 先跑通当前单页产品闭环，再讨论未来多页面信息架构。
- 当前主线以 README、`src/api/main.py`、`/api/business/*` 和 smoke tests 为准。
- 旧 demo、旧 Agent、旧兼容接口、旧页面规划不放在当前产品文档里。
- 产品主链路、页面结构、API 边界或产品定位发生变化时，必须同步更新 `CHANGELOG.md`。
- 结构级清理还必须同步更新 `versioning/CHANGELOG.md` 和 `versioning/VERSION.md`。
