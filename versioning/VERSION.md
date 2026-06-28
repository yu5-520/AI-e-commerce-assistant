Current Version: 12.6.1

V12.6.1｜商品档案 findOpenTask 前端断点修复

主线：保留 V12.6 的 RAG经营动作权限闸门、系统估算、自动确认/主管审批流，同时修复商品档案页进入后因任务动作桥接函数不完整导致的 `findOpenTask is not a function`。现在 AppTaskStore 和 AppTaskActions 都提供 findOpenTask，task-actions 兼容旧缓存和空任务池，任务查询失败不会阻断商品档案渲染。
