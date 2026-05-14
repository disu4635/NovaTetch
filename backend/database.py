from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

DATABASE_URL = "sqlite:///./novatech.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class RunRecord(Base):
    __tablename__ = "runs"

    run_id = Column(String, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class QualityRun(Base):
    __tablename__ = "quality_runs"

    quality_run_id  = Column(String, primary_key=True, index=True)
    run_id          = Column(String, nullable=False, index=True)
    status          = Column(String, nullable=False, default="running")
    progress_msg    = Column(Text, nullable=True)
    contract_b_json = Column(Text, nullable=True)
    risk_matrix_json= Column(Text, nullable=True)
    pdf_path        = Column(Text, nullable=True)
    error           = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
