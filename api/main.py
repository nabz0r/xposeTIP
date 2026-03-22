from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.config import settings
from api.database import engine
from api.routers import auth, targets, scans, findings, modules, graph, system, settings as settings_router, workspaces, accounts, scrapers, events


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Install structured logging to Redis
    from api.services.log_handler import setup_logging
    setup_logging(redis_url=settings.REDIS_URL, container="api")

    import logging as _logging
    _logging.getLogger("api").info("xpose API started — Redis log handler active, v0.28.0")

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
    version="0.28.0",
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
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])


@app.post("/api/v1/scan/quick")
async def quick_scan(request_body: dict):
    """Quick scan endpoint — no auth required, limited modules, rate limited by IP.

    Creates target in 'public' workspace, dispatches async scan via Celery,
    returns scan_id for polling. Cached results returned immediately if recent.
    """
    from datetime import datetime, timezone
    from fastapi import HTTPException
    from sqlalchemy import select as sa_select
    from api.database import async_session
    from api.models.workspace import Workspace
    from api.models.target import Target
    from api.models.scan import Scan

    email = (request_body.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email required")

    # Rate limit via Redis (5 scans/hour/email)
    try:
        import redis as r
        rc = r.from_url(settings.REDIS_URL)
        key = f"quickscan:{email}"
        count = rc.incr(key)
        if count == 1:
            rc.expire(key, 3600)
        if count > 5:
            rc.close()
            raise HTTPException(status_code=429, detail="Rate limit: 3 quick scans per hour. Create a free account for more.")
        rc.close()
    except HTTPException:
        raise
    except Exception:
        pass

    QUICK_MODULES = ["email_validator", "dns_deep", "holehe", "gravatar", "geoip"]

    async with async_session() as db:
        # Get or create public workspace
        result = await db.execute(sa_select(Workspace).where(Workspace.slug == "public"))
        public_ws = result.scalar_one_or_none()
        if not public_ws:
            public_ws = Workspace(name="Quick Scans", slug="public", plan="free")
            db.add(public_ws)
            await db.flush()

        # Check if target already exists in public workspace
        result = await db.execute(
            sa_select(Target).where(Target.email == email, Target.workspace_id == public_ws.id)
        )
        target = result.scalar_one_or_none()

        # If recently scanned, return cached teaser
        if target and target.profile_data and target.last_scanned:
            age = (datetime.now(timezone.utc) - target.last_scanned).total_seconds()
            if age < 86400:
                await db.commit()
                return _build_teaser(target)

        if not target:
            target = Target(email=email, workspace_id=public_ws.id, status="pending")
            db.add(target)
            await db.flush()

        # Create scan with limited modules
        scan = Scan(
            target_id=target.id,
            workspace_id=public_ws.id,
            status="pending",
            modules=QUICK_MODULES,
            module_progress={m: "queued" for m in QUICK_MODULES},
        )
        db.add(scan)
        target.status = "scanning"
        await db.commit()

        scan_id = str(scan.id)
        target_id = str(target.id)

    # Dispatch Celery task
    try:
        from api.tasks.scan_orchestrator import launch_scan
        launch_scan.delay(scan_id)
    except Exception:
        pass

    return {
        "status": "scanning",
        "target_id": target_id,
        "scan_id": scan_id,
        "email": email,
        "message": "Scan started. Results in ~20 seconds.",
    }


@app.get("/api/v1/scan/quick/{scan_id}/status")
async def quick_scan_status(scan_id: str):
    """Poll quick scan status — no auth required."""
    import uuid as _uuid
    from fastapi import HTTPException
    from sqlalchemy import select as sa_select
    from api.database import async_session
    from api.models.scan import Scan
    from api.models.target import Target

    async with async_session() as db:
        result = await db.execute(sa_select(Scan).where(Scan.id == _uuid.UUID(scan_id)))
        scan = result.scalar_one_or_none()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        if scan.status not in ("completed", "failed"):
            return {"status": scan.status, "scan_id": str(scan.id)}

        result = await db.execute(sa_select(Target).where(Target.id == scan.target_id))
        target = result.scalar_one_or_none()
        if not target:
            return {"status": "completed", "scan_id": str(scan.id)}

        return _build_teaser(target)


def _build_teaser(target):
    """Build teaser response for quick scan — limited data with upsell."""
    profile = target.profile_data or {}
    fp = profile.get("fingerprint", {})
    teaser = profile.get("quick_teaser", {})

    return {
        "status": "completed",
        "target_id": str(target.id),
        "email": target.email,
        "teaser": {
            "display_name": profile.get("primary_name", ""),
            "avatar_seed": fp.get("avatar_seed"),
            "exposure_score": target.exposure_score or 0,
            "threat_score": target.threat_score or 0,
            "fingerprint_axes": fp.get("axes", {}),
            "fingerprint_risk": fp.get("risk_level", "LOW"),
            "accounts_count": len(profile.get("social_profiles", [])),
            "sources_count": len(profile.get("data_sources", [])),
            "top_findings": teaser.get("top_findings", []),
            "total_findings": teaser.get("total_findings", 0),
        },
        "upsell": {
            "message": "Create a free account to see the full report",
            "features": ["Identity estimation", "Persona clustering", "Digital fingerprint", "Remediation plan"],
            "cta_url": f"/setup?email={target.email}",
        },
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
