
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
import logging
import json
from database import EmailIntent, ReplyTone

# Azure AI imports
try:
    from azure.ai.generative import GenerativeClient
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Initialize Azure AI only
        azure_endpoint = os.getenv("AZURE_AI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_AI_API_KEY")
        
        if not azure_endpoint:
            raise ValueError("AZURE_AI_ENDPOINT not found in environment variables")
        
        if not azure_api_key:
            raise ValueError("AZURE_AI_API_KEY not found in environment variables")
        
        if not AZURE_AVAILABLE:
            raise ValueError("Azure AI SDK not available. Install azure-ai-generative")
        
        try:
            # Use API key authentication
            self.client = GenerativeClient(
                endpoint=azure_endpoint,
                credential=AzureKeyCredential(azure_api_key)
            )
            
            self.model = os.getenv("AZURE_AI_MODEL", "gpt-4")
            logger.info("Azure AI service initialized successfully")
            
        except Exception as e:
            logger.error(f"Azure AI initialization failed: {e}")
            raise ValueError(f"Failed to initialize Azure AI: {e}")
        
    def classify_email_intent(self, subject: str, body: str) -> EmailIntent:
        """Classify the intent of an email using Azure AI"""
        try:
            prompt = f"""
            Analyze the following email and classify its intent into one of these categories:
            - Meeting Request: Someone wants to schedule a meeting or call
            - Job Inquiry: Someone asking about job opportunities or applications
            - Complaint: Someone expressing dissatisfaction or problems
            - Feedback: Someone providing feedback or suggestions
            - Support Request: Someone asking for help or technical support
            - Follow-up: Someone following up on a previous conversation
            - Other: Anything that doesn't fit the above categories

            Email Subject: {subject}
            Email Body: {body}

            Respond with ONLY the category name (e.g., "Meeting Request", "Job Inquiry", etc.)
            """

            response = self.client.generate_content(
                model=self.model,
                prompt=prompt,
                max_tokens=50,
                temperature=0.1
            )
            intent_text = response.choices[0].message.content.strip()
            
            # Map the response to our enum
            intent_mapping = {
                "Meeting Request": EmailIntent.MEETING_REQUEST,
                "Job Inquiry": EmailIntent.JOB_INQUIRY,
                "Complaint": EmailIntent.COMPLAINT,
                "Feedback": EmailIntent.FEEDBACK,
                "Support Request": EmailIntent.SUPPORT_REQUEST,
                "Follow-up": EmailIntent.FOLLOW_UP,
                "Other": EmailIntent.OTHER
            }
            
            return intent_mapping.get(intent_text, EmailIntent.OTHER)
            
        except Exception as e:
            logger.error(f"Error classifying email intent: {e}")
            return EmailIntent.OTHER

    def generate_email_summary(self, subject: str, body: str) -> str:
        """Generate a concise summary of the email using Azure AI"""
        try:
            prompt = f"""
            Provide a brief, professional summary of this email in 2-3 sentences:

            Subject: {subject}
            Body: {body}

            Focus on the key points and action items.
            """

            response = self.client.generate_content(
                model=self.model,
                prompt=prompt,
                max_tokens=150,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating email summary: {e}")
            return "Summary generation failed."

    def generate_draft_reply(self, subject: str, body: str, intent: EmailIntent, tone: ReplyTone, sender_name: str = None) -> str:
        """Generate a draft reply based on email content, intent, and tone"""
        try:
            # Create tone-specific instructions
            tone_instructions = {
                ReplyTone.FORMAL: "Write a formal, professional response using business language and proper etiquette.",
                ReplyTone.FRIENDLY: "Write a warm, friendly response that maintains professionalism while being approachable.",
                ReplyTone.APOLOGETIC: "Write a response that acknowledges any issues and expresses sincere apologies where appropriate.",
                ReplyTone.ASSERTIVE: "Write a confident, direct response that clearly states your position or requirements."
            }
            
            # Create intent-specific context
            intent_context = {
                EmailIntent.MEETING_REQUEST: "This is a meeting request. Consider availability, scheduling preferences, and meeting purpose.",
                EmailIntent.JOB_INQUIRY: "This is a job inquiry. Consider the candidate's qualifications and company hiring process.",
                EmailIntent.COMPLAINT: "This is a complaint. Address concerns professionally and offer solutions.",
                EmailIntent.FEEDBACK: "This is feedback. Acknowledge the input and show appreciation for their time.",
                EmailIntent.SUPPORT_REQUEST: "This is a support request. Provide helpful guidance or escalate appropriately.",
                EmailIntent.FOLLOW_UP: "This is a follow-up. Reference the previous conversation and provide updates.",
                EmailIntent.OTHER: "This is a general inquiry. Provide a helpful and professional response."
            }
            
            prompt = f"""
            Generate a professional email reply based on the following information:

            Original Email:
            Subject: {subject}
            Body: {body}
            
            Intent: {intent.value}
            Tone: {tone.value}
            {f"Sender Name: {sender_name}" if sender_name else ""}

            Instructions:
            {tone_instructions[tone]}
            {intent_context[intent]}
            
            Requirements:
            - Keep the response concise (2-4 sentences)
            - Be professional and appropriate
            - Address the main points of the original email
            - Use the specified tone throughout
            - Include a proper greeting and closing
            - Don't include email headers (From, To, Subject)
            """

            response = self.client.generate_content(
                model=self.model,
                prompt=prompt,
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating draft reply: {e}")
            return "Reply generation failed. Please try again."

    def improve_reply(self, original_reply: str, feedback: str) -> str:
        """Improve a reply based on user feedback"""
        try:
            prompt = f"""
            Improve the following email reply based on the user's feedback:

            Original Reply:
            {original_reply}

            User Feedback:
            {feedback}

            Please provide an improved version that addresses the feedback while maintaining professionalism.
            """

            response = self.client.generate_content(
                model=self.model,
                prompt=prompt,
                max_tokens=400,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error improving reply: {e}")
            return original_reply

    def get_available_tones(self) -> List[Dict]:
        """Get available reply tones with descriptions"""
        return [
            {"value": ReplyTone.FORMAL.value, "description": "Professional and business-like"},
            {"value": ReplyTone.FRIENDLY.value, "description": "Warm and approachable"},
            {"value": ReplyTone.APOLOGETIC.value, "description": "Sincere and apologetic"},
            {"value": ReplyTone.ASSERTIVE.value, "description": "Confident and direct"}
        ]

    def get_available_intents(self) -> List[Dict]:
        """Get available email intents with descriptions"""
        return [
            {"value": EmailIntent.MEETING_REQUEST.value, "description": "Meeting or call scheduling"},
            {"value": EmailIntent.JOB_INQUIRY.value, "description": "Job opportunities or applications"},
            {"value": EmailIntent.COMPLAINT.value, "description": "Dissatisfaction or problems"},
            {"value": EmailIntent.FEEDBACK.value, "description": "Feedback or suggestions"},
            {"value": EmailIntent.SUPPORT_REQUEST.value, "description": "Help or technical support"},
            {"value": EmailIntent.FOLLOW_UP.value, "description": "Following up on previous conversation"},
            {"value": EmailIntent.OTHER.value, "description": "General inquiries"}
        ]

    def test_connection(self) -> bool:
        """Test Azure AI API connection"""
        try:
            response = self.client.generate_content(
                model=self.model,
                prompt="Hello",
                max_tokens=10
            )
            logger.info("Azure AI API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Azure AI API connection test failed: {e}")
            return False

# Utility function to extract sender name from email
def extract_sender_name(email_string: str) -> Optional[str]:
    """Extract sender name from 'Name <email@domain.com>' format"""
    import re
    name_pattern = r'^([^<]+)<'
    match = re.search(name_pattern, email_string)
    if match:
        return match.group(1).strip()
    return None

if __name__ == "__main__":
    # Test the AI service
    try:
        ai_service = AIService()
        
        if ai_service.test_connection():
            print("API connection successful!")
            
            # Test intent classification
            test_subject = "Meeting Request for Project Discussion"
            test_body = "Hi, I would like to schedule a meeting to discuss the project timeline and deliverables."
            
            intent = ai_service.classify_email_intent(test_subject, test_body)
            print(f"Intent classification: {intent.value}")
            
            # Test summary generation
            summary = ai_service.generate_email_summary(test_subject, test_body)
            print(f"Summary: {summary}")
            
            # Test reply generation
            reply = ai_service.generate_draft_reply(test_subject, test_body, intent, ReplyTone.FORMAL)
            print(f"Draft reply: {reply}")
            
        else:
            print("API connection failed. Check your API key.")
            
    except Exception as e:
        print(f"Error testing AI service: {e}") 