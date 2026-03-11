import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def setup_mongodb(url: str='mongodb://synthhire:localdev123@localhost:27017/synthhire?authSource=admin'):
    client = AsyncIOMotorClient(url)
    db = client.synthhire
    print('🗄️  Setting up MongoDB collections and indexes...')
    try:
        await db.create_collection('transcripts', validator={'$jsonSchema': {'bsonType': 'object', 'required': ['session_id', 'user_id'], 'properties': {'session_id': {'bsonType': 'string'}, 'user_id': {'bsonType': 'string'}, 'exchanges': {'bsonType': 'array'}, 'full_transcript_text': {'bsonType': 'string'}}}})
    except:
        pass
    await db.transcripts.create_index([('session_id', 1)], unique=True)
    await db.transcripts.create_index([('user_id', 1), ('created_at', -1)])
    await db.exchanges.create_index([('session_id', 1), ('exchange_number', 1)])
    await db.exchanges.create_index([('created_at', -1)])
    await db.whiteboard_snapshots.create_index([('session_id', 1), ('snapshot_number', 1)])
    await db.emotional_frames.create_index([('session_id', 1), ('timestamp', 1)])
    await db.emotional_frames.create_index([('created_at', 1)], expireAfterSeconds=30 * 24 * 60 * 60)
    await db.emotional_summaries.create_index([('session_id', 1)], unique=True)
    await db.company_patterns.create_index([('company_slug', 1)], unique=True)
    await db.reports.create_index([('session_id', 1)], unique=True)
    await db.reports.create_index([('user_id', 1), ('created_at', -1)])
    await db.ml_training_exports.create_index([('export_date', -1)])
    await db.prosody_analysis.create_index([('session_id', 1)])
    await db.prosody_analysis.create_index([('created_at', 1)], expireAfterSeconds=90 * 24 * 60 * 60)
    print('✅ MongoDB setup complete')
    client.close()
if __name__ == '__main__':
    asyncio.run(setup_mongodb())