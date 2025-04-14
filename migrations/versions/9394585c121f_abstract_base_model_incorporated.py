"""abstract base model incorporated

Revision ID: 9394585c121f
Revises: 80ab3a78d0a2
Create Date: 2025-04-13 08:41:08.064818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9394585c121f'
down_revision: Union[str, None] = '80ab3a78d0a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.alter_column('is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False)
        batch_op.alter_column('is_deleted',
               existing_type=sa.BOOLEAN(),
               nullable=False)

    with op.batch_alter_table('user_tokens', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=6), nullable=True))

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_tokens', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('is_deleted')
        batch_op.drop_column('is_active')

    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.alter_column('is_deleted',
               existing_type=sa.BOOLEAN(),
               nullable=True)
        batch_op.alter_column('is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    # ### end Alembic commands ###
