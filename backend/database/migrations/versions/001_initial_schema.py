from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.execute('ALTER TABLE questions ADD COLUMN IF NOT EXISTS ideal_response_embedding vector(384)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_questions_embedding ON questions USING ivfflat (ideal_response_embedding vector_cosine_ops) WITH (lists = 50)')
    op.execute('ALTER TABLE session_exchanges ADD COLUMN IF NOT EXISTS candidate_response_embedding vector(384)')
    print('✅ pgvector extensions and embedding columns added')

def downgrade():
    op.execute('ALTER TABLE session_exchanges DROP COLUMN IF EXISTS candidate_response_embedding')
    op.execute('DROP INDEX IF EXISTS idx_questions_embedding')
    op.execute('ALTER TABLE questions DROP COLUMN IF EXISTS ideal_response_embedding')
    op.execute('DROP EXTENSION IF EXISTS vector')
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')