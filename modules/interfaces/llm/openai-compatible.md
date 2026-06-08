# OpenAI-compatible 接口模块

统一使用 /chat/completions。

输入：system prompt、user prompt、model、api key、base url。

输出：choices[0].message.content。

原则：workflow 不写模型细节；模型切换通过环境变量和 provider registry 完成。