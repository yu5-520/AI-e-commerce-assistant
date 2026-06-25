Current Version: 11.11.0

V11.11｜部署原子化 + 版本一致性守卫

主线：ECS 不再作为半开发环境原地 git pull 运行 → 新版本 clone 到独立 releases 目录 → VERSION / FastAPI app.version / health.API_VERSION / 前端资源版本 / 关键路由全部一致才允许切换 current → systemd 固定运行 current 软链接 → 健康检查失败自动回滚上一版 → fetch 失败不再继续 reset 到旧缓存。
