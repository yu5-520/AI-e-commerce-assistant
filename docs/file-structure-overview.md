# 文件结构总览

```text
AI-e-commerce-assistant/
├── README.md
├── docs/                 # 产品、架构、演示、求职与复盘文档
├── examples/             # Mock ERP / CRM 数据
├── knowledge_base/        # 简单 RAG 知识片段
├── src/                  # Python Mock Workflow
│   ├── data_loader/
│   ├── diagnosis/
│   ├── rag/
│   ├── rpa_tasks/
│   ├── approval/
│   ├── reports/
│   └── run_demo.py
├── schemas/              # JSON Schema 数据契约
├── prompts/              # Prompt 模板
├── workflows/            # 工作流定义
├── evals/                # Evals 样例和运行器
└── web_demo/             # 静态前端 Demo
```

## 核心入口

运行主流程：

```bash
python -m src.run_demo
```

运行评测：

```bash
python evals/run_evals.py
```

打开前端：

```text
web_demo/index.html
```

## 当前版本

V6：前端三段式 Demo。

下一版本：V7 API 可交互 Demo。
