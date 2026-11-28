"""Export Alembic revisions into Wrangler D1-compatible SQL migration files."""

import argparse
from io import StringIO
from pathlib import Path
import re

from alembic import command
from alembic.config import Config

API_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = API_ROOT / "migrations_d1"

def strip_non_d1_statements(raw_sql: str) -> str:
    """Remove transaction wrappers and alembic_version statements for Cloudflare D1."""
    kept_statements: list[str] = []
    for statement in raw_sql.split(";"):
        stmt = statement.strip()
        if not stmt:
            continue
        # Remove leading comment-only lines from a statement when checking its type
        non_comment = "\n".join(
            line for line in stmt.splitlines() if not line.strip().startswith("--")
        ).strip()
        if not non_comment:
            continue
        if re.match(r"^(?:BEGIN(?:\s+TRANSACTION)?|COMMIT)$", non_comment, re.IGNORECASE):
            continue
        if "alembic_version" in non_comment.lower():
            continue
        kept_statements.append(f"{stmt};")
    return "\n\n".join(kept_statements) + ("\n" if kept_statements else "")


def export_revision_sql(revision_range: str, output_file: Path) -> Path:
    """Render Alembic SQL for `revision_range` and write a D1-ready SQL file."""
    buffer = StringIO()
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    cfg.output_buffer = buffer

    command.upgrade(cfg, revision_range, sql=True)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(strip_non_d1_statements(buffer.getvalue()), encoding="utf-8")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Alembic migration to Cloudflare D1 SQL.")
    parser.add_argument(
        "--revision",
        default="head",
        help="Alembic revision or range (e.g. '0001_initial_schema' or 'base:head').",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUT_DIR / "0001_initial_schema.sql",
        help="Target SQL file path inside migrations_d1/.",
    )
    args = parser.parse_args()
    written = export_revision_sql(args.revision, args.output)
    print(f"Wrote D1 migration SQL to {written}")


if __name__ == "__main__":
    main()
