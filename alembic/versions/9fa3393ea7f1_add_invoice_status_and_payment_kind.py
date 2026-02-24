"""add invoice status and payment kind

Revision ID: 9fa3393ea7f1
Revises: b4648ffcc29d
Create Date: 2026-02-24 00:00:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9fa3393ea7f1"
down_revision = "b4648ffcc29d"
branch_labels = None
depends_on = None

invoice_status_enum = sa.Enum("PENDING", "PARTIAL", "PAID", name="invoice_status")
payment_kind_enum = sa.Enum("PAYMENT", "REFUND", name="payment_kind")


def upgrade() -> None:
    bind = op.get_bind()

    payment_kind_enum.create(bind, checkfirst=True)
    invoice_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "payments",
        sa.Column(
            "kind",
            payment_kind_enum,
            nullable=False,
            server_default=sa.text("'PAYMENT'"),
        ),
    )

    op.add_column(
        "invoices",
        sa.Column(
            "status",
            invoice_status_enum,
            nullable=True,
            server_default=sa.text("'PENDING'"),
        ),
    )

    op.execute("UPDATE invoices SET status = 'PENDING'")
    op.execute(
        """
        UPDATE invoices
        SET status = CASE
            WHEN p.net_paid = 0 THEN 'PENDING'::invoice_status
            WHEN p.net_paid < invoices.total_amount THEN 'PARTIAL'::invoice_status
            ELSE 'PAID'::invoice_status
        END
        FROM (
            SELECT invoice_id, COALESCE(SUM(amount), 0) AS net_paid
            FROM payments
            GROUP BY invoice_id
        ) AS p
        WHERE invoices.id = p.invoice_id
        """
    )

    op.alter_column("invoices", "status", nullable=False)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_column("invoices", "status")
    op.drop_column("payments", "kind")

    invoice_status_enum.drop(bind, checkfirst=True)
    payment_kind_enum.drop(bind, checkfirst=True)
