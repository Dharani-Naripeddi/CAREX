"""Add Phase 4 support services tables (lab, pharmacy, billing, notifications)

Revision ID: c1f8a42b9102
Revises: 4a17b1386984
Create Date: 2026-09-02 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1f8a42b9102'
down_revision = '4a17b1386984'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Lab Tests
    op.create_table(
        'lab_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sample_type', sa.String(length=100), nullable=False),
        sa.Column('normal_range', sa.String(length=255), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_lab_tests_code'), 'lab_tests', ['code'], unique=True)
    op.create_index(op.f('ix_lab_tests_id'), 'lab_tests', ['id'], unique=False)
    op.create_index(op.f('ix_lab_tests_name'), 'lab_tests', ['name'], unique=False)
    op.create_index(op.f('ix_lab_tests_category'), 'lab_tests', ['category'], unique=False)

    # 2. Lab Orders
    op.create_table(
        'lab_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('admission_id', sa.Integer(), nullable=True),
        sa.Column('emergency_case_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Enum('NORMAL', 'URGENT', 'STAT', name='laborderpriority'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SAMPLE_COLLECTED', 'IN_PROGRESS', 'COMPLETED', 'VERIFIED', 'CANCELLED', name='laborderstatus'), nullable=False),
        sa.Column('clinical_notes', sa.Text(), nullable=True),
        sa.Column('sample_type', sa.String(length=100), nullable=True),
        sa.Column('order_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sample_collected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collected_by_id', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performed_by_id', sa.Integer(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by_id', sa.Integer(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['admission_id'], ['admissions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['collected_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['emergency_case_id'], ['emergency_cases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['test_id'], ['lab_tests.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['verified_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_lab_orders_id'), 'lab_orders', ['id'], unique=False)
    op.create_index(op.f('ix_lab_orders_order_number'), 'lab_orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_lab_orders_patient_id'), 'lab_orders', ['patient_id'], unique=False)
    op.create_index(op.f('ix_lab_orders_doctor_id'), 'lab_orders', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_lab_orders_priority'), 'lab_orders', ['priority'], unique=False)
    op.create_index(op.f('ix_lab_orders_status'), 'lab_orders', ['status'], unique=False)

    # 3. Lab Results
    op.create_table(
        'lab_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('technician_id', sa.Integer(), nullable=False),
        sa.Column('result_summary', sa.Text(), nullable=True),
        sa.Column('technician_notes', sa.Text(), nullable=True),
        sa.Column('is_abnormal', sa.Boolean(), nullable=False),
        sa.Column('is_critical', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['lab_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['technician_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_lab_results_id'), 'lab_results', ['id'], unique=False)
    op.create_index(op.f('ix_lab_results_order_id'), 'lab_results', ['order_id'], unique=True)

    # 4. Lab Result Parameters
    op.create_table(
        'lab_result_parameters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lab_result_id', sa.Integer(), nullable=False),
        sa.Column('parameter_name', sa.String(length=150), nullable=False),
        sa.Column('result_value', sa.String(length=100), nullable=False),
        sa.Column('numeric_value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('reference_range', sa.String(length=100), nullable=True),
        sa.Column('flag', sa.Enum('NORMAL', 'LOW', 'HIGH', 'CRITICAL', name='labresultflag'), nullable=False),
        sa.Column('is_critical', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lab_result_id'], ['lab_results.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_lab_result_parameters_id'), 'lab_result_parameters', ['id'], unique=False)
    op.create_index(op.f('ix_lab_result_parameters_lab_result_id'), 'lab_result_parameters', ['lab_result_id'], unique=False)

    # 5. Lab Reports
    op.create_table(
        'lab_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_number', sa.String(length=50), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('lab_result_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('technician_id', sa.Integer(), nullable=False),
        sa.Column('verified_by_id', sa.Integer(), nullable=True),
        sa.Column('report_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'RELEASED', 'ARCHIVED', name='labreportstatus'), nullable=False),
        sa.Column('clinical_impression', sa.Text(), nullable=True),
        sa.Column('conclusion', sa.Text(), nullable=True),
        sa.Column('print_html', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['lab_result_id'], ['lab_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['lab_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['technician_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['verified_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_lab_reports_id'), 'lab_reports', ['id'], unique=False)
    op.create_index(op.f('ix_lab_reports_order_id'), 'lab_reports', ['order_id'], unique=True)
    op.create_index(op.f('ix_lab_reports_report_number'), 'lab_reports', ['report_number'], unique=True)

    # 6. Medicines
    op.create_table(
        'medicines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('generic_name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('manufacturer', sa.String(length=200), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('reorder_level', sa.Integer(), nullable=False),
        sa.Column('max_stock_level', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_medicines_code'), 'medicines', ['code'], unique=True)
    op.create_index(op.f('ix_medicines_id'), 'medicines', ['id'], unique=False)
    op.create_index(op.f('ix_medicines_name'), 'medicines', ['name'], unique=False)
    op.create_index(op.f('ix_medicines_category'), 'medicines', ['category'], unique=False)

    # 7. Medicine Batches
    op.create_table(
        'medicine_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('medicine_id', sa.Integer(), nullable=False),
        sa.Column('batch_number', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('initial_quantity', sa.Integer(), nullable=False),
        sa.Column('purchase_price', sa.Float(), nullable=False),
        sa.Column('selling_price', sa.Float(), nullable=False),
        sa.Column('manufacturing_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=False),
        sa.Column('supplier', sa.String(length=200), nullable=True),
        sa.Column('storage_location', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['medicine_id'], ['medicines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_medicine_batches_id'), 'medicine_batches', ['id'], unique=False)
    op.create_index(op.f('ix_medicine_batches_medicine_id'), 'medicine_batches', ['medicine_id'], unique=False)
    op.create_index(op.f('ix_medicine_batches_expiry_date'), 'medicine_batches', ['expiry_date'], unique=False)

    # 8. Pharmacy Transactions
    op.create_table(
        'pharmacy_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_number', sa.String(length=50), nullable=False),
        sa.Column('medicine_id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=True),
        sa.Column('transaction_type', sa.Enum('PURCHASE', 'DISPENSE', 'ADJUSTMENT', 'RETURN', 'EXPIRED', 'DAMAGED', name='pharmacytransactiontype'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('performed_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['medicine_batches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['medicine_id'], ['medicines.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['performed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pharmacy_transactions_id'), 'pharmacy_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_pharmacy_transactions_transaction_number'), 'pharmacy_transactions', ['transaction_number'], unique=True)
    op.create_index(op.f('ix_pharmacy_transactions_medicine_id'), 'pharmacy_transactions', ['medicine_id'], unique=False)

    # 9. Prescriptions
    op.create_table(
        'prescriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prescription_number', sa.String(length=50), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('admission_id', sa.Integer(), nullable=True),
        sa.Column('emergency_case_id', sa.Integer(), nullable=True),
        sa.Column('diagnosis', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PARTIALLY_DISPENSED', 'DISPENSED', 'CANCELLED', name='prescriptionstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['admission_id'], ['admissions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['emergency_case_id'], ['emergency_cases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_prescriptions_id'), 'prescriptions', ['id'], unique=False)
    op.create_index(op.f('ix_prescriptions_prescription_number'), 'prescriptions', ['prescription_number'], unique=True)
    op.create_index(op.f('ix_prescriptions_patient_id'), 'prescriptions', ['patient_id'], unique=False)
    op.create_index(op.f('ix_prescriptions_status'), 'prescriptions', ['status'], unique=False)

    # 10. Prescription Items
    op.create_table(
        'prescription_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prescription_id', sa.Integer(), nullable=False),
        sa.Column('medicine_id', sa.Integer(), nullable=False),
        sa.Column('dosage', sa.String(length=100), nullable=False),
        sa.Column('frequency', sa.String(length=100), nullable=False),
        sa.Column('duration', sa.String(length=100), nullable=False),
        sa.Column('quantity_prescribed', sa.Integer(), nullable=False),
        sa.Column('quantity_dispensed', sa.Integer(), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PARTIALLY_DISPENSED', 'DISPENSED', 'OUT_OF_STOCK', name='prescriptionitemstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['medicine_id'], ['medicines.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['prescription_id'], ['prescriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_prescription_items_id'), 'prescription_items', ['id'], unique=False)
    op.create_index(op.f('ix_prescription_items_prescription_id'), 'prescription_items', ['prescription_id'], unique=False)

    # 11. Dispensings
    op.create_table(
        'dispensings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dispensing_number', sa.String(length=50), nullable=False),
        sa.Column('prescription_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('pharmacist_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pharmacist_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['prescription_id'], ['prescriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dispensings_id'), 'dispensings', ['id'], unique=False)
    op.create_index(op.f('ix_dispensings_dispensing_number'), 'dispensings', ['dispensing_number'], unique=True)

    # 12. Dispensing Items
    op.create_table(
        'dispensing_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dispensing_id', sa.Integer(), nullable=False),
        sa.Column('prescription_item_id', sa.Integer(), nullable=False),
        sa.Column('medicine_id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('quantity_dispensed', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['medicine_batches.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['dispensing_id'], ['dispensings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['medicine_id'], ['medicines.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['prescription_item_id'], ['prescription_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dispensing_items_id'), 'dispensing_items', ['id'], unique=False)

    # 13. Billing Items
    op.create_table(
        'billing_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.Enum('CONSULTATION', 'ROOM', 'LAB', 'MEDICINE', 'PROCEDURE', 'OTHER', name='billingcategory'), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('tax_percent', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_billing_items_code'), 'billing_items', ['code'], unique=True)
    op.create_index(op.f('ix_billing_items_id'), 'billing_items', ['id'], unique=False)
    op.create_index(op.f('ix_billing_items_name'), 'billing_items', ['name'], unique=False)

    # 14. Invoices
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('admission_id', sa.Integer(), nullable=True),
        sa.Column('emergency_case_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('paid_amount', sa.Float(), nullable=False),
        sa.Column('balance_amount', sa.Float(), nullable=False),
        sa.Column('payment_status', sa.Enum('UNPAID', 'PARTIALLY_PAID', 'PAID', 'CANCELLED', name='invoicepaymentstatus'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['admission_id'], ['admissions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['emergency_case_id'], ['emergency_cases.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_invoices_id'), 'invoices', ['id'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_number'), 'invoices', ['invoice_number'], unique=True)
    op.create_index(op.f('ix_invoices_patient_id'), 'invoices', ['patient_id'], unique=False)
    op.create_index(op.f('ix_invoices_payment_status'), 'invoices', ['payment_status'], unique=False)

    # 15. Invoice Items
    op.create_table(
        'invoice_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('billing_item_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('category', sa.Enum('CONSULTATION', 'ROOM', 'LAB', 'MEDICINE', 'PROCEDURE', 'OTHER', name='billingcategory'), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('discount', sa.Float(), nullable=False),
        sa.Column('tax_percent', sa.Float(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['billing_item_id'], ['billing_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_invoice_items_id'), 'invoice_items', ['id'], unique=False)
    op.create_index(op.f('ix_invoice_items_invoice_id'), 'invoice_items', ['invoice_id'], unique=False)

    # 16. Payments
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_number', sa.String(length=50), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_method', sa.Enum('CASH', 'CARD', 'UPI', 'OTHER', name='paymentmethod'), nullable=False),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('payment_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('recorded_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recorded_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_invoice_id'), 'payments', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_payments_payment_number'), 'payments', ['payment_number'], unique=True)

    # 17. Notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('role_target', sa.String(length=50), nullable=True),
        sa.Column('type', sa.Enum('INFO', 'SUCCESS', 'WARNING', 'CRITICAL', 'ALERT', name='notificationtype'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'NORMAL', 'HIGH', 'URGENT', name='notificationpriority'), nullable=False),
        sa.Column('related_entity', sa.String(length=50), nullable=True),
        sa.Column('related_entity_id', sa.String(length=100), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_role_target'), 'notifications', ['role_target'], unique=False)


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('payments')
    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('billing_items')
    op.drop_table('dispensing_items')
    op.drop_table('dispensings')
    op.drop_table('prescription_items')
    op.drop_table('prescriptions')
    op.drop_table('pharmacy_transactions')
    op.drop_table('medicine_batches')
    op.drop_table('medicines')
    op.drop_table('lab_reports')
    op.drop_table('lab_result_parameters')
    op.drop_table('lab_results')
    op.drop_table('lab_orders')
    op.drop_table('lab_tests')
