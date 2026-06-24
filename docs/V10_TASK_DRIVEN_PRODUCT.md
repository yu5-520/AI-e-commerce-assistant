# V10 Task Driven Product

V10 turns the system from an architecture-ready SaaS base into a task-driven AI operating product.

## Core rule

```text
用户只完成任务，系统和 Agent 自动完成理解、分类、标签、流转、同步和留痕。
```

## Product principles

```text
凡是需要用户介入的事情，都以任务形式出现。
凡是系统能自动判断的事情，不让用户手动配置。
标签是 Agent 的工作语言，不是用户的工作负担。
前端展示用户动作，不展示系统复杂度。
```

## Minimal navigation

```text
总览
报表
经营
任务
日志
账号
系统
```

## V10.1 navigation compression

```text
商品、竞品、上新、流量不再占用左侧主导航。
这些经营对象折叠到“经营”页面内部，用轻入口或页内标签进入。
旧路由继续保留，用于内部跳转、详情页、任务卡跳转和后续经营页轻标签。
账号权限 visibleModules 需要映射到 V10 主导航，避免旧模块列表误隐藏新入口。
```

## User actions

```text
老板：查看 / 关注 / 确认
总管：派发 / 通过 / 驳回
运营：接收 / 提交 / 补充
```

## Task types

```text
经营处理任务
报表补充任务
标签变化任务
权重复核任务
跨账号复核任务
系统确认任务
```

## Agent automation scope

```text
垂直类目标签
店铺权重标签
商品角色标签
风险标签
任务强度
跨账号流转
审计留痕
```

## V10 update rhythm

```text
V10.0 任务驱动产品原则
V10.1 主导航压缩
V10.2 UI 排版产品化
V10.3 总览改成今日任务台
V10.4 报表导入驱动任务
V10.5 跨账号任务自动流转
V10.6 任务操作极简化
V10.7 Agent 自动标签与经营档案
V10.8 标签变化任务
V10.9 任务驱动验收守卫
```
