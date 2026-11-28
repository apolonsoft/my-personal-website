"""Add users and password_reset_tokens tables.

Revision ID: 0002_auth_and_profile
Revises: 0001_initial_schema
Create Date: 2026-11-28 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "0002_auth_and_profile"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users and password_reset_tokens tables with indexes."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("password_hash", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=False),
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column("headline", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=False),
        sa.Column("bio", sqlmodel.sql.sqltypes.AutoString(length=4000), nullable=False),
        sa.Column("avatar_key", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column("avatar_url", sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=False),
        sa.Column("social_links_json", sqlmodel.sql.sqltypes.AutoString(length=4000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["avatar_key"], ["image_assets.object_key"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_password_reset_tokens_expires_at"),
        "password_reset_tokens",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_password_reset_tokens_token_hash"),
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_password_reset_tokens_user_id"),
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop password_reset_tokens and users tables."""
    op.drop_index(op.f("ix_password_reset_tokens_user_id"), table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_token_hash"), table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_expires_at"), table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_index(op.f("ix_users_is_active"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
