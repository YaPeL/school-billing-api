"""add invoice status and payment kind

Revision ID: 2f4d3a9a6c7b
Revises: b4648ffcc29d
Create Date: 2026-02-24 16:25:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2f4d3a9a6c7b"
down_revision = "b4648ffcc29d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    invoice_status = sa.Enum("PENDING", "PARTIAL", "PAID", name="invoice_status")
    payment_kind = sa.Enum("PAYMENT", "REFUND", name="payment_kind")
    invoice_status.create(op.get_bind(), checkfirst=True)
    payment_kind.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "invoices",
        sa.Column("status", invoice_status, nullable=True, server_default=sa.text("'PENDING'")),
    )
    op.add_column(
        "payments",
        sa.Column("kind", payment_kind, nullable=True, server_default=sa.text("'PAYMENT'")),
    )

    op.execute("UPDATE payments SET kind = 'PAYMENT' WHERE kind IS NULL")
    op.execute("UPDATE invoices SET status = 'PENDING' WHERE status IS NULL")

    op.execute(
        """
        WITH invoice_net_paid AS (
            SELECT
                p.invoice_id,
                COALESCE(SUM(
                    CASE
                        WHEN p.kind = 'PAYMENT' THEN p.amount
                        ELSE -p.amount
                    END
                ), 0) AS net_paid
            FROM payments p
            GROUP BY p.invoice_id
        )
        UPDATE invoices i
        SET status = CASE
            WHEN n.net_paid = 0 THEN 'PENDING'::invoice_status
            WHEN n.net_paid < i.total_amount THEN 'PARTIAL'::invoice_status
            ELSE 'PAID'::invoice_status
        END
        FROM invoice_net_paid n
        WHERE i.id = n.invoice_id
        """
    )

    op.alter_column("payments", "kind", nullable=False, server_default=sa.text("'PAYMENT'"))
    op.alter_column("invoices", "status", nullable=False, server_default=sa.text("'PENDING'"))


def downgrade() -> None:
    op.drop_column("payments", "kind")
    op.drop_column("invoices", "status")

    payment_kind = sa.Enum("PAYMENT", "REFUND", name="payment_kind")
    invoice_status = sa.Enum("PENDING", "PARTIAL", "PAID", name="invoice_status")
    payment_kind.drop(op.get_bind(), checkfirst=True)
    invoice_status.drop(op.get_bind(), checkfirst=True)
