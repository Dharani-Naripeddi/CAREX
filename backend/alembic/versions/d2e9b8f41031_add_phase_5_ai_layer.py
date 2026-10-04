"""add_phase_5_ai_layer

Revision ID: d2e9b8f41031
Revises: c1f8a42b9102
Create Date: 2026-09-02 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2e9b8f41031'
down_revision = 'c1f8a42b9102'
branch_labels = None
depends_on = None


def upgrade():
    # 1. ai_predictions
    op.create_table(
        'ai_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediction_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=50), nullable=True),
        sa.Column('prediction_value', sa.JSON(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('model_provider_type', sa.String(length=50), nullable=False),
        sa.Column('explanation', sa.JSON(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=False),
        sa.Column('input_features', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_predictions_id'), 'ai_predictions', ['id'], unique=False)
    op.create_index(op.f('ix_ai_predictions_prediction_type'), 'ai_predictions', ['prediction_type'], unique=False)
    op.create_index(op.f('ix_ai_predictions_entity_type'), 'ai_predictions', ['entity_type'], unique=False)
    op.create_index(op.f('ix_ai_predictions_entity_id'), 'ai_predictions', ['entity_id'], unique=False)
    op.create_index(op.f('ix_ai_predictions_generated_at'), 'ai_predictions', ['generated_at'], unique=False)

    # 2. ai_alerts
    op.create_table(
        'ai_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reason', sa.JSON(), nullable=False),
        sa.Column('recommended_action', sa.Text(), nullable=False),
        sa.Column('related_entity', sa.String(length=50), nullable=False),
        sa.Column('related_entity_id', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['acknowledged_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_alerts_id'), 'ai_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_ai_alerts_alert_type'), 'ai_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_ai_alerts_severity'), 'ai_alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_ai_alerts_status'), 'ai_alerts', ['status'], unique=False)
    op.create_index(op.f('ix_ai_alerts_created_at'), 'ai_alerts', ['created_at'], unique=False)

    # 3. ai_feedbacks
    op.create_table(
        'ai_feedbacks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediction_id', sa.Integer(), nullable=True),
        sa.Column('alert_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prediction_id'], ['ai_predictions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['alert_id'], ['ai_alerts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_feedbacks_id'), 'ai_feedbacks', ['id'], unique=False)

    # 4. ai_document_records
    op.create_table(
        'ai_document_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=100), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=False),
        sa.Column('ai_summary', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('verified_by_id', sa.Integer(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['verified_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_document_records_id'), 'ai_document_records', ['id'], unique=False)

    # 5. ai_shift_handovers
    op.create_table(
        'ai_shift_handovers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ward_id', sa.Integer(), nullable=True),
        sa.Column('shift_name', sa.String(length=50), nullable=False),
        sa.Column('from_nurse_id', sa.Integer(), nullable=False),
        sa.Column('to_nurse_id', sa.Integer(), nullable=True),
        sa.Column('patient_summaries', sa.JSON(), nullable=False),
        sa.Column('important_observations', sa.Text(), nullable=True),
        sa.Column('next_shift_checklist', sa.JSON(), nullable=False),
        sa.Column('ai_notes', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='DRAFT'),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['ward_id'], ['wards.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['from_nurse_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['to_nurse_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_shift_handovers_id'), 'ai_shift_handovers', ['id'], unique=False)


def downgrade():
    op.drop_table('ai_shift_handovers')
    op.drop_table('ai_document_records')
    op.drop_table('ai_feedbacks')
    op.drop_table('ai_alerts')
    op.drop_table('ai_predictions')
