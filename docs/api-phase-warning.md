# API 阶段注意事项

进入 V7 后，不要一次性接真实 ERP / CRM。

第一步只做：

```text
FastAPI 包装当前 Mock Workflow
```

不要做：

- 真实账号登录
- 真实店铺后台操作
- 真实客户数据导入
- 自动改价
- 自动投放
- 自动群发

V7 的目标只是：

> 前端可以调用后端，展示真实 Python Workflow 输出。
