"""add keys secrets

Revision ID: 4323fa6b57bb
Revises: f7664a50c0ac
Create Date: 2022-09-05 23:19:49.233078

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4323fa6b57bb"
down_revision = "f7664a50c0ac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "secrets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_secrets_id"), "secrets", ["id"], unique=False)
    op.create_table(
        "keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("secret_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["content.id"],
        ),
        sa.ForeignKeyConstraint(
            ["secret_id"],
            ["secrets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_keys_id"), "keys", ["id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_keys_id"), table_name="keys")
    op.drop_table("keys")
    op.drop_index(op.f("ix_secrets_id"), table_name="secrets")
    op.drop_table("secrets")
    # ### end Alembic commands ###
