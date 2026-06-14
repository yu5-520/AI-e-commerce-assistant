# Web Demo

这是一个静态前端原型，用于演示 AI + RPA + ERP + CRM 电商经营自动化工作台的三段式流程。

## 运行方式

直接用浏览器打开：

```text
web_demo/index.html
```

## 页面流程

```text
导入 Mock 数据
↓
生成 AI / RAG 诊断
↓
生成 RPA 任务草案
↓
查看人工确认项
```

## 当前定位

当前页面不连接真实后端，也不执行真实 ERP / CRM / 店铺后台操作。

它用于展示：

- ERP 数据摘要
- CRM 数据摘要
- 商品风险诊断
- 客户分层与售后敏感识别
- RPA 低风险任务草案
- Human-in-the-loop 人工确认边界

## 后续升级

后续可以将页面按钮连接到：

```bash
python -m src.run_demo
```

或者通过 API 调用后端工作流，返回真实 JSON 输出并渲染到页面。
