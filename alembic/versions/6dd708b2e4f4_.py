"""empty message

Revision ID: 6dd708b2e4f4
Revises: b626a67b9740
Create Date: 2026-08-29 13:53:58.071266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6dd708b2e4f4'
down_revision: Union[str, Sequence[str], None] = 'b626a67b9740'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # 1. customer_balance_adjustments — новая таблица, без изменений
    # ------------------------------------------------------------------
    op.create_table(
        'customer_balance_adjustments',
        sa.Column('customer_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('debt_before', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('debt_after', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('prepayment_before', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('prepayment_after', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_customer_balance_adjustments_customer_id'),
                     'customer_balance_adjustments', ['customer_id'], unique=False)
    op.create_index(op.f('ix_customer_balance_adjustments_user_id'),
                     'customer_balance_adjustments', ['user_id'], unique=False)

    # ------------------------------------------------------------------
    # 2. route_customers -> orders: ПЕРЕИМЕНОВАНИЕ, данные сохраняются
    # ------------------------------------------------------------------
    op.rename_table('route_customers', 'orders')

    # 2a. enum delivery_status: убираем значение PAID (Postgres не умеет
    # удалять значения enum напрямую — пересоздаём тип и переносим данные).
    # РЕШЕНИЕ: строки со статусом PAID переводятся в DELIVERED, т.к. факт
    # оплаты теперь живёт отдельно в payments/payment_method.
    # !! Подтвердить с продуктом, что это верный маппинг !!
    op.execute("ALTER TYPE delivery_status RENAME TO delivery_status_old")
    op.execute("CREATE TYPE delivery_status AS ENUM ('PENDING', 'ON_WAY', 'DELIVERED', 'FAILED')")
    op.execute("""
        ALTER TABLE orders
        ALTER COLUMN status DROP DEFAULT
    """)
    op.execute("""
        ALTER TABLE orders
        ALTER COLUMN status TYPE delivery_status
        USING (
            CASE WHEN status::text = 'PAID' THEN 'DELIVERED' ELSE status::text END
        )::delivery_status
    """)
    op.execute("DROP TYPE delivery_status_old")

    # 2b. order -> sequence: переименование колонки, не drop+add
    op.alter_column('orders', 'order', new_column_name='sequence')

    # 2c. индексы переименовываем вместо drop+create (мгновенно, без rebuild)
    op.execute("ALTER INDEX ix_route_customers_route_id RENAME TO ix_orders_route_id")
    op.execute("ALTER INDEX ix_route_customers_customer_id RENAME TO ix_orders_customer_id")

    # 2d. переименовываем ограничения для консистентности имён (не обязательно
    # функционально, но избавляет от "route_customers_..." в имени orders-таблицы)
    op.execute("ALTER TABLE orders RENAME CONSTRAINT route_customers_pkey TO orders_pkey")
    op.execute(
        "ALTER TABLE orders RENAME CONSTRAINT route_customers_customer_id_fkey "
        "TO orders_customer_id_fkey"
    )
    op.execute(
        "ALTER TABLE orders RENAME CONSTRAINT route_customers_route_id_fkey "
        "TO orders_route_id_fkey"
    )

    # 2e. новые колонки orders
    op.add_column('orders', sa.Column('returned_bottles', sa.Integer(), server_default='0', nullable=True))
    op.add_column('orders', sa.Column('damaged_bottles', sa.Integer(), server_default='0', nullable=True))
    op.add_column('orders', sa.Column('bottle_balance_after', sa.Integer(), nullable=True))
    op.add_column('orders', sa.Column('bulk_5l_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('orders', sa.Column('bulk_5l_price', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=True))
    op.add_column('orders', sa.Column('bulk_10l_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('orders', sa.Column('bulk_10l_price', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=True))
    op.add_column('orders', sa.Column('picked_coolers', sa.Integer(), server_default='0', nullable=True))
    op.add_column('orders', sa.Column('picked_bottles', sa.Integer(), server_default='0', nullable=True))
    op.add_column('orders', sa.Column('water_price_applied', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=True))
    op.add_column('orders', sa.Column('damaged_fine_applied', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=True))
    op.add_column('orders', sa.Column('order_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=True))
    order_purpose_enum = postgresql.ENUM(
        'DELIVERY_19L', 'PICKUP', 'BULK_WATER',
        name='order_purpose',
        create_type=False,
    )
    order_purpose_enum.create(bind, checkfirst=True)

    op.add_column('orders', sa.Column(
        'purpose', order_purpose_enum,
        server_default='DELIVERY_19L', nullable=True,
    ))

    op.add_column('orders', sa.Column('moved_from_route_id', sa.UUID(), nullable=True))
    op.add_column('orders', sa.Column('moved_at', sa.DateTime(timezone=True), nullable=True))

    op.create_index(op.f('ix_orders_moved_from_route_id'), 'orders', ['moved_from_route_id'], unique=False)
    op.create_foreign_key(
        None, 'orders', 'routes', ['moved_from_route_id'], ['id'], ondelete='CASCADE',
    )

    # 2f. номер заказа: бэкафилл в хронологическом порядке, потом IDENTITY
    op.add_column('orders', sa.Column('number', sa.BigInteger(), nullable=True))
    op.execute("""
        UPDATE orders o
        SET number = sub.rn
        FROM (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) AS rn
            FROM orders
        ) sub
        WHERE o.id = sub.id
    """)
    op.alter_column('orders', 'number', nullable=False)
    op.execute("""
        DO $$
        DECLARE
            next_number bigint;
        BEGIN
            SELECT COALESCE(MAX(number), 0) + 1 INTO next_number FROM orders;
            EXECUTE format(
                'ALTER TABLE orders ALTER COLUMN number ADD GENERATED BY DEFAULT AS IDENTITY (START WITH %s INCREMENT BY 1)',
                next_number
            );
        END $$;
    """)
    op.create_unique_constraint('orders_number_key', 'orders', ['number'])

    # ------------------------------------------------------------------
    # 3. route_expenses — новая таблица, без изменений
    # ------------------------------------------------------------------
    op.create_table(
        'route_expenses',
        sa.Column('route_id', sa.UUID(), nullable=False),
        sa.Column('driver_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('category', sa.Enum('FUEL', 'LUNCH', 'REPAIR', 'OTHER', name='expense_category'),
                  server_default='OTHER', nullable=False),
        sa.Column('comment', sa.String(length=255), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_route_expenses_driver_id'), 'route_expenses', ['driver_id'], unique=False)
    op.create_index(op.f('ix_route_expenses_route_id'), 'route_expenses', ['route_id'], unique=False)

    # ------------------------------------------------------------------
    # 4. customers: has_cooler -> cooler_count, с бэкафиллом
    # ------------------------------------------------------------------
    op.add_column('customers', sa.Column('cooler_count', sa.Integer(), server_default='0', nullable=False))
    op.execute("UPDATE customers SET cooler_count = 1 WHERE has_cooler = true")
    op.add_column('customers', sa.Column('custom_water_price', sa.Numeric(precision=12, scale=2), nullable=True))
    op.drop_column('customers', 'has_cooler')

    # ------------------------------------------------------------------
    # 5. payments: route_customer_id -> order_id (переименование, не drop+add!)
    # ------------------------------------------------------------------
    op.drop_constraint(op.f('payments_route_customer_id_key'), 'payments', type_='unique')
    op.drop_constraint(op.f('payments_route_customer_id_fkey'), 'payments', type_='foreignkey')
    op.alter_column('payments', 'route_customer_id', new_column_name='order_id')
    op.create_foreign_key(None, 'payments', 'orders', ['order_id'], ['id'], ondelete='SET NULL')

    op.add_column('payments', sa.Column('note', sa.String(length=255), nullable=True))

    # recorded_by_user_id: NOT NULL по спеке, но на непустой таблице у нас нет
    # исторических данных о том, кто провёл старые платежи. Решаем безопасно:
    # если таблица пустая (свежее окружение) — сразу NOT NULL;
    # если есть строки — оставляем nullable и громко предупреждаем,
    # NOT NULL накатывается отдельной миграцией после ручного бэкафилла.
    payments_count = bind.execute(text("SELECT COUNT(*) FROM payments")).scalar()

    op.add_column('payments', sa.Column('recorded_by_user_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_payments_recorded_by_user_id'), 'payments', ['recorded_by_user_id'], unique=False)
    op.create_foreign_key(None, 'payments', 'users', ['recorded_by_user_id'], ['id'], ondelete='RESTRICT')

    if payments_count == 0:
        op.alter_column('payments', 'recorded_by_user_id', nullable=False)
    else:
        print(
            f"[6dd708b2e4f4] ВНИМАНИЕ: {payments_count} существующих payments не имеют "
            "recorded_by_user_id. Колонка оставлена nullable. Требуется ручной бэкафилл "
            "и отдельная миграция с ALTER COLUMN ... SET NOT NULL, прежде чем полагаться "
            "на это поле как на обязательное в коде."
        )

    # ------------------------------------------------------------------
    # 6. price_settings / routes — без изменений
    # ------------------------------------------------------------------
    op.add_column('price_settings', sa.Column(
        'damaged_bottle_fine', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False,
    ))
    op.alter_column('routes', 'driver_id', existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column('routes', 'driver_id', existing_type=sa.UUID(), nullable=False)
    op.drop_column('price_settings', 'damaged_bottle_fine')

    # payments: откатываем recorded_by_user_id / note / order_id -> route_customer_id
    op.drop_constraint(op.f('ix_payments_recorded_by_user_id'), 'payments', type_='index')
    op.drop_constraint(None, 'payments', type_='foreignkey')  # recorded_by_user_id fk
    op.drop_column('payments', 'recorded_by_user_id')
    op.drop_column('payments', 'note')

    op.drop_constraint(None, 'payments', type_='foreignkey')  # order_id fk
    op.alter_column('payments', 'order_id', new_column_name='route_customer_id')
    op.create_foreign_key(
        op.f('payments_route_customer_id_fkey'), 'payments', 'orders',
        ['route_customer_id'], ['id'], ondelete='SET NULL',
    )
    op.create_unique_constraint(
        op.f('payments_route_customer_id_key'), 'payments', ['route_customer_id'],
    )

    # customers: cooler_count -> has_cooler, с обратным бэкафиллом
    op.add_column('customers', sa.Column(
        'has_cooler', sa.BOOLEAN(), server_default=sa.text('false'), nullable=False,
    ))
    op.execute("UPDATE customers SET has_cooler = (cooler_count > 0)")
    op.drop_column('customers', 'custom_water_price')
    op.drop_column('customers', 'cooler_count')

    # route_expenses
    op.drop_index(op.f('ix_route_expenses_route_id'), table_name='route_expenses')
    op.drop_index(op.f('ix_route_expenses_driver_id'), table_name='route_expenses')
    op.drop_table('route_expenses')

    # orders -> route_customers: откатываем номер, purpose, доп.колонки, enum
    op.drop_constraint('orders_number_key', 'orders', type_='unique')
    op.execute("ALTER TABLE orders ALTER COLUMN number DROP IDENTITY IF EXISTS")
    op.drop_column('orders', 'number')

    op.drop_constraint(None, 'orders', type_='foreignkey')  # moved_from_route_id fk
    op.drop_index(op.f('ix_orders_moved_from_route_id'), table_name='orders')
    op.drop_column('orders', 'moved_at')
    op.drop_column('orders', 'moved_from_route_id')
    op.drop_column('orders', 'completed_at')
    op.drop_column('orders', 'purpose')
    op.execute("DROP TYPE IF EXISTS order_purpose")
    op.drop_column('orders', 'order_amount')
    op.drop_column('orders', 'damaged_fine_applied')
    op.drop_column('orders', 'water_price_applied')
    op.drop_column('orders', 'picked_bottles')
    op.drop_column('orders', 'picked_coolers')
    op.drop_column('orders', 'bulk_10l_price')
    op.drop_column('orders', 'bulk_10l_count')
    op.drop_column('orders', 'bulk_5l_price')
    op.drop_column('orders', 'bulk_5l_count')
    op.drop_column('orders', 'bottle_balance_after')
    op.drop_column('orders', 'damaged_bottles')
    op.drop_column('orders', 'returned_bottles')

    op.execute("ALTER TABLE orders RENAME CONSTRAINT orders_pkey TO route_customers_pkey")
    op.execute(
        "ALTER TABLE orders RENAME CONSTRAINT orders_customer_id_fkey "
        "TO route_customers_customer_id_fkey"
    )
    op.execute(
        "ALTER TABLE orders RENAME CONSTRAINT orders_route_id_fkey "
        "TO route_customers_route_id_fkey"
    )
    op.execute("ALTER INDEX ix_orders_route_id RENAME TO ix_route_customers_route_id")
    op.execute("ALTER INDEX ix_orders_customer_id RENAME TO ix_route_customers_customer_id")

    op.alter_column('orders', 'sequence', new_column_name='order')

    # enum: возвращаем PAID (данные, ушедшие в DELIVERED при апгрейде, не восстановить —
    # это ожидаемая необратимость даунгрейда после lossy-маппинга)
    op.execute("ALTER TYPE delivery_status RENAME TO delivery_status_new")
    op.execute(
        "CREATE TYPE delivery_status AS ENUM ('PENDING', 'ON_WAY', 'DELIVERED', 'FAILED', 'PAID')"
    )
    op.execute("""
        ALTER TABLE orders
        ALTER COLUMN status TYPE delivery_status
        USING status::text::delivery_status
    """)
    op.execute("DROP TYPE delivery_status_new")

    op.rename_table('orders', 'route_customers')

    # customer_balance_adjustments
    op.drop_index(op.f('ix_customer_balance_adjustments_user_id'), table_name='customer_balance_adjustments')
    op.drop_index(op.f('ix_customer_balance_adjustments_customer_id'), table_name='customer_balance_adjustments')
    op.drop_table('customer_balance_adjustments')