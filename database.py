from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./email_summarizer.db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Enum for email status
class EmailStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"

# Enum for email intent
class EmailIntent(enum.Enum):
    MEETING_REQUEST = "Meeting Request"
    JOB_INQUIRY = "Job Inquiry"
    COMPLAINT = "Complaint"
    FEEDBACK = "Feedback"
    SUPPORT_REQUEST = "Support Request"
    FOLLOW_UP = "Follow-up"
    OTHER = "Other"

# Enum for reply tone
class ReplyTone(enum.Enum):
    FORMAL = "Formal"
    FRIENDLY = "Friendly"
    APOLOGETIC = "Apologetic"
    ASSERTIVE = "Assertive"

# Email model
class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    draft_reply = Column(Text, nullable=True)
    intent = Column(Enum(EmailIntent), nullable=True)
    tone = Column(Enum(ReplyTone), nullable=True)
    status = Column(Enum(EmailStatus), default=EmailStatus.PENDING)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Email(id={self.id}, sender='{self.sender}', subject='{self.subject}', status='{self.status}')>"

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Initialize database
def init_db():
    create_tables()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db() 