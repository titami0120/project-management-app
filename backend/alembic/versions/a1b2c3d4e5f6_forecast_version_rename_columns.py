"""forecast_version: replace trigger_type/note with name/description

Revision ID: a1b2c3d4e5f6
Revises: 5fdbdff17f7b
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5fdbdff17f7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("forecast_versions") as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("description", sa.String(500), nullable=True))

    op.execute("UPDATE forecast_versions SET name = COALESCE(note, trigger_type)")

    with op.batch_alter_table("forecast_versions") as batch_op:
        batch_op.alter_column("name", nullable=False)
        batch_op.drop_column("trigger_type")
        batch_op.drop_column("note")


def downgrade() -> None:
    with op.batch_alter_table("forecast_versions") as batch_op:
        batch_op.add_column(sa.Column("trigger_type", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("note", sa.String(500), nullable=True))

    op.execute("UPDATE forecast_versions SET trigger_type = 'manual', note = name")

    with op.batch_alter_table("forecast_versions") as batch_op:
        batch_op.alter_column("trigger_type", nullable=False)
        batch_op.drop_column("name")
        batch_op.drop_column("description")
