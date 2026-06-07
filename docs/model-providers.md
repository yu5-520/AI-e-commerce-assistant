# 大模型接口配置说明

本仓库使用统一 OpenAI-compatible 调用层。

## GitHub Actions 配置

在仓库 Settings 中配置：

Repository Variables:
- LLM_ENABLED=true
- LLM_PROVIDER=deepseek
- LLM_MODEL=deepseek-chat
- LLM_BASE_URL=可选，自定义供应商才需要

Repository Secrets:
- LLM_API_KEY=你的模型平台 API Key

## 支持的 provider

配置文件：config/model_providers.json

当前内置：
- openai
- deepseek
- qwen_dashscope
- moonshot
- zhipu
- minimax
- baichuan
- stepfun
- siliconflow
- volcengine_ark
- tencent_hunyuan
- baidu_qianfan
- custom

## DeepSeek 示例

Variables:
- LLM_ENABLED=true
- LLM_PROVIDER=deepseek
- LLM_MODEL=deepseek-chat

Secrets:
- LLM_API_KEY=DeepSeek API Key

## 通义千问 / DashScope 示例

Variables:
- LLM_ENABLED=true
- LLM_PROVIDER=qwen_dashscope
- LLM_MODEL=qwen-plus

Secrets:
- LLM_API_KEY=DashScope API Key

## 自定义 OpenAI-compatible 示例

Variables:
- LLM_ENABLED=true
- LLM_PROVIDER=custom
- LLM_BASE_URL=https://your-provider.example.com/v1
- LLM_MODEL=your-model-name

Secrets:
- LLM_API_KEY=你的 API Key

## 设计原则

workflow 不写供应商细节，只传通用环境变量。

新增模型时优先修改 config/model_providers.json；如果模型平台兼容 /chat/completions，就不需要改 workflow。
