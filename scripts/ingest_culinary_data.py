"""CLI script to ingest culinary knowledge records into the SQLite database."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.core.logging import setup_logging
from backend.app.db.connection import get_db_manager
from backend.app.db.schema import init_database
from backend.app.services.rag.ingestion import KnowledgeIngestionService


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest culinary knowledge from JSON or CSV file.")
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        default="backend/app/db/fixtures/demo_culinary_kb.json",
        help="Path to JSON or CSV file to ingest",
    )
    parser.add_argument(
        "--allow-overwrite-verified",
        action="store_true",
        default=False,
        help="Allow unverified imports to overwrite verified existing records",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        default=True,
        help="Initialize database schema and tables before ingesting",
    )
    args = parser.parse_args()

    setup_logging(level="INFO")
    db_mgr = get_db_manager()

    if args.init_db:
        print("[*] Initializing SQLite schema, FTS5 virtual tables, and sqlite-vec...")
        init_database(db_mgr)

    target_path = Path(args.file)
    if not target_path.is_absolute():
        target_path = project_root / target_path

    if not target_path.exists():
        print(f"[!] Error: File not found at {target_path}", file=sys.stderr)
        return 1

    print(f"[*] Ingesting culinary knowledge from: {target_path} ...")
    ingestion_service = KnowledgeIngestionService(db_manager=db_mgr)

    if target_path.suffix.lower() == ".json":
        summary = ingestion_service.ingest_from_json_file(
            target_path,
            allow_overwrite_verified=args.allow_overwrite_verified,
        )
    elif target_path.suffix.lower() == ".csv":
        summary = ingestion_service.ingest_from_csv_file(
            target_path,
            allow_overwrite_verified=args.allow_overwrite_verified,
        )
    else:
        print(f"[!] Unsupported file extension: {target_path.suffix}. Expected .json or .csv", file=sys.stderr)
        return 1

    print("========================================")
    print("Ingestion Summary:")
    print(f"  Batch Import ID: {summary.import_id}")
    print(f"  Source:          {summary.source_name}")
    print(f"  Total Records:   {summary.total_records}")
    print(f"  Inserted:        {summary.inserted}")
    print(f"  Updated:         {summary.updated}")
    print(f"  Skipped/Errors:  {summary.skipped}")
    if summary.errors:
        print("\nWarnings / Row Errors:")
        for err in summary.errors:
            print(f"  - Row {err.get('row')}: {err.get('identifier')} -> {err.get('error')}")
    print("========================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
