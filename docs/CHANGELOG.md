# CHANGELOG

## V10.9.0

任务驱动验收守卫。

- 新增 `src/services/v109_acceptance_guard_service.py`，固定 V10 任务驱动产品的端到端验收链。
- V10 readiness 增加 `acceptanceGuard`、`acceptanceChain`、`acceptanceRules` 和 `blockingFailures`。
- 验收链覆盖报表导入、V10.4 模块刷新、V10.7 经营档案、Agent 自动标签、V10.8 标签变化任务、任务池可见、V10.5 跨账号视图、V10.6 极简动作、日志留痕和 RAG 记忆候选。
- 系统状态页展示 V10.9 验收链路、验收规则和阻断失败项。
- V10 守卫升级为端到端验收：导入测试数据、生成标签变化任务、三端查看任务、运营接收提交、总管复核通过，并检查 RAG 记忆候选草案。
- V10.9 不新增日常操作功能，只收束产品闭环。

## V10.8.0

标签变化任务。

- 新增 `src/services/v108_tag_change_task_service.py`，将 V10.7 的 `tagChangeTaskCandidates` 写入统一任务池。
- 导入接口在 `v107OperatingProfile` 之后返回 `v108TagChangeTaskSync`。
- 标签变化任务带上经营档案快照 `profileSnapshot`，避免后续标签变化后历史判断不可追溯。
- 标签变化任务复用 V10.5 跨账号视图和 V10.6 极简任务动作。
- 用户不确认标签、不手动分类，只在标签变化形成任务时处理。
- V10 readiness 增加 `tagChangeTaskRules` 和 `tagChangeTaskFlow`。
- 系统状态页展示 V10.8 标签变化任务规则。
- V10 守卫增加候选转任务、任务池可见、导入返回同步结果和角色视图检查。

## V10.7.0

Agent 自动标签与经营档案。

- 新增 `src/services/v107_operating_profile_service.py`，导入店铺 / 商品信息后自动生成 Agent 经营档案。
- 导入接口在 `v104ImportTaskSync` 外额外返回 `v107OperatingProfile`，包含店铺档案、商品档案、自动标签和标签变化任务候选。
- 自动标签覆盖垂直类目、店铺权重、商品角色、风险和任务强度。
- 标签是 Agent 的工作语言，`userConfirmationRequired=false`；用户默认不确认标签，只保留修改权。
- 商品或店铺数据持续走低时，系统生成 `tag_change_task` 候选，让用户以任务形式介入。
- V10 readiness 增加 `operatingProfileRules`、`operatingProfileTagTypes` 和 `operatingProfileSurfaces`。
- 系统状态页展示 V10.7 Agent 经营档案规则。
- V10 守卫增加经营档案服务、导入返回经营档案、无需用户确认标签和标签变化任务候选检查。

## V10.6.0

任务操作极简化。

- 新增 `src/services/v106_task_action_simplifier.py`，将任务卡动作压缩为一个主动作和一个次动作。
- `/api/modules/todo` 返回 `taskActionSurface`、`simplifiedActions`、`primaryTaskAction`、`secondaryTaskAction` 和 `visibleTaskActions`。
- 老板动作固定为查看 / 关注 / 确认，总管动作固定为派发 / 通过 / 驳回，运营动作固定为接收 / 提交 / 补充。
- 任务页从多按钮操作栏收束为 V10.6 极简动作栏，详情不再被算作流程动作。
- 拆分、置顶、排序、来源跳转等低频动作不再占用任务卡主操作位，后端事件和日志继续保留完整链路。
- 系统状态页展示 V10.6 任务操作规则。
- V10 守卫增加 task action simplifier、todo 动作投射、任务页极简动作和运行态接口检查。

## V10.5.0

跨账号任务自动流转。

- 新增 `src/services/v105_cross_account_flow_service.py`，将同一个任务投射成老板、总管、运营三种角色视图。
- 任务接口 `/api/modules/todo` 返回 `crossAccountFlow`、`roleViewStatus`、`displayStatus` 和 `primaryRoleActions`。
- 老板账号看到进度视图，总管账号看到派发 / 复核视图，运营账号看到接收 / 提交 / 补充视图。
- 运营提交后自动进入总管待复核，总管复核后老板同步看到完成结果。
- 任务页展示“当前视图”和“下一同步”，减少用户理解流程节点的成本。
- 系统状态页展示 V10.5 跨账号任务流转规则和角色动作。
- V10 守卫增加跨账号 service、todo role projection、任务页展示和运行态接口检查。

## V10.4.0

报表导入驱动任务。

- 新增 `src/services/v104_import_task_sync_service.py`，将现有 V3/V6 报表导入结果包装成 V10.4 前端刷新契约。
- `/api/data/import/confirm`、`/api/data/import/report`、`/api/data/import/mock-alerts` 统一返回 `v104ImportTaskSync`。
- V10.4 契约固定 `updatedModules`、`frontendRefreshTargets`、`createdTaskCount`、`summary` 和 `nextAction`。
- 前端报表页上传后显示“已更新，生成 X 个任务”，并同步刷新总览、经营、任务、报表、日志。
- `AppApi.refreshAfterDataImport(result)` 接收导入结果，刷新任务、报表、总览和日志状态。
- 系统状态页展示 V10.4 报表导入驱动任务流程和刷新契约。
- V10 守卫增加导入接口、V10.4 契约、报表页刷新和导入结果检查。

## V10.3.0

总览深化为今日任务台。

- 固定总览五块结构：今日优先任务、高风险事项、最新报表结果、待复核事项、今日完成进度。
- `/api/modules/dashboard` 返回 `dashboardMode=today_task_workbench` 与 `todayWorkbench`，前端不再自己猜任务台结构。
- 总览 UI 从指标看板深化为任务工作台，优先任务成为主区域，高风险、待复核、完成进度进入右侧辅助区。
- 新增 `web_demo/v103-workbench.css`，独立承载今日任务台布局样式。
- 系统状态页展示 V10.3 今日任务台结构和规则。
- V10 守卫增加 dashboard service、todayWorkbench、五块结构和任务台样式检查。

## V10.2.0

UI 排版产品化。

- 固定 V10.2 排版规则：标题区压缩、说明文字最小化、主操作区放大、数据流转默认折叠。
- 前端缓存升级为 `?v=10.2.0`。
- 总览页升级为“今日任务台”，首屏突出处理任务，不再以系统展示为中心。
- 新增报表页入口，上传报表成为报表页主操作，并将同步结果压缩为状态条。
- 系统状态页展示 V10.2 产品化排版规则，不与日常经营界面争抢视觉空间。
- V10 守卫增加排版、报表页、任务台和首屏主动作检查。

## V10.1.0

主导航压缩。

- 左侧主导航压缩为总览、报表、经营、任务、日志、账号、系统七个大入口。
- 商品、竞品、上新、流量不再占用主导航，折叠进入经营模块内部轻入口。
- 保留商品、竞品、上新、流量旧路由，用于内部跳转、详情页和后续经营页轻标签。
- 前端启动层增加 V10 主导航映射，避免旧账号 visibleModules 把新主导航误隐藏。
- V10 contract 增加 navigationRouteMap、collapsedOperationRoutes 和 navigationCompressionRules。

## V10.0.0

任务驱动产品起版。

- 将产品主线从“企业交付验收一致性”推进到“任务驱动型 AI 经营系统”。
- 固定原则：用户只完成任务，系统和 Agent 自动完成理解、分类、标签、流转、同步和留痕。
- 新增 `/api/architecture/v10/task-driven-product` 与 `/api/architecture/v10/readiness`。
- 固定前端主导航收缩方向：总览、报表、经营、任务、日志、账号、系统。
- 固定角色动作：老板查看/关注/确认，总管派发/通过/驳回，运营接收/提交/补充。
- 固定任务类型：经营处理、报表补充、标签变化、权重复核、跨账号复核、系统确认。
- 标签不作为用户默认配置项，而是 Agent 的工作语言；需要用户介入的标签变化以任务形式出现。

## V9.9.0

交付验收一致性收口。

- 固定仓库、运行态、API、前端、企业边界、部署验收六段检查流程。
- 新增 V9.9 delivery readiness contract，形成最终交付前的 readiness 证据链。
- 暴露 `/api/architecture/v9/delivery-readiness` 与 `/api/architecture/v9/readiness`。
- 前端缓存版本统一为 `?v=9.9.0`，降低服务器旧页面残留风险。
- 架构守卫升级为 V9.9 运行态入口检查。
