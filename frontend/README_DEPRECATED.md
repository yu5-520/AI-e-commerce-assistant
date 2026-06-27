# frontend 已废弃

本目录是历史资产，不是当前 UI 修改依据。

## 当前前端入口

```text
web_demo/
```

## 禁止事项

```text
不要把 frontend/ 当作当前产品入口。
不要基于 frontend/ 修改 UI、路由、接口契约或页面状态。
不要把 frontend/ 中的旧页面逻辑同步回 web_demo/，除非先在 docs/MODULE_CHAIN.md 明确迁移链路。
```

## 当前规则

V12.3 之后，AI 修改仓库时必须优先读取：

```text
README.md
docs/MODULE_CHAIN.md
docs/API_CONTRACT.md
web_demo/core/api-client.js
web_demo/modules/*
src/api/main.py
src/api/routes/*
src/services/*
```

`frontend/` 只用于历史参考，不参与当前部署、不参与当前产品验收。
