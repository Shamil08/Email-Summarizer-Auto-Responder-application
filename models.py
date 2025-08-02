from pydantic import BaseModel, validator, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
import re

# Enums for validation
class EmailStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"

class ReplyToneEnum(str, Enum):
    FORMAL = "Formal"
    FRIENDLY = "Friendly"
    APOLOGETIC = "Apologetic"
    ASSERTIVE = "Assertive"

class EmailIntentEnum(str, Enum):
    MEETING_REQUEST = "Meeting Request"
    JOB_INQUIRY = "Job Inquiry"
    COMPLAINT = "Complaint"
    FEEDBACK = "Feedback"
    SUPPORT_REQUEST = "Support Request"
    FOLLOW_UP = "Follow-up"
    OTHER = "Other"

# Request Models
class EmailUpdateRequest(BaseModel):
    """Model for updating email data"""
    draft_reply: str = Field(..., min_length=1, max_length=5000, description="Email reply content")
    tone: ReplyToneEnum = Field(..., description="Reply tone")
    status: EmailStatusEnum = Field(..., description="Email status")
    
    @validator('draft_reply')
    def validate_draft_reply(cls, v):
        """Validate draft reply content"""
        if not v.strip():
            raise ValueError('Draft reply cannot be empty')
        if len(v.strip()) < 10:
            raise ValueError('Draft reply must be at least 10 characters')
        return v.strip()
    
    @validator('draft_reply')
    def validate_no_script_tags(cls, v):
        """Prevent XSS attacks"""
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'onload=',
            r'onerror=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        content_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, content_lower):
                raise ValueError('Draft reply contains potentially malicious content')
        return v

class ReplyRegenerationRequest(BaseModel):
    """Model for regenerating replies"""
    tone: ReplyToneEnum = Field(..., description="New tone for reply")

class EmailProcessingRequest(BaseModel):
    """Model for manual email processing"""
    force_process: bool = Field(default=False, description="Force processing even if no new emails")
    max_emails: int = Field(default=10, ge=1, le=50, description="Maximum emails to process")
    
    @validator('max_emails')
    def validate_max_emails(cls, v):
        """Ensure reasonable limit"""
        if v < 1:
            raise ValueError('max_emails must be at least 1')
        if v > 50:
            raise ValueError('max_emails cannot exceed 50')
        return v

class SchedulerConfigRequest(BaseModel):
    """Model for scheduler configuration"""
    enabled: bool = Field(default=True, description="Enable/disable scheduler")
    scheduler_type: str = Field(default="time", regex="^(time|interval)$", description="Scheduler type")
    morning_time: str = Field(default="09:00", regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Morning time (HH:MM)")
    evening_time: str = Field(default="16:00", regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Evening time (HH:MM)")
    interval_minutes: int = Field(default=5, ge=1, le=1440, description="Interval in minutes")
    
    @validator('morning_time', 'evening_time')
    def validate_time_format(cls, v):
        """Validate time format HH:MM"""
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format')
        return v

# Response Models
class EmailResponse(BaseModel):
    """Model for email data in responses"""
    id: int
    sender: str
    subject: str
    body: str
    summary: Optional[str]
    draft_reply: Optional[str]
    intent: Optional[str]
    tone: Optional[str]
    status: str
    timestamp: Optional[datetime]
    
    class Config:
        from_attributes = True

class SchedulerStatusResponse(BaseModel):
    """Model for scheduler status response"""
    enabled: bool
    running: bool
    type: Optional[str]
    morning_time: Optional[str]
    evening_time: Optional[str]
    interval_minutes: Optional[str]
    jobs: List[dict]

class HealthCheckResponse(BaseModel):
    """Model for health check response"""
    status: str
    email_client: bool
    ai_service: bool
    scheduler: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SuccessResponse(BaseModel):
    """Model for success responses"""
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Utility Models
class EmailStats(BaseModel):
    """Model for email statistics"""
    total_emails: int
    pending_emails: int
    approved_emails: int
    rejected_emails: int
    sent_emails: int
    today_processed: int
    this_week_processed: int

class AIServiceConfig(BaseModel):
    """Model for AI service configuration"""
    model: str = Field(default="gpt-4", description="OpenAI model to use")
    max_tokens: int = Field(default=300, ge=50, le=1000, description="Maximum tokens for AI responses")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="AI response creativity")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Ensure temperature is within valid range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Temperature must be between 0.0 and 1.0')
        return v

# Validation Functions
def validate_email_address(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_email_content(content: str) -> bool:
    """Validate email content for malicious content"""
    dangerous_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'onload=',
        r'onerror=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>'
    ]
    
    content_lower = content.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, content_lower):
            return False
    return True

def validate_email_id(email_id: int) -> bool:
    """Validate email ID"""
    return email_id > 0 