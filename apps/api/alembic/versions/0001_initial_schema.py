"""Initial schema for image_assets and posts tables.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-28 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create image_assets and posts tables with indexes."""
    op.create_table(
        "image_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("object_key", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=False),
        sa.Column("filename", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("content_type", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("alt_text", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_image_assets_object_key"),
        "image_assets",
        ["object_key"],
        unique=True,
    )

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=300), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("category", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("hero_image_key", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column("hero_image_url", sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=False),
        sa.Column("image_alt", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.Column("pub_date", sa.DateTime(), nullable=False),
        sa.Column("updated_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["hero_image_key"], ["image_assets.object_key"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_posts_category"), "posts", ["category"], unique=False)
    op.create_index(op.f("ix_posts_pub_date"), "posts", ["pub_date"], unique=False)
    op.create_index(op.f("ix_posts_published"), "posts", ["published"], unique=False)
    op.create_index(op.f("ix_posts_slug"), "posts", ["slug"], unique=True)


def downgrade() -> None:
    """Drop posts and image_assets tables."""
    op.drop_index(op.f("ix_posts_slug"), table_name="posts")
    op.drop_index(op.f("ix_posts_published"), table_name="posts")
    op.drop_index(op.f("ix_posts_pub_date"), table_name="posts")
    op.drop_index(op.f("ix_posts_category"), table_name="posts")
    op.drop_table("posts")
    op.drop_index(op.f("ix_image_assets_object_key"), table_name="image_assets")
    op.drop_table("image_assets")
