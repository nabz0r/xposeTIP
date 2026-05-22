"""S155 — Synthetic test for S150 _create_pe_graph_edges idempotency.

Validates the get-or-create branch that the smoke (commit 05299a1) could
not reliably exercise: forces a pre-existing Identity tuple and proves
the function reuses it without IntegrityError instead of inserting a
duplicate.

Runs inside the api container via:
  docker compose exec api pytest tests/test_create_pe_graph_edges.py -v

Requires a live Postgres connection (same as the running stack).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sqlalchemy import select, func, delete

from api.tasks.utils import get_sync_session
from api.models.workspace import Workspace
from api.models.target import Target
from api.models.identity import Identity, IdentityLink
from api.services.layer4.public_exposure_enricher import _create_pe_graph_edges


SMOKE_WS_SLUG = "_s155_smoke"


@pytest.fixture
def smoke_workspace():
    """Throwaway workspace + target + email anchor + 1 pre-existing
    media_mention Identity. Cleaned up at teardown.

    Returns a dict with workspace_id, target_id, email_node_id, and
    existing_mm_id — UUIDs only, no ORM objects (avoids cross-session
    detached-instance issues since each test opens its own session).
    """
    session = get_sync_session()
    try:
        # Cleanup any leftover from a previous failed run
        leftover = session.execute(
            select(Workspace).where(Workspace.slug == SMOKE_WS_SLUG)
        ).scalar_one_or_none()
        if leftover:
            session.execute(delete(Workspace).where(Workspace.id == leftover.id))
            session.commit()

        ws = Workspace(name="_S155 Smoke", slug=SMOKE_WS_SLUG, plan="free")
        session.add(ws)
        session.flush()

        target = Target(
            workspace_id=ws.id,
            email="s155@smoke.test",
            status="completed",
        )
        session.add(target)
        session.flush()

        email_node = Identity(
            workspace_id=ws.id,
            target_id=target.id,
            type="email",
            value="s155@smoke.test",
            confidence=1.0,
        )
        session.add(email_node)

        existing_mm = Identity(
            workspace_id=ws.id,
            target_id=target.id,
            type="media_mention",
            value="https://example.com/preexisting-article",
            platform="public_exposure",
            source_module="public_exposure",
            confidence=0.6,
        )
        session.add(existing_mm)
        session.commit()

        ids = {
            "workspace_id": ws.id,
            "target_id": target.id,
            "email_node_id": email_node.id,
            "existing_mm_id": existing_mm.id,
        }
        yield ids
    finally:
        # Cleanup — cascade delete on Workspace removes targets/identities/links
        try:
            session.execute(delete(Workspace).where(Workspace.slug == SMOKE_WS_SLUG))
            session.commit()
        except Exception:
            session.rollback()
        session.close()


def _count_media_mentions(session, target_id):
    return session.execute(
        select(func.count()).select_from(Identity).where(
            Identity.target_id == target_id,
            Identity.type == "media_mention",
        )
    ).scalar()


def _count_links_to(session, dest_id):
    return session.execute(
        select(func.count()).select_from(IdentityLink).where(
            IdentityLink.dest_id == dest_id,
        )
    ).scalar()


def test_reuses_existing_identity_on_duplicate_value(smoke_workspace):
    """S150 KEY ASSERTION: when a media_mention Identity with the same
    (workspace_id, target_id, type, value) already exists, the function
    must reuse it (get-or-create branch) and NOT insert a duplicate.
    Pre-S150 this raised IntegrityError silently and lost data."""
    session = get_sync_session()
    try:
        target = session.execute(
            select(Target).where(Target.id == smoke_workspace["target_id"])
        ).scalar_one()
        existing_mm_id = smoke_workspace["existing_mm_id"]

        n_mm_before = _count_media_mentions(session, target.id)
        assert n_mm_before == 1, "Fixture should have seeded exactly 1 media_mention"

        finding_dict = {
            "indicator_value": "https://example.com/preexisting-article",
            "indicator_type": "media_mention",
            "title": "Rescan article",
            "data": {"scraper": "google_news_rss"},
            "confidence": 0.7,
        }

        _create_pe_graph_edges([finding_dict], target, session)
        session.flush()

        n_mm_after = _count_media_mentions(session, target.id)
        assert n_mm_after == n_mm_before, (
            f"Identity duplicated: before={n_mm_before} after={n_mm_after}. "
            "S150 regression — get-or-create branch did not reuse existing row."
        )

        # IdentityLink should have been created on this first call
        link = session.execute(
            select(IdentityLink).where(
                IdentityLink.dest_id == existing_mm_id,
                IdentityLink.link_type == "mentioned_in",
            )
        ).scalar_one_or_none()
        assert link is not None, "IdentityLink not created on first call"
    finally:
        session.close()


def test_second_call_does_not_duplicate_link(smoke_workspace):
    """ANTI-DUPLICATION ASSERTION: calling _create_pe_graph_edges twice
    with the same input must produce exactly 1 IdentityLink, not 2."""
    session = get_sync_session()
    try:
        target = session.execute(
            select(Target).where(Target.id == smoke_workspace["target_id"])
        ).scalar_one()
        existing_mm_id = smoke_workspace["existing_mm_id"]

        finding_dict = {
            "indicator_value": "https://example.com/preexisting-article",
            "indicator_type": "media_mention",
            "title": "Rescan article",
            "data": {"scraper": "google_news_rss"},
            "confidence": 0.7,
        }

        # First call — creates the link
        _create_pe_graph_edges([finding_dict], target, session)
        session.flush()
        assert _count_links_to(session, existing_mm_id) == 1, "First call should create 1 link"

        # Second call — must reuse, not duplicate
        _create_pe_graph_edges([finding_dict], target, session)
        session.flush()
        assert _count_links_to(session, existing_mm_id) == 1, (
            "IdentityLink duplicated on second call — S150 IdentityLink get-or-create regression."
        )
    finally:
        session.close()


def test_new_value_still_creates_identity_and_link(smoke_workspace):
    """NEGATIVE CASE: a finding_dict with a value NOT in the DB must
    create both a new Identity and a new IdentityLink. Proves the
    existing-Identity branch isn't over-applied to all inputs."""
    session = get_sync_session()
    try:
        target = session.execute(
            select(Target).where(Target.id == smoke_workspace["target_id"])
        ).scalar_one()

        finding_dict = {
            "indicator_value": "https://newsource.com/brand-new-article",
            "indicator_type": "media_mention",
            "title": "Brand new article",
            "data": {"scraper": "gdelt"},
            "confidence": 0.8,
        }

        n_mm_before = _count_media_mentions(session, target.id)

        _create_pe_graph_edges([finding_dict], target, session)
        session.flush()

        n_mm_after = _count_media_mentions(session, target.id)
        assert n_mm_after == n_mm_before + 1, (
            f"Brand-new Identity not inserted: before={n_mm_before} after={n_mm_after}. "
            "Either the get-or-create branch is over-applied, or the INSERT path is broken."
        )

        # New IdentityLink should exist for the new Identity
        new_mm = session.execute(
            select(Identity).where(
                Identity.target_id == target.id,
                Identity.value == "https://newsource.com/brand-new-article",
            )
        ).scalar_one_or_none()
        assert new_mm is not None, "New media_mention Identity not found"

        link = session.execute(
            select(IdentityLink).where(
                IdentityLink.dest_id == new_mm.id,
                IdentityLink.link_type == "mentioned_in",
            )
        ).scalar_one_or_none()
        assert link is not None, "IdentityLink for new Identity not created"
    finally:
        session.close()
