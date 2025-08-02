#!/usr/bin/env python3
"""
Test script to demonstrate Pydantic validation functionality
"""

from models import (
    EmailUpdateRequest, ReplyRegenerationRequest, EmailProcessingRequest,
    ReplyToneEnum, EmailStatusEnum, validate_email_address, validate_email_content
)

def test_email_update_validation():
    """Test email update validation"""
    print("Testing Email Update Validation...")
    
    # Valid request
    try:
        valid_request = EmailUpdateRequest(
            draft_reply="Thank you for your email. I will get back to you soon.",
            tone=ReplyToneEnum.FORMAL,
            status=EmailStatusEnum.PENDING
        )
        print("✅ Valid email update request created successfully")
    except Exception as e:
        print(f"❌ Valid request failed: {e}")
    
    # Invalid request - empty reply
    try:
        invalid_request = EmailUpdateRequest(
            draft_reply="",  # Empty reply
            tone=ReplyToneEnum.FORMAL,
            status=EmailStatusEnum.PENDING
        )
        print("❌ Invalid request should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught invalid request: {e}")
    
    # Invalid request - malicious content
    try:
        malicious_request = EmailUpdateRequest(
            draft_reply="<script>alert('xss')</script>Hello there!",
            tone=ReplyToneEnum.FORMAL,
            status=EmailStatusEnum.PENDING
        )
        print("❌ Malicious request should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught malicious content: {e}")

def test_reply_regeneration_validation():
    """Test reply regeneration validation"""
    print("\nTesting Reply Regeneration Validation...")
    
    # Valid request
    try:
        valid_request = ReplyRegenerationRequest(
            tone=ReplyToneEnum.FRIENDLY
        )
        print("✅ Valid reply regeneration request created successfully")
    except Exception as e:
        print(f"❌ Valid request failed: {e}")
    
    # Invalid request - wrong tone type
    try:
        invalid_request = ReplyRegenerationRequest(
            tone="InvalidTone"  # Invalid tone
        )
        print("❌ Invalid request should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught invalid tone: {e}")

def test_email_processing_validation():
    """Test email processing validation"""
    print("\nTesting Email Processing Validation...")
    
    # Valid request
    try:
        valid_request = EmailProcessingRequest(
            force_process=False,
            max_emails=25
        )
        print("✅ Valid email processing request created successfully")
    except Exception as e:
        print(f"❌ Valid request failed: {e}")
    
    # Invalid request - too many emails
    try:
        invalid_request = EmailProcessingRequest(
            force_process=False,
            max_emails=100  # Too many emails
        )
        print("❌ Invalid request should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught too many emails: {e}")

def test_utility_functions():
    """Test utility validation functions"""
    print("\nTesting Utility Validation Functions...")
    
    # Test email address validation
    valid_email = "test@example.com"
    invalid_email = "not-an-email"
    
    if validate_email_address(valid_email):
        print("✅ Valid email address correctly validated")
    else:
        print("❌ Valid email address incorrectly rejected")
    
    if not validate_email_address(invalid_email):
        print("✅ Invalid email address correctly rejected")
    else:
        print("❌ Invalid email address incorrectly accepted")
    
    # Test email content validation
    safe_content = "Hello, this is a safe email content."
    malicious_content = "<script>alert('xss')</script>Hello there!"
    
    if validate_email_content(safe_content):
        print("✅ Safe email content correctly validated")
    else:
        print("❌ Safe email content incorrectly rejected")
    
    if not validate_email_content(malicious_content):
        print("✅ Malicious email content correctly rejected")
    else:
        print("❌ Malicious email content incorrectly accepted")

if __name__ == "__main__":
    print("🧪 Pydantic Validation Test Suite")
    print("=" * 50)
    
    test_email_update_validation()
    test_reply_regeneration_validation()
    test_email_processing_validation()
    test_utility_functions()
    
    print("\n" + "=" * 50)
    print("✅ All validation tests completed!")
    print("\nBenefits of this validation system:")
    print("- 🔒 Prevents XSS attacks")
    print("- 📝 Ensures data integrity")
    print("- 🚫 Blocks malicious content")
    print("- ✅ Validates email formats")
    print("- 🛡️ Protects against injection attacks") 