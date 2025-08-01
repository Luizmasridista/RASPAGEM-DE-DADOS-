#!/usr/bin/env python3
"""
Demo script to test the email notification service functionality.
This script demonstrates the email notification features without actually sending emails.
"""

from datetime import datetime
from services.notification_service import (
    EmailConfig, EmailNotifier, EmailTemplateFormatter,
    NotificationMessage, NotificationLevel, NotificationService
)
from models.data_models import ProductConfig


def demo_email_config_validation():
    """Demonstrate email configuration validation."""
    print("=== Email Configuration Validation Demo ===")
    
    # Valid configuration
    try:
        valid_config = EmailConfig(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="test@gmail.com",
            password="password123",
            from_email="test@gmail.com",
            to_emails=["recipient@gmail.com"]
        )
        print("✅ Valid email configuration created successfully")
        print(f"   SMTP Server: {valid_config.smtp_server}:{valid_config.smtp_port}")
        print(f"   From: {valid_config.from_email}")
        print(f"   To: {', '.join(valid_config.to_emails)}")
    except Exception as e:
        print(f"❌ Error creating valid config: {e}")
    
    # Invalid configuration examples
    invalid_configs = [
        {
            "name": "Empty SMTP server",
            "config": {
                "smtp_server": "",
                "smtp_port": 587,
                "username": "test@gmail.com",
                "password": "password123",
                "from_email": "test@gmail.com",
                "to_emails": ["recipient@gmail.com"]
            }
        },
        {
            "name": "Invalid port",
            "config": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 0,
                "username": "test@gmail.com",
                "password": "password123",
                "from_email": "test@gmail.com",
                "to_emails": ["recipient@gmail.com"]
            }
        },
        {
            "name": "Invalid email address",
            "config": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@gmail.com",
                "password": "password123",
                "from_email": "invalid-email",
                "to_emails": ["recipient@gmail.com"]
            }
        },
        {
            "name": "Empty recipients",
            "config": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@gmail.com",
                "password": "password123",
                "from_email": "test@gmail.com",
                "to_emails": []
            }
        }
    ]
    
    for invalid_config in invalid_configs:
        try:
            EmailConfig(**invalid_config["config"])
            print(f"❌ {invalid_config['name']}: Should have failed but didn't")
        except ValueError as e:
            print(f"✅ {invalid_config['name']}: Correctly rejected - {e}")
        except Exception as e:
            print(f"❓ {invalid_config['name']}: Unexpected error - {e}")
    
    print()


def demo_email_templates():
    """Demonstrate email template formatting."""
    print("=== Email Template Formatting Demo ===")
    
    # Price alert template
    product = ProductConfig(
        nome="Smartphone Samsung Galaxy S24",
        url="https://example.com/smartphone-galaxy-s24",
        preco_alvo=2500.00
    )
    current_price = 2199.99
    
    print("📱 Price Alert Template:")
    html_content = EmailTemplateFormatter.format_price_alert_html(product, current_price)
    print(f"   Product: {product.nome}")
    print(f"   Current Price: R$ {current_price:,.2f}")
    print(f"   Target Price: R$ {product.preco_alvo:,.2f}")
    print(f"   Savings: R$ {product.preco_alvo - current_price:,.2f}")
    print(f"   HTML Length: {len(html_content)} characters")
    print("   ✅ HTML template generated successfully")
    
    # System alert template
    print("\n🔧 System Alert Template:")
    system_levels = [
        (NotificationLevel.INFO, "Sistema iniciado com sucesso"),
        (NotificationLevel.WARNING, "Taxa de falhas de scraping acima do normal"),
        (NotificationLevel.ERROR, "Falha ao conectar com o banco de dados"),
        (NotificationLevel.CRITICAL, "Sistema fora do ar - múltiplas falhas críticas")
    ]
    
    for level, message in system_levels:
        html_content = EmailTemplateFormatter.format_system_alert_html(message, level)
        print(f"   {level.value}: {message}")
        print(f"   HTML Length: {len(html_content)} characters")
        print("   ✅ HTML template generated successfully")
    
    print()


def demo_email_notifier():
    """Demonstrate email notifier functionality (without actually sending emails)."""
    print("=== Email Notifier Demo ===")
    
    # Create email configuration
    email_config = EmailConfig(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="test@gmail.com",
        password="password123",
        from_email="test@gmail.com",
        to_emails=["recipient@gmail.com"]
    )
    
    # Create email notifier
    email_notifier = EmailNotifier(email_config, enabled=False)  # Disabled to avoid actual sending
    print("✅ Email notifier created successfully")
    print(f"   Enabled: {email_notifier.is_enabled()}")
    
    # Test price alert message creation
    price_message = NotificationMessage(
        title="🎯 ALERTA DE PREÇO: Smartphone Samsung Galaxy S24",
        content="Price alert content",
        level=NotificationLevel.INFO,
        timestamp=datetime.now(),
        metadata={
            "product_name": "Smartphone Samsung Galaxy S24",
            "current_price": 2199.99,
            "target_price": 2500.00,
            "url": "https://example.com/smartphone-galaxy-s24"
        }
    )
    
    # Create email message (this tests the internal email creation logic)
    try:
        email_msg = email_notifier._create_email_message(price_message)
        print("✅ Price alert email message created successfully")
        print(f"   Subject: {email_msg['Subject']}")
        print(f"   From: {email_msg['From']}")
        print(f"   To: {email_msg['To']}")
        
        # Check parts
        parts = email_msg.get_payload()
        print(f"   Parts: {len(parts)} (text + HTML)")
        print(f"   Text part type: {parts[0].get_content_type()}")
        print(f"   HTML part type: {parts[1].get_content_type()}")
    except Exception as e:
        print(f"❌ Error creating price alert email: {e}")
    
    # Test system alert message creation
    system_message = NotificationMessage(
        title="🚨 SISTEMA - CRITICAL",
        content="Sistema fora do ar - múltiplas falhas críticas",
        level=NotificationLevel.CRITICAL,
        timestamp=datetime.now(),
        metadata={"system_message": "Sistema fora do ar - múltiplas falhas críticas"}
    )
    
    try:
        email_msg = email_notifier._create_email_message(system_message)
        print("✅ System alert email message created successfully")
        print(f"   Subject: {email_msg['Subject']}")
        print(f"   From: {email_msg['From']}")
        print(f"   To: {email_msg['To']}")
    except Exception as e:
        print(f"❌ Error creating system alert email: {e}")
    
    print()


def demo_notification_service_integration():
    """Demonstrate integration with the main notification service."""
    print("=== Notification Service Integration Demo ===")
    
    # Create notification service
    service = NotificationService()
    print("✅ Notification service created with console notifier")
    
    # Create and add email notifier
    email_config = EmailConfig(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="test@gmail.com",
        password="password123",
        from_email="test@gmail.com",
        to_emails=["recipient@gmail.com"]
    )
    
    email_notifier = EmailNotifier(email_config, enabled=False)  # Disabled for demo
    service.add_notifier("email", email_notifier)
    print("✅ Email notifier added to service")
    print(f"   Available notifiers: {list(service.notifiers.keys())}")
    
    # Test sending price alert through service
    product = ProductConfig(
        nome="Notebook Dell Inspiron 15",
        url="https://example.com/notebook-dell-inspiron",
        preco_alvo=3000.00
    )
    
    print("\n📧 Sending price alert through service...")
    try:
        service.send_price_alert(product, 2799.99)
        print("✅ Price alert sent successfully to all notifiers")
    except Exception as e:
        print(f"❌ Error sending price alert: {e}")
    
    # Test sending system alert through service
    print("\n🔔 Sending system alert through service...")
    try:
        service.send_system_alert("Monitoramento iniciado com sucesso", "INFO")
        print("✅ System alert sent successfully to all notifiers")
    except Exception as e:
        print(f"❌ Error sending system alert: {e}")
    
    print()


def main():
    """Run all email notification demos."""
    print("🚀 Email Notification Service Demo")
    print("=" * 50)
    print()
    
    try:
        demo_email_config_validation()
        demo_email_templates()
        demo_email_notifier()
        demo_notification_service_integration()
        
        print("🎉 All email notification demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Email configuration validation")
        print("✅ HTML email template generation for price alerts")
        print("✅ HTML email template generation for system alerts")
        print("✅ Email message creation with multipart content")
        print("✅ Integration with main notification service")
        print("✅ Support for multiple notification channels")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()