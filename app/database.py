import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from urllib.parse import quote_plus
from app.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

odbc_connect_str = quote_plus(settings.connection_string)
SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={odbc_connect_str}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        logger.info(f"Conexión exitosa a la base de datos '{settings.db_database}' en el servidor '{settings.db_server}'")
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        raise
    finally:
        db.close()
