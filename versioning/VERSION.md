Current Version: 11.13.0

V11.13｜Demo 快速部署模式

主线：Demo 阶段高频小改不再走 releases/current 原子发布 → 新增 scripts/deploy_fast.sh → 日常更新只执行 fetch / reset / 版本一致性检查 / systemd 重启 / health 检查 → 不 clone release、不重建 venv、不默认 pip install → 阶段版本仍保留 deploy_atomic.sh，客户环境再走完整发布。
