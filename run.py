import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "false").lower() in ("true", "1", "yes")

    print("=" * 60)
    print("🚀 启动智服云 CoreDesk - 全渠道智能客服中台 (Phase 1 至 Phase 5)")
    print(f"🔗 访问地址: http://{host}:{port}")
    print("⚡ 核心架构: JEV 网关 + CQRS 账务 + Auto-Pilot + Action Agent + QA & 知识飞轮")
    print("=" * 60)
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)

