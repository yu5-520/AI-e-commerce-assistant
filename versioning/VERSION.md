Current Version: 11.12.0

V11.12｜轻量原子部署 + 共享 venv

主线：保留 releases / current 原子切换，但默认使用 shared/.venv 共享虚拟环境 → requirements 未变化时跳过 pip install → 版本一致性仍强校验，路由守卫默认 warn 不误杀低配 ECS → systemd 固定运行 current 代码 + shared venv → 运行时 health 仍为硬闸门，路由检查默认警告。
