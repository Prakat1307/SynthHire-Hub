from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import time
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
Base = declarative_base()

def get_engine(database_url: str):
    return create_engine(database_url, pool_size=20, max_overflow=10, pool_pre_ping=True, pool_recycle=3600)

def wait_for_db(engine, max_retries=15, delay=2):
    retries = 0
    while retries < max_retries:
        try:
            with engine.connect() as conn:
                logger.info('Successfully connected to the database!')
                return True
        except OperationalError:
            retries += 1
            logger.warning(f'Database connection failed. Retrying in {delay} seconds... ({retries}/{max_retries})')
            time.sleep(delay)
    logger.error('Could not connect to the database after maximum retries.')
    raise Exception('Database connection timeout')

def get_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)