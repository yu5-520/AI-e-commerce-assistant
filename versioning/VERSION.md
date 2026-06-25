Current Version: 11.4.0

V11.4｜后端账号隔离安全闸

主线：生产模式禁止信任 X-Mock-User-Id → 统一 UserContext 认证边界 → Repository 查询强制 tenant + org + data scope → 严格模式下缺 tenant/org/store 归属的数据进入隔离区，不进入经营模块 → 账号页只展示数据范围，不展示账号绑定店铺。
