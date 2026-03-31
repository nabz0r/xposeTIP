"""Standalone test script for Discovery Engine.

Usage:
    # Mock mode (no API key, no DB — pure logic test)
    python -m api.discovery.test_discovery --mock

    # Dry run with real SerpAPI (needs SERPAPI_KEY)
    python -m api.discovery.test_discovery --mock --real-search

    # With real target from DB
    python -m api.discovery.test_discovery --target-id UUID --dry-run

Options:
    --mock          Use hardcoded test profile + MockSearchClient
    --real-search   Use real SerpAPI (needs SERPAPI_KEY env var)
    --dry-run       Print results, don't write to DB
    --target-id     UUID of existing scanned target
    --max-queries   Override query budget (default: 5)
    --max-pages     Override page budget (default: 10)
"""
import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

MOCK_PROFILE = {
    "identifiers": [
        {"type": "username", "value": "nabz0r"},
        {"type": "email", "value": "nabil@test.com"},
    ],
    "resolved_name": "Nabil Ksontini",
    "axes": {"developer_activity": 0.85, "gaming_presence": 0.6},
    "geo_country": "LU",
    "platforms_found": ["github.com", "steam.com", "chess.com"],
}


def main():
    parser = argparse.ArgumentParser(description="Discovery Engine test")
    parser.add_argument("--mock", action="store_true", help="Use mock profile")
    parser.add_argument("--real-search", action="store_true", help="Use real SerpAPI")
    parser.add_argument("--dry-run", action="store_true", help="Print only, no DB writes")
    parser.add_argument("--target-id", type=str, help="Target UUID")
    parser.add_argument("--max-queries", type=int, default=5)
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    from api.discovery.query_generator import DiscoveryBudget
    from api.discovery.pipeline import DiscoveryPipeline

    budget = DiscoveryBudget(
        max_queries=args.max_queries,
        max_pages=args.max_pages,
        max_seconds=120,
    )

    if args.mock and not args.real_search:
        # Force mock search client
        os.environ.pop("SERPAPI_KEY", None)

    if args.mock:
        print("=" * 60)
        print("Discovery Engine Test — MOCK MODE")
        print("=" * 60)

        # Show generated queries
        from api.discovery.query_generator import QueryGenerator
        gen = QueryGenerator()
        queries = gen.generate(MOCK_PROFILE, max_queries=args.max_queries)
        print(f"\nGenerated {len(queries)} queries:")
        for q in queries:
            print(f"  [{q['priority']}] {q['template_id']}: {q['query'][:80]}")
            print(f"       reason: {q['reason']}")

        # Run pipeline
        print(f"\nRunning pipeline (dry_run=True)...")
        pipeline = DiscoveryPipeline(
            target_id="mock",
            budget=budget,
            dry_run=True,
        )
        result = pipeline.run(profile_snapshot=MOCK_PROFILE)
        print(f"\nResult: {result}")

    elif args.target_id:
        print("=" * 60)
        print(f"Discovery Engine Test — TARGET {args.target_id}")
        print(f"dry_run=True (test script always dry-run)")
        print("=" * 60)

        from api.tasks.utils import get_sync_session
        session = get_sync_session()

        try:
            # Pass DB session even in dry-run — needed for quality gate + profile builder
            # Only DB WRITES are skipped in dry-run mode
            pipeline = DiscoveryPipeline(
                target_id=args.target_id,
                budget=budget,
                db_session=session,
                dry_run=True,
            )
            # Build profile and show quality gate stats
            profile = pipeline._build_profile_snapshot(args.target_id)
            if profile:
                print(f"\nProfile: {len(profile.get('identifiers', []))} identifiers, "
                      f"name={profile.get('resolved_name')}, "
                      f"geo={profile.get('geo_country')}, "
                      f"{len(profile.get('platforms_found', []))} platforms")
                print(f"Quality gate: {len(pipeline.quality_gate.known_identifiers)} identifiers, "
                      f"{len(pipeline.quality_gate.known_platforms)} platforms loaded")

            result = pipeline.run(profile_snapshot=profile)
            print(f"\nResult: {result}")
        finally:
            session.close()
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python -m api.discovery.test_discovery --mock")
        print("  python -m api.discovery.test_discovery --target-id UUID --dry-run")


if __name__ == "__main__":
    main()
