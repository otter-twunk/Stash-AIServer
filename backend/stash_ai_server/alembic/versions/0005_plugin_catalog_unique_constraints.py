"""De-duplicate plugin_catalog rows and enforce uniqueness on catalog and settings

Revision ID: 0005_plugin_catalog_unique_constraints
Revises: 0004_ai_tagging_perf_indexes
Create Date: 2026-06-21

Fixes two latent data-integrity bugs:
1. plugin_catalog had no unique constraint on (source_id, plugin_name), so
   repeated source refreshes could accumulate duplicate rows. loader.py then
   crashed with MultipleResultsFound on every boot for the affected plugins.
2. plugin_settings had no unique constraint on (plugin_name, key), leaving a
   similar race window open for concurrent setting writes.

Upgrade steps:
  a. Remove duplicate plugin_catalog rows, keeping the one with the lowest id
     per (source_id, plugin_name).
  b. Replace the plain composite index on plugin_settings(plugin_name, key)
     with a unique one.
  c. Add unique constraints on both tables.
"""
from alembic import op
import sqlalchemy as sa


revision = '0005_plugin_catalog_uq'
down_revision = '0004_ai_tagging_perf_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # --- plugin_catalog ---
    # Delete duplicate rows keeping the lowest id per (source_id, plugin_name).
    conn.execute(sa.text("""
        DELETE FROM plugin_catalog
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM plugin_catalog
            GROUP BY source_id, plugin_name
        )
    """))

    op.create_unique_constraint(
        'uq_plugin_catalog_source_name',
        'plugin_catalog',
        ['source_id', 'plugin_name'],
    )

    # --- plugin_settings ---
    # The plain composite index is superseded by the unique constraint below.
    op.drop_index('ix_plugin_settings_plugin_name_key', table_name='plugin_settings')
    op.create_unique_constraint(
        'uq_plugin_settings_name_key',
        'plugin_settings',
        ['plugin_name', 'key'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_plugin_settings_name_key', 'plugin_settings', type_='unique')
    op.create_index('ix_plugin_settings_plugin_name_key', 'plugin_settings', ['plugin_name', 'key'])

    op.drop_constraint('uq_plugin_catalog_source_name', 'plugin_catalog', type_='unique')
    # Note: downgrade cannot restore deleted duplicate rows.
