# Demo 维护说明

## 1. 修改 Mock 数据

Mock 数据位于：

```text
examples/
```

修改后运行：

```bash
python -m src.run_demo
```

检查 outputs 是否更新。

## 2. 修改诊断规则

商品诊断：

```text
src/diagnosis/product_diagnosis.py
```

客户分层：

```text
src/diagnosis/customer_segmentation.py
```

## 3. 修改 RAG 知识片段

知识库位于：

```text
knowledge_base/
```

修改后运行：

```bash
python -m src.run_demo
```

检查：

```text
outputs/rag_retrieval_context.json
```

## 4. 修改前端展示

页面：

```text
web_demo/index.html
web_demo/styles.css
web_demo/app.js
```

如果只改展示文案，优先改 `app.js` 里的样例数据。

## 5. 修改 Evals

评测入口：

```text
evals/run_evals.py
```

评测样例：

```text
evals/*.json
```

## 6. 维护原则

- 不引入真实客户隐私。
- 不新增自动改价、自动投放、自动群发等高风险能力。
- 每次新增能力都要说明是否需要人工确认。
- 每次新增输出都尽量结构化为 JSON。
