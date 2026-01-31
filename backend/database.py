from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import logging

from core.config import settings

Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String(100), unique=True, index=True)
    name = Column(String(100))
    role = Column(String(200))
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    tasks = relationship("Task", back_populates="agent")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), unique=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    agent_id = Column(Integer, ForeignKey("agents.id"))
    agent = relationship("Agent", back_populates="tasks")

    code_content = Column(Text, nullable=True)
    target_files = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True)


class Tool(Base):
    __tablename__ = "tools"
    
    id = Column(Integer, primary_key=True)
    tool_id = Column(String(100), unique=True, index=True)
    name = Column(String(100))
    description = Column(Text)
    category = Column(String(50))
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(100), unique=True, index=True)
    sender_id = Column(String(100))
    receiver_id = Column(String(100))
    content = Column(Text)
    message_type = Column(String(50))  # task, response, notification, error
    created_at = Column(DateTime, default=datetime.now)
    is_read = Column(Boolean, default=False)


class AuditResult(Base):
    __tablename__ = "audit_results"
    
    id = Column(Integer, primary_key=True)
    result_id = Column(String(100), unique=True, index=True)
    task_id = Column(String(100))
    severity = Column(String(20))  # critical, high, medium, low, info
    category = Column(String(50))  # security, performance, style, bug
    description = Column(Text)
    file_path = Column(String(200), nullable=True)
    line_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class ToolExecution(Base):
    __tablename__ = "tool_executions"
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(String(100), unique=True, index=True)
    tool_id = Column(String(100))
    task_id = Column(String(100))
    status = Column(String(50))  # success, failed, timeout
    input_params = Column(Text)
    output_result = Column(Text)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
