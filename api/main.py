from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.config import settings
from api.database import engine
from api.routers import auth, targets, scans, findings, modules, graph, system, settings as settings_router, workspaces, accounts, scrapers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Install structured logging to Redis
    from api.services.log_handler import setup_logging
    setup_logging(redis_url=settings.REDIS_URL, container="api")

    import logging as _logging
    _logging.getLogger("api").info("xpose API started — Redis log handler active, v0.18.0")

    # Fernet encryption health check
    try:
        from api.routers.settings import _get_fernet
        f = _get_fernet()
        test = f.encrypt(b"test")
        f.decrypt(test)
        _logging.getLogger("api").info("Fernet encryption healthy")
    except Exception:
        _logging.getLogger("api").error("Fernet encryption broken — check SECRET_KEY in .env")

    # Optional syslog forwarding
    if settings.SYSLOG_HOST:
        import logging
        from logging.handlers import SysLogHandler
        proto = SysLogHandler.TCP_LOG_HOST if settings.SYSLOG_PROTOCOL == "tcp" else None
        syslog_handler = SysLogHandler(
            address=(settings.SYSLOG_HOST, settings.SYSLOG_PORT),
            socktype=__import__("socket").SOCK_STREAM if settings.SYSLOG_PROTOCOL == "tcp" else __import__("socket").SOCK_DGRAM,
        )
        syslog_handler.setFormatter(logging.Formatter("xpose[%(name)s]: %(levelname)s %(message)s"))
        logging.getLogger().addHandler(syslog_handler)

    yield
    await engine.dispose()


app = FastAPI(
    title="xpose",
    description="Identity Threat Intelligence Platform",
    version="0.20.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(targets.router, prefix="/api/v1/targets", tags=["targets"])
app.include_router(scans.router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(findings.router, prefix="/api/v1/findings", tags=["findings"])
app.include_router(modules.router, prefix="/api/v1/modules", tags=["modules"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["graph"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(settings_router.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])
app.include_router(scrapers.router, prefix="/api/v1/scrapers", tags=["scrapers"])


@app.post("/api/v1/scan/quick")
async def quick_scan(request_body: dict):
    """Quick scan endpoint — no auth required, limited modules, rate limited.

    For the landing page demo. Runs only fast, free scanners.
    Returns results inline (not async).
    """
    import asyncio
    from datetime import datetime, timezone, timedelta

    email = request_body.get("email", "").strip()
    if not email or "@" not in email:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Valid email required")

    # Rate limit: check Redis for IP-based limiting
    try:
        import redis as r
        rc = r.from_url(settings.REDIS_URL)
        # Simple rate limit: 5 scans per hour per email
        key = f"quickscan:{email}"
        count = rc.incr(key)
        if count == 1:
            rc.expire(key, 3600)
        if count > 5:
            from fastapi import HTTPException
            raise HTTPException(status_code=429, detail="Rate limit: max 5 quick scans per email per hour")
        rc.close()
    except Exception:
        pass  # If Redis fails, allow the scan

    # Run only fast, free modules synchronously
    quick_modules = ["email_validator", "dns_deep", "geoip"]
    all_findings = []

    for module_id in quick_modules:
        try:
            from api.tasks.module_tasks import _get_scanner
            scanner = _get_scanner(module_id)
            if not scanner:
                continue
            loop = asyncio.new_event_loop()
            try:
                results = loop.run_until_complete(scanner.scan(email))
            finally:
                loop.close()
            for result in results:
                all_findings.append({
                    "module": result.module,
                    "severity": result.severity,
                    "title": result.title,
                    "description": result.description,
                    "category": result.category,
                })
        except Exception:
            pass

    return {
        "email": email,
        "findings": all_findings,
        "total": len(all_findings),
        "modules_run": quick_modules,
        "note": "Quick scan — sign up for full 25-module analysis",
    }


@app.get("/health")
async def health():
    db_ok = False
    redis_ok = False
    try:
        from api.database import async_session
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass
    try:
        import redis as r
        rc = r.from_url(settings.REDIS_URL)
        rc.ping()
        redis_ok = True
        rc.close()
    except Exception:
        pass
    return {"status": "ok" if (db_ok and redis_ok) else "degraded", "db": db_ok, "redis": redis_ok}


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check — infrastructure, workers, queue depth."""
    import time
    start = time.time()
    checks = {}

    # PostgreSQL
    try:
        from api.database import async_session
        async with async_session() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            pool = engine.pool
            checks["postgresql"] = {
                "status": "healthy",
                "version": version,
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }
    except Exception as e:
        checks["postgresql"] = {"status": "unhealthy", "error": str(e)}

    # Redis
    try:
        import redis as r
        rc = r.from_url(settings.REDIS_URL)
        rc.ping()
        info = rc.info("server")
        memory = rc.info("memory")
        checks["redis"] = {
            "status": "healthy",
            "version": info.get("redis_version"),
            "used_memory_human": memory.get("used_memory_human"),
            "connected_clients": rc.info("clients").get("connected_clients", 0),
        }
        rc.close()
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # Celery workers
    try:
        from api.tasks import celery_app
        inspector = celery_app.control.inspect(timeout=2.0)
        active = inspector.active() or {}
        reserved = inspector.reserved() or {}
        stats = inspector.stats() or {}
        worker_names = list(stats.keys())
        checks["celery"] = {
            "status": "healthy" if worker_names else "unhealthy",
            "workers": len(worker_names),
            "active_tasks": sum(len(t) for t in active.values()),
            "reserved_tasks": sum(len(t) for t in reserved.values()),
        }
    except Exception as e:
        checks["celery"] = {"status": "unhealthy", "error": str(e)}

    # Queue depth
    try:
        import redis as r
        rc = r.from_url(settings.REDIS_URL)
        queue_depth = rc.llen("celery")
        checks["queue"] = {"celery": queue_depth}
        rc.close()
    except Exception:
        checks["queue"] = {"celery": -1}

    elapsed = round((time.time() - start) * 1000, 1)
    all_healthy = all(
        c.get("status") == "healthy"
        for c in checks.values()
        if isinstance(c, dict) and "status" in c
    )

    return {
        "status": "ok" if all_healthy else "degraded",
        "checks": checks,
        "response_time_ms": elapsed,
    }
