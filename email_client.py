import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailClient:
    def __init__(self):
        # IMAP Configuration
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.imap_port = int(os.getenv("IMAP_PORT", 993))
        self.email_username = os.getenv("EMAIL_USERNAME")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        # SMTP Configuration
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not all([self.email_username, self.email_password, self.smtp_username, self.smtp_password]):
            raise ValueError("Email credentials not properly configured in environment variables")

    def _decode_email_header(self, header: str) -> str:
        """Decode email header properly"""
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_string += part.decode(encoding or 'utf-8')
                else:
                    decoded_string += str(part)
            return decoded_string
        except Exception as e:
            logger.error(f"Error decoding header: {e}")
            return str(header)

    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract email body from message"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body += part.get_payload(decode=True).decode()
                    except Exception as e:
                        logger.error(f"Error decoding part: {e}")
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except Exception as e:
                logger.error(f"Error decoding body: {e}")
        
        return body.strip()

    def fetch_unread_emails(self) -> List[Dict]:
        """Fetch unread emails from IMAP server"""
        emails = []
        
        try:
            # Connect to IMAP server
            imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            imap.login(self.email_username, self.email_password)
            
            # Select inbox
            imap.select('INBOX')
            
            # Search for unread emails
            status, messages = imap.search(None, 'UNSEEN')
            
            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()
                
                for email_id in email_ids:
                    try:
                        # Fetch email
                        status, msg_data = imap.fetch(email_id, '(RFC822)')
                        
                        if status == 'OK':
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)
                            
                            # Extract email information
                            sender = self._decode_email_header(msg.get('From', ''))
                            subject = self._decode_email_header(msg.get('Subject', ''))
                            body = self._get_email_body(msg)
                            
                            email_info = {
                                'id': email_id.decode(),
                                'sender': sender,
                                'subject': subject,
                                'body': body,
                                'timestamp': msg.get('Date', '')
                            }
                            
                            emails.append(email_info)
                            logger.info(f"Fetched email: {subject}")
                    
                    except Exception as e:
                        logger.error(f"Error processing email {email_id}: {e}")
                        continue
            
            imap.close()
            imap.logout()
            
        except Exception as e:
            logger.error(f"Error connecting to IMAP server: {e}")
            raise
        
        return emails

    def send_email_reply(self, to_email: str, subject: str, body: str, original_subject: str = None) -> bool:
        """Send email reply via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            
            # Add "Re:" prefix to subject if not already present
            if original_subject and not subject.startswith('Re:'):
                msg['Subject'] = f"Re: {original_subject}"
            else:
                msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(self.smtp_username, to_email, text)
                
                logger.info(f"Email sent successfully to: {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def mark_email_as_read(self, email_id: str) -> bool:
        """Mark email as read in IMAP server"""
        try:
            imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            imap.login(self.email_username, self.email_password)
            imap.select('INBOX')
            
            # Mark email as read
            imap.store(email_id, '+FLAGS', '\\Seen')
            imap.close()
            imap.logout()
            
            logger.info(f"Email {email_id} marked as read")
            return True
            
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False

    def test_connection(self) -> Dict[str, bool]:
        """Test both IMAP and SMTP connections"""
        results = {'imap': False, 'smtp': False}
        
        # Test IMAP
        try:
            imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            imap.login(self.email_username, self.email_password)
            imap.logout()
            results['imap'] = True
            logger.info("IMAP connection test successful")
        except Exception as e:
            logger.error(f"IMAP connection test failed: {e}")
        
        # Test SMTP
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                results['smtp'] = True
                logger.info("SMTP connection test successful")
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
        
        return results

# Utility functions
def extract_email_address(email_string: str) -> str:
    """Extract email address from 'Name <email@domain.com>' format"""
    import re
    email_pattern = r'<([^>]+)>'
    match = re.search(email_pattern, email_string)
    if match:
        return match.group(1)
    return email_string.strip()

def format_email_for_display(email_info: Dict) -> Dict:
    """Format email information for display"""
    return {
        'id': email_info['id'],
        'sender': extract_email_address(email_info['sender']),
        'subject': email_info['subject'],
        'body': email_info['body'][:200] + "..." if len(email_info['body']) > 200 else email_info['body'],
        'timestamp': email_info['timestamp']
    }

if __name__ == "__main__":
    # Test the email client
    try:
        client = EmailClient()
        results = client.test_connection()
        print(f"Connection test results: {results}")
        
        if all(results.values()):
            print("All connections successful!")
        else:
            print("Some connections failed. Check your credentials.")
            
    except Exception as e:
        print(f"Error initializing email client: {e}") 