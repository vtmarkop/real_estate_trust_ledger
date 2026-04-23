# app/core/db.py
from sqlmodel import create_engine
from app.core.config import settings

# Φτιάχνουμε τον κινητήρα της βάσης και τον κάνουμε διαθέσιμο σε όλο το app
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)