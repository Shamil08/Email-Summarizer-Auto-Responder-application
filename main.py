from fastapi import FastAPI, Request, Depends, HTTPException, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
import logging
from typing import List, Optional
import os
from dotenv import load_dotenv

# Import our modules
from database import get_db, Email, EmailStatus, EmailIntent, ReplyTone, init_db
from email_client import EmailClient, extract_email_address
from ai_service import AIService, extract_sender_name
from models import (
    EmailUpdateRequest, ReplyRegenerationRequest, EmailProcessingRequest,
    EmailResponse, SchedulerStatusResponse, HealthCheckResponse, 
    ErrorResponse, SuccessResponse, validate_email_id
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Email Summarizer & Auto-Responder", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize services
email_client = None
ai_service = None
scheduler = None

# Initialize database
init_db()

def initialize_services():
    """Initialize email client and AI service"""
    global email_client, ai_service
    try:
        email_client = EmailClient()
        ai_service = AIService()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")

def process_new_emails():
    """Process new emails - fetch, classify, and generate replies"""
    try:
        if not email_client or not ai_service:
            logger.error("Services not initialized")
            return
        
        # Fetch unread emails
        emails = email_client.fetch_unread_emails()
        
        if not emails:
            logger.info("No new emails found")
            return
        
        # Process each email
        for email_data in emails:
            try:
                # Extract email information
                sender = email_data['sender']
                subject = email_data['subject']
                body = email_data['body']
                
                # Classify intent
                intent = ai_service.classify_email_intent(subject, body)
                
                # Generate summary
                summary = ai_service.generate_email_summary(subject, body)
                
                # Generate draft reply with default tone (Formal)
                draft_reply = ai_service.generate_draft_reply(
                    subject, body, intent, ReplyTone.FORMAL, 
                    extract_sender_name(sender)
                )
                
                # Save to database
                db = next(get_db())
                email_record = Email(
                    sender=extract_email_address(sender),
                    subject=subject,
                    body=body,
                    summary=summary,
                    draft_reply=draft_reply,
                    intent=intent,
                    tone=ReplyTone.FORMAL,
                    status=EmailStatus.PENDING
                )
                db.add(email_record)
                db.commit()
                db.close()
                
                logger.info(f"Processed email: {subject}")
                
            except Exception as e:
                logger.error(f"Error processing email: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in process_new_emails: {e}")

def start_scheduler():
    """Start the background scheduler with time-based scheduling"""
    global scheduler
    try:
        scheduler = AsyncIOScheduler()
        
        # Get scheduler configuration from environment
        scheduler_enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
        scheduler_type = os.getenv("SCHEDULER_TYPE", "time").lower()  # "time" or "interval"
        
        if not scheduler_enabled:
            logger.info("Scheduler is disabled")
            return
        
        if scheduler_type == "interval":
            # Interval-based scheduling (original functionality)
            interval_minutes = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", 5))
            scheduler.add_job(
                process_new_emails,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="email_processor",
                name="Process new emails (Interval)",
                replace_existing=True
            )
            logger.info(f"Interval scheduler started with {interval_minutes} minute interval")
            
        elif scheduler_type == "time":
            # Time-based scheduling
            from apscheduler.triggers.cron import CronTrigger
            
            # Get time configurations from environment
            morning_time = os.getenv("SCHEDULER_MORNING_TIME", "09:00")
            evening_time = os.getenv("SCHEDULER_EVENING_TIME", "16:00")
            
            # Parse times
            morning_hour, morning_minute = map(int, morning_time.split(":"))
            evening_hour, evening_minute = map(int, evening_time.split(":"))
            
            # Add morning job
            scheduler.add_job(
                process_new_emails,
                trigger=CronTrigger(hour=morning_hour, minute=morning_minute),
                id="email_processor_morning",
                name=f"Process new emails (Morning - {morning_time})",
                replace_existing=True
            )
            
            # Add evening job
            scheduler.add_job(
                process_new_emails,
                trigger=CronTrigger(hour=evening_hour, minute=evening_minute),
                id="email_processor_evening",
                name=f"Process new emails (Evening - {evening_time})",
                replace_existing=True
            )
            
            logger.info(f"Time-based scheduler started - Morning: {morning_time}, Evening: {evening_time}")
        
        scheduler.start()
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

def get_scheduler_status():
    """Get current scheduler status and configuration"""
    global scheduler
    
    if not scheduler:
        return {
            "enabled": False,
            "running": False,
            "type": None,
            "jobs": []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "enabled": True,
        "running": scheduler.running,
        "type": os.getenv("SCHEDULER_TYPE", "time"),
        "morning_time": os.getenv("SCHEDULER_MORNING_TIME", "09:00"),
        "evening_time": os.getenv("SCHEDULER_EVENING_TIME", "16:00"),
        "interval_minutes": os.getenv("SCHEDULER_INTERVAL_MINUTES", "5"),
        "jobs": jobs
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services and start scheduler on startup"""
    initialize_services()
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler on app shutdown"""
    if scheduler:
        scheduler.shutdown()

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard - main page"""
    try:
        # Get all emails ordered by timestamp (newest first)
        emails = db.query(Email).order_by(Email.timestamp.desc()).all()
        
        # Get available tones and intents for the UI
        if ai_service:
            tones = ai_service.get_available_tones()
            intents = ai_service.get_available_intents()
        else:
            tones = []
            intents = []
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "emails": emails,
            "tones": tones,
            "intents": intents,
            "status_options": [status.value for status in EmailStatus]
        })
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/process-emails", response_model=SuccessResponse)
async def process_emails(
    request: EmailProcessingRequest,
    background_tasks: BackgroundTasks
):
    """Manually trigger email processing with validation"""
    try:
        # Validate request parameters
        if request.max_emails > 50:
            raise HTTPException(status_code=400, detail="Maximum emails cannot exceed 50")
        
        background_tasks.add_task(process_new_emails)
        return SuccessResponse(message="Email processing started")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering email processing: {e}")
        raise HTTPException(status_code=500, detail="Error processing emails")

@app.post("/update-email/{email_id}", response_model=SuccessResponse)
async def update_email(
    email_id: int,
    request: EmailUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update email draft reply, tone, and status with validation"""
    try:
        # Validate email ID
        if not validate_email_id(email_id):
            raise HTTPException(status_code=400, detail="Invalid email ID")
        
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Update email with validated data
        email.draft_reply = request.draft_reply
        email.tone = ReplyTone(request.tone.value)
        email.status = EmailStatus(request.status.value)
        
        db.commit()
        
        return SuccessResponse(message="Email updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email: {e}")
        raise HTTPException(status_code=500, detail="Error updating email")

@app.post("/send-email/{email_id}", response_model=SuccessResponse)
async def send_email(email_id: int, db: Session = Depends(get_db)):
    """Send email reply with validation"""
    try:
        # Validate email ID
        if not validate_email_id(email_id):
            raise HTTPException(status_code=400, detail="Invalid email ID")
        
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        if not email_client:
            raise HTTPException(status_code=500, detail="Email client not initialized")
        
        # Validate email content before sending
        if not email.draft_reply or len(email.draft_reply.strip()) < 10:
            raise HTTPException(status_code=400, detail="Email reply is too short or empty")
        
        # Send email
        success = email_client.send_email_reply(
            email.sender,
            f"Re: {email.subject}",
            email.draft_reply,
            email.subject
        )
        
        if success:
            # Update status to sent
            email.status = EmailStatus.SENT
            db.commit()
            return SuccessResponse(message="Email sent successfully")
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Error sending email")

@app.post("/regenerate-reply/{email_id}", response_model=SuccessResponse)
async def regenerate_reply(
    email_id: int,
    request: ReplyRegenerationRequest,
    db: Session = Depends(get_db)
):
    """Regenerate reply with different tone and validation"""
    try:
        # Validate email ID
        if not validate_email_id(email_id):
            raise HTTPException(status_code=400, detail="Invalid email ID")
        
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        if not ai_service:
            raise HTTPException(status_code=500, detail="AI service not initialized")
        
        # Generate new reply with validated tone
        new_reply = ai_service.generate_draft_reply(
            email.subject,
            email.body,
            email.intent,
            ReplyTone(request.tone.value),
            extract_sender_name(email.sender)
        )
        
        # Validate generated reply
        if not new_reply or len(new_reply.strip()) < 10:
            raise HTTPException(status_code=500, detail="Generated reply is too short or empty")
        
        # Update email
        email.draft_reply = new_reply
        email.tone = ReplyTone(request.tone.value)
        db.commit()
        
        return SuccessResponse(message=f"Reply regenerated successfully with {request.tone.value} tone")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating reply: {e}")
        raise HTTPException(status_code=500, detail="Error regenerating reply")

@app.get("/email/{email_id}", response_model=EmailResponse)
async def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get email details for AJAX requests with validation"""
    try:
        # Validate email ID
        if not validate_email_id(email_id):
            raise HTTPException(status_code=400, detail="Invalid email ID")
        
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        return EmailResponse(
            id=email.id,
            sender=email.sender,
            subject=email.subject,
            body=email.body,
            summary=email.summary,
            draft_reply=email.draft_reply,
            intent=email.intent.value if email.intent else None,
            tone=email.tone.value if email.tone else None,
            status=email.status.value,
            timestamp=email.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email: {e}")
        raise HTTPException(status_code=500, detail="Error getting email")

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint with validation"""
    try:
        # Test services
        email_ok = email_client is not None
        ai_ok = ai_service is not None
        scheduler_ok = scheduler is not None and scheduler.running
        
        status = "healthy" if all([email_ok, ai_ok, scheduler_ok]) else "unhealthy"
        
        return HealthCheckResponse(
            status=status,
            email_client=email_ok,
            ai_service=ai_ok,
            scheduler=scheduler_ok
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            email_client=False,
            ai_service=False,
            scheduler=False
        )

@app.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status_endpoint():
    """Get scheduler status and configuration with validation"""
    try:
        status = get_scheduler_status()
        return SchedulerStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail="Error getting scheduler status")

@app.post("/scheduler/start")
async def start_scheduler_endpoint():
    """Start the scheduler"""
    try:
        if scheduler and scheduler.running:
            return {"message": "Scheduler is already running"}
        
        start_scheduler()
        return {"message": "Scheduler started successfully"}
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail="Error starting scheduler")

@app.post("/scheduler/stop")
async def stop_scheduler_endpoint():
    """Stop the scheduler"""
    try:
        if not scheduler or not scheduler.running:
            return {"message": "Scheduler is not running"}
        
        stop_scheduler()
        return {"message": "Scheduler stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail="Error stopping scheduler")

@app.post("/scheduler/restart", response_model=SuccessResponse)
async def restart_scheduler_endpoint():
    """Restart the scheduler with validation"""
    try:
        if scheduler and scheduler.running:
            stop_scheduler()
        
        start_scheduler()
        return SuccessResponse(message="Scheduler restarted successfully")
    except Exception as e:
        logger.error(f"Error restarting scheduler: {e}")
        raise HTTPException(status_code=500, detail="Error restarting scheduler")

# Global exception handler for validation errors
@app.exception_handler(ValueError)
async def validation_exception_handler(request: Request, exc: ValueError):
    """Handle validation errors from Pydantic"""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc)
        ).dict()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred"
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 