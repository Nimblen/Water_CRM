"""empty message

Revision ID: 00129265b738
Revises: 339e1f278863
Create Date: 2026-08-12 17:17:47.710359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00129265b738'
down_revision: Union[str, Sequence[str], None] = '339e1f278863'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    payment_method_enum = sa.Enum(
        'CASH',
        'CARD',
        'TRANSFER',
        'DEBT',
        name='payment_method',
    )

    payment_method_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.add_column(
        'payments',
        sa.Column(
            'payment_method',
            payment_method_enum,
            nullable=True,
        ),
    )


    op.execute(
        """
        UPDATE payments
        SET payment_method = 'CASH'
        WHERE payment_method IS NULL
        """
    )

    op.alter_column(
        'payments',
        'payment_method',
        existing_type=payment_method_enum,
        nullable=False,
    )

    op.add_column(
        'route_customers',
        sa.Column(
            'payment_method',
            payment_method_enum,
            nullable=True,
        ),
    )

    op.drop_column('route_customers', 'payment_photo')
    op.drop_column('route_customers', 'payment_amount')


def downgrade() -> None:
    payment_method_enum = sa.Enum(
        'CASH',
        'CARD',
        'TRANSFER',
        'DEBT',
        name='payment_method',
    )

    op.add_column(
        'route_customers',
        sa.Column(
            'payment_amount',
            sa.NUMERIC(
                precision=12,
                scale=2,
            ),
            nullable=True,
        ),
    )

    op.add_column(
        'route_customers',
        sa.Column(
            'payment_photo',
            sa.VARCHAR(length=500),
            nullable=True,
        ),
    )

    op.drop_column(
        'route_customers',
        'payment_method',
    )

    op.drop_column(
        'payments',
        'payment_method',
    )

    payment_method_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )