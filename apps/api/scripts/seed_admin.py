"""Idempotent CLI script for headless default admin user onboarding."""

import argparse
import os
from typing import Any

import httpx


def onboard_default_admin(
    client: Any,
    *,
    email: str,
    password: str,
    full_name: str,
    headline: str = "",
) -> bool:
    """Create the default admin user if not already initialized.

    Returns True if a new admin was created, False if already initialized.
    """
    status_res = client.get("/api/auth/onboarding/status")
    status_res.raise_for_status()
    if status_res.json().get("initialized"):
        return False

    res = client.post(
        "/api/auth/onboarding",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "headline": headline,
        },
    )
    if res.status_code == 409:
        return False
    res.raise_for_status()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Onboard default admin user.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8787")
    parser.add_argument(
        "--email",
        default=os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@apolonsoft.dev"),
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!"),
    )
    parser.add_argument(
        "--full-name",
        default=os.environ.get("DEFAULT_ADMIN_NAME", "Apolonsoft Admin"),
    )
    parser.add_argument(
        "--headline",
        default=os.environ.get("DEFAULT_ADMIN_HEADLINE", "Developers & Designers"),
    )
    args = parser.parse_args()

    with httpx.Client(base_url=args.api_url, timeout=30.0) as client:
        created = onboard_default_admin(
            client,
            email=args.email,
            password=args.password,
            full_name=args.full_name,
            headline=args.headline,
        )

    if created:
        print(f"Created default admin user: {args.email}")
    else:
        print("Admin onboarding already completed; skipped.")


if __name__ == "__main__":
    main()
