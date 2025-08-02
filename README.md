# Email Summarizer & Auto-Responder

A comprehensive web application that automatically fetches emails, classifies their intent using AI, generates intelligent replies, and provides an admin dashboard for managing email responses.

## 🚀 Features

- **Email Fetching**: Connect to IMAP servers to fetch unread emails
- **AI Processing**: Use OpenAI GPT-4 to classify email intent and generate replies
- **Smart Classification**: Automatically categorize emails (Meeting Request, Job Inquiry, Complaint, etc.)
- **Tone Selection**: Generate replies with different tones (Formal, Friendly, Apologetic, Assertive)
- **Admin Dashboard**: Modern web interface for managing emails and responses
- **Auto-Scheduler**: Background processing every 5 minutes
- **Email Sending**: Send approved replies via SMTP
- **Database Storage**: SQLite database with SQLAlchemy ORM

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Email account with IMAP/SMTP access
- Internet connection

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd email_summarizer
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the project root:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Email Server Configuration (IMAP)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here

# Database Configuration
DATABASE_URL=sqlite:///./email_summarizer.db

# Application Configuration
SECRET_KEY=your_secret_key_here
SCHEDULER_INTERVAL_MINUTES=5
```

### 4. Email Setup (Gmail Example)

#### For Gmail:
1. Enable 2-Factor Authentication
2. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the generated password in your `.env` file

#### For Other Providers:
- **Outlook**: Use `outlook.office365.com` for IMAP/SMTP
- **Yahoo**: Use `imap.mail.yahoo.com` and `smtp.mail.yahoo.com`
- **Custom**: Check your email provider's IMAP/SMTP settings

## 🚀 Running the Application

### 1. Initialize Database
```bash
python database.py
```

### 2. Start the Application
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the Dashboard
Open your browser and navigate to:
```
http://localhost:8000
```

## 📊 Dashboard Features

### Email Management
- **View All Emails**: See all processed emails with status, intent, and draft replies
- **Edit Replies**: Modify AI-generated draft replies
- **Change Tone**: Regenerate replies with different tones
- **Update Status**: Mark emails as pending, approved, rejected, or sent
- **Send Emails**: Approve and send replies via SMTP

### Email Classification
The AI automatically classifies emails into:
- **Meeting Request**: Scheduling requests and calls
- **Job Inquiry**: Job applications and opportunities
- **Complaint**: Issues and problems
- **Feedback**: Suggestions and comments
- **Support Request**: Help and technical support
- **Follow-up**: Follow-up messages
- **Other**: General inquiries

### Reply Tones
Generate replies with different tones:
- **Formal**: Professional business language
- **Friendly**: Warm and approachable
- **Apologetic**: Sincere and apologetic
- **Assertive**: Confident and direct

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `IMAP_SERVER` | IMAP server address | `imap.gmail.com` |
| `IMAP_PORT` | IMAP server port | `993` |
| `EMAIL_USERNAME` | Your email address | Required |
| `EMAIL_PASSWORD` | Your email password/app password | Required |
| `SMTP_SERVER` | SMTP server address | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USERNAME` | SMTP username (usually same as email) | Required |
| `SMTP_PASSWORD` | SMTP password/app password | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///./email_summarizer.db` |
| `SECRET_KEY` | Application secret key | Required |
| `SCHEDULER_INTERVAL_MINUTES` | Email check interval | `5` |

### Customizing Email Processing

#### Modify Intent Classification
Edit `ai_service.py` to add new email categories:

```python
class EmailIntent(enum.Enum):
    MEETING_REQUEST = "Meeting Request"
    JOB_INQUIRY = "Job Inquiry"
    # Add your custom categories here
    CUSTOM_CATEGORY = "Custom Category"
```

#### Add New Reply Tones
Edit `ai_service.py` to add new tones:

```python
class ReplyTone(enum.Enum):
    FORMAL = "Formal"
    FRIENDLY = "Friendly"
    # Add your custom tones here
    CUSTOM_TONE = "Custom Tone"
```

## 🔍 API Endpoints

### Web Interface
- `GET /` - Admin dashboard
- `POST /process-emails` - Manually trigger email processing
- `POST /update-email/{email_id}` - Update email draft and status
- `POST /send-email/{email_id}` - Send email reply
- `POST /regenerate-reply/{email_id}` - Regenerate reply with new tone

### Health & Status
- `GET /health` - System health check
- `GET /email/{email_id}` - Get email details (JSON)

## 🐛 Troubleshooting

### Common Issues

#### 1. Email Connection Failed
**Symptoms**: "Error connecting to IMAP server"
**Solutions**:
- Verify email credentials in `.env`
- Check if 2FA is enabled and app password is used
- Ensure IMAP is enabled in email settings
- Try different IMAP/SMTP servers

#### 2. OpenAI API Error
**Symptoms**: "Error classifying email intent"
**Solutions**:
- Verify OpenAI API key is correct
- Check API key has sufficient credits
- Ensure internet connection is stable

#### 3. Database Errors
**Symptoms**: "Database connection failed"
**Solutions**:
- Ensure SQLite is installed
- Check file permissions for database directory
- Delete `email_summarizer.db` and restart

#### 4. Scheduler Not Working
**Symptoms**: Emails not being processed automatically
**Solutions**:
- Check scheduler interval in `.env`
- Verify all services are initialized
- Check application logs for errors

### Debug Mode
Enable debug logging by modifying `main.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Health Check
Visit `/health` endpoint to check system status:
```bash
curl http://localhost:8000/health
```

## 📁 Project Structure

```
email_summarizer/
├── main.py              # FastAPI application and routes
├── database.py          # SQLAlchemy models and DB setup
├── email_client.py      # IMAP/SMTP email handling
├── ai_service.py        # OpenAI integration
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .env                # Environment variables (create this)
├── templates/
│   └── dashboard.html  # Admin dashboard template
└── static/
    └── style.css       # Custom CSS styles
```

## 🔒 Security Considerations

### Email Security
- Use app passwords instead of regular passwords
- Enable 2-Factor Authentication
- Use secure IMAP/SMTP connections (SSL/TLS)

### API Security
- Keep OpenAI API key secure
- Use environment variables for sensitive data
- Regularly rotate API keys

### Application Security
- Use strong SECRET_KEY
- Keep dependencies updated
- Monitor application logs

## 🚀 Deployment

### Local Development
```bash
python main.py
```

### Production Deployment
1. Use a production WSGI server (Gunicorn)
2. Set up reverse proxy (Nginx)
3. Use environment variables for configuration
4. Set up SSL/TLS certificates
5. Configure firewall rules

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Test individual components
4. Create an issue with detailed information

## 🔄 Updates

### Version 1.0.0
- Initial release
- Email fetching and processing
- AI-powered classification and reply generation
- Admin dashboard
- Background scheduler
- SMTP email sending

---

**Note**: This application processes real emails. Always review AI-generated replies before sending them to ensure they meet your standards and requirements. 