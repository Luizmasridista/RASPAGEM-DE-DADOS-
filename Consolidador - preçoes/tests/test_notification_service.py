"""
Unit tests for the notification service.
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
from io import StringIO
import sys
import smtplib

from services.notification_service import (
    NotificationService, ConsoleNotifier, NotificationFormatter,
    NotificationMessage, NotificationLevel, NotificationColor,
    BaseNotifier, EmailNotifier, EmailConfig, EmailTemplateFormatter
)
from models.data_models import ProductConfig


class TestNotificationFormatter(unittest.TestCase):
    """Test cases for NotificationFormatter utility class."""
    
    def test_format_price(self):
        """Test price formatting with Brazilian currency format."""
        # Test regular price
        self.assertEqual(
            NotificationFormatter.format_price(123.45),
            "R$ 123,45"
        )
        
        # Test price with thousands
        self.assertEqual(
            NotificationFormatter.format_price(1234.56),
            "R$ 1.234,56"
        )
        
        # Test large price
        self.assertEqual(
            NotificationFormatter.format_price(1234567.89),
            "R$ 1.234.567,89"
        )
        
        # Test zero price
        self.assertEqual(
            NotificationFormatter.format_price(0.0),
            "R$ 0,00"
        )
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        test_datetime = datetime(2024, 1, 15, 14, 30, 45)
        formatted = NotificationFormatter.format_timestamp(test_datetime)
        self.assertEqual(formatted, "15/01/2024 14:30:45")
    
    def test_format_product_alert(self):
        """Test product alert message formatting."""
        product = ProductConfig(
            nome="Produto Teste",
            url="https://example.com/produto",
            preco_alvo=100.0
        )
        current_price = 85.0
        
        result = NotificationFormatter.format_product_alert(product, current_price)
        
        # Check title
        self.assertIn("ALERTA DE PREÇO", result["title"])
        self.assertIn("Produto Teste", result["title"])
        
        # Check content
        content = result["content"]
        self.assertIn("Produto Teste", content)
        self.assertIn("R$ 85,00", content)  # Current price
        self.assertIn("R$ 100,00", content)  # Target price
        self.assertIn("R$ 15,00", content)  # Savings
        self.assertIn("15.0%", content)  # Savings percentage
        self.assertIn("https://example.com/produto", content)
    
    def test_format_system_alert(self):
        """Test system alert message formatting."""
        message = "Sistema iniciado com sucesso"
        level = NotificationLevel.INFO
        
        result = NotificationFormatter.format_system_alert(message, level)
        
        # Check title
        self.assertIn("SISTEMA", result["title"])
        self.assertIn("INFO", result["title"])
        
        # Check content
        self.assertIn(message, result["content"])
        self.assertIn(":", result["content"])  # Timestamp separator
    
    def test_colorize_text(self):
        """Test text colorization."""
        text = "Test message"
        
        # Test basic colorization
        colored = NotificationFormatter.colorize_text(text, NotificationColor.RED)
        self.assertIn(NotificationColor.RED.value, colored)
        self.assertIn(NotificationColor.RESET.value, colored)
        self.assertIn(text, colored)
        
        # Test bold colorization
        bold_colored = NotificationFormatter.colorize_text(text, NotificationColor.GREEN, bold=True)
        self.assertIn(NotificationColor.BOLD.value, bold_colored)
        self.assertIn(NotificationColor.GREEN.value, bold_colored)
        self.assertIn(NotificationColor.RESET.value, bold_colored)


class TestNotificationMessage(unittest.TestCase):
    """Test cases for NotificationMessage data class."""
    
    def test_valid_notification_message(self):
        """Test creating a valid notification message."""
        message = NotificationMessage(
            title="Test Title",
            content="Test content",
            level=NotificationLevel.INFO,
            timestamp=datetime.now()
        )
        
        self.assertEqual(message.title, "Test Title")
        self.assertEqual(message.content, "Test content")
        self.assertEqual(message.level, NotificationLevel.INFO)
        self.assertIsInstance(message.timestamp, datetime)
    
    def test_empty_title_validation(self):
        """Test validation of empty title."""
        with self.assertRaises(ValueError) as context:
            NotificationMessage(
                title="",
                content="Test content",
                level=NotificationLevel.INFO,
                timestamp=datetime.now()
            )
        
        self.assertIn("Título da notificação não pode estar vazio", str(context.exception))
    
    def test_empty_content_validation(self):
        """Test validation of empty content."""
        with self.assertRaises(ValueError) as context:
            NotificationMessage(
                title="Test Title",
                content="",
                level=NotificationLevel.INFO,
                timestamp=datetime.now()
            )
        
        self.assertIn("Conteúdo da notificação não pode estar vazio", str(context.exception))
    
    def test_whitespace_only_validation(self):
        """Test validation of whitespace-only title and content."""
        with self.assertRaises(ValueError):
            NotificationMessage(
                title="   ",
                content="Test content",
                level=NotificationLevel.INFO,
                timestamp=datetime.now()
            )
        
        with self.assertRaises(ValueError):
            NotificationMessage(
                title="Test Title",
                content="   ",
                level=NotificationLevel.INFO,
                timestamp=datetime.now()
            )


class MockNotifier(BaseNotifier):
    """Mock notifier for testing purposes."""
    
    def __init__(self, enabled: bool = True, should_fail: bool = False):
        super().__init__(enabled)
        self.should_fail = should_fail
        self.sent_messages = []
    
    def send_notification(self, message: NotificationMessage) -> bool:
        if self.should_fail:
            raise Exception("Mock notifier failure")
        
        self.sent_messages.append(message)
        return True


class TestConsoleNotifier(unittest.TestCase):
    """Test cases for ConsoleNotifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.notifier = ConsoleNotifier(use_colors=False)  # Disable colors for testing
        self.test_message = NotificationMessage(
            title="Test Alert",
            content="This is a test message",
            level=NotificationLevel.INFO,
            timestamp=datetime(2024, 1, 15, 14, 30, 45)
        )
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_send_notification_success(self, mock_stdout):
        """Test successful notification sending."""
        result = self.notifier.send_notification(self.test_message)
        
        self.assertTrue(result)
        output = mock_stdout.getvalue()
        self.assertIn("Test Alert", output)
        self.assertIn("This is a test message", output)
        self.assertIn("[INFO]", output)
        self.assertIn("15/01/2024 14:30:45", output)
    
    def test_send_notification_disabled(self):
        """Test notification sending when notifier is disabled."""
        self.notifier.disable()
        result = self.notifier.send_notification(self.test_message)
        
        self.assertFalse(result)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_colored_output(self, mock_stdout):
        """Test colored console output."""
        colored_notifier = ConsoleNotifier(use_colors=True)
        
        # Test different levels
        levels_to_test = [
            NotificationLevel.INFO,
            NotificationLevel.WARNING,
            NotificationLevel.ERROR,
            NotificationLevel.CRITICAL
        ]
        
        for level in levels_to_test:
            message = NotificationMessage(
                title=f"Test {level.value}",
                content="Test content",
                level=level,
                timestamp=datetime.now()
            )
            
            result = colored_notifier.send_notification(message)
            self.assertTrue(result)
            
            output = mock_stdout.getvalue()
            # Should contain ANSI color codes when colors are enabled
            self.assertIn("\033[", output)
    
    def test_enable_disable_functionality(self):
        """Test enable/disable functionality."""
        # Initially enabled
        self.assertTrue(self.notifier.is_enabled())
        
        # Disable
        self.notifier.disable()
        self.assertFalse(self.notifier.is_enabled())
        
        # Enable again
        self.notifier.enable()
        self.assertTrue(self.notifier.is_enabled())


class TestNotificationService(unittest.TestCase):
    """Test cases for NotificationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = NotificationService()
        self.test_product = ProductConfig(
            nome="Produto Teste",
            url="https://example.com/produto",
            preco_alvo=100.0
        )
    
    def test_initialization(self):
        """Test service initialization with default console notifier."""
        self.assertIn("console", self.service.notifiers)
        self.assertIsInstance(self.service.get_notifier("console"), ConsoleNotifier)
    
    def test_add_remove_notifier(self):
        """Test adding and removing notifiers."""
        mock_notifier = MockNotifier()
        
        # Add notifier
        self.service.add_notifier("mock", mock_notifier)
        self.assertIn("mock", self.service.notifiers)
        self.assertEqual(self.service.get_notifier("mock"), mock_notifier)
        
        # Remove notifier
        result = self.service.remove_notifier("mock")
        self.assertTrue(result)
        self.assertNotIn("mock", self.service.notifiers)
        
        # Try to remove non-existent notifier
        result = self.service.remove_notifier("nonexistent")
        self.assertFalse(result)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_send_price_alert(self, mock_stdout):
        """Test sending price alert."""
        current_price = 85.0
        
        self.service.send_price_alert(self.test_product, current_price)
        
        output = mock_stdout.getvalue()
        self.assertIn("ALERTA DE PREÇO", output)
        self.assertIn("Produto Teste", output)
        self.assertIn("R$ 85,00", output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_send_system_alert(self, mock_stdout):
        """Test sending system alert."""
        message = "Sistema iniciado"
        
        self.service.send_system_alert(message, "INFO")
        
        output = mock_stdout.getvalue()
        self.assertIn("SISTEMA", output)
        self.assertIn("INFO", output)
        self.assertIn(message, output)
    
    def test_send_system_alert_invalid_level(self):
        """Test sending system alert with invalid level."""
        # Should not raise exception, but log error
        with patch.object(self.service.logger, 'error') as mock_logger:
            self.service.send_system_alert("Test message", "INVALID_LEVEL")
            mock_logger.assert_called_once()
    
    def test_multiple_notifiers(self):
        """Test sending notifications through multiple notifiers."""
        # Add mock notifiers
        mock1 = MockNotifier()
        mock2 = MockNotifier()
        
        self.service.add_notifier("mock1", mock1)
        self.service.add_notifier("mock2", mock2)
        
        # Send alert
        self.service.send_price_alert(self.test_product, 85.0)
        
        # Check that both mock notifiers received the message
        self.assertEqual(len(mock1.sent_messages), 1)
        self.assertEqual(len(mock2.sent_messages), 1)
        
        # Check message content
        message = mock1.sent_messages[0]
        self.assertIn("ALERTA DE PREÇO", message.title)
        self.assertIn("Produto Teste", message.content)
    
    def test_notifier_failure_handling(self):
        """Test handling of notifier failures."""
        # Add failing notifier
        failing_notifier = MockNotifier(should_fail=True)
        self.service.add_notifier("failing", failing_notifier)
        
        # Should not raise exception
        with patch.object(self.service.logger, 'error') as mock_logger:
            self.service.send_system_alert("Test message")
            # Should log the error
            mock_logger.assert_called()
    
    def test_disabled_notifier_skipped(self):
        """Test that disabled notifiers are skipped."""
        mock_notifier = MockNotifier()
        mock_notifier.disable()
        
        self.service.add_notifier("disabled", mock_notifier)
        self.service.send_system_alert("Test message")
        
        # Should not have received any messages
        self.assertEqual(len(mock_notifier.sent_messages), 0)


class TestEmailConfig(unittest.TestCase):
    """Test cases for EmailConfig data class."""
    
    def test_valid_email_config(self):
        """Test creating a valid email configuration."""
        config = EmailConfig(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="test@gmail.com",
            password="password123",
            from_email="test@gmail.com",
            to_emails=["recipient@gmail.com"]
        )
        
        self.assertEqual(config.smtp_server, "smtp.gmail.com")
        self.assertEqual(config.smtp_port, 587)
        self.assertTrue(config.use_tls)
    
    def test_empty_smtp_server_validation(self):
        """Test validation of empty SMTP server."""
        with self.assertRaises(ValueError) as context:
            EmailConfig(
                smtp_server="",
                smtp_port=587,
                username="test@gmail.com",
                password="password123",
                from_email="test@gmail.com",
                to_emails=["recipient@gmail.com"]
            )
        
        self.assertIn("SMTP server não pode estar vazio", str(context.exception))
    
    def test_invalid_smtp_port_validation(self):
        """Test validation of invalid SMTP port."""
        with self.assertRaises(ValueError) as context:
            EmailConfig(
                smtp_server="smtp.gmail.com",
                smtp_port=0,
                username="test@gmail.com",
                password="password123",
                from_email="test@gmail.com",
                to_emails=["recipient@gmail.com"]
            )
        
        self.assertIn("SMTP port deve estar entre 1 e 65535", str(context.exception))
    
    def test_invalid_email_validation(self):
        """Test validation of invalid email addresses."""
        with self.assertRaises(ValueError) as context:
            EmailConfig(
                smtp_server="smtp.gmail.com",
                smtp_port=587,
                username="test@gmail.com",
                password="password123",
                from_email="invalid-email",
                to_emails=["recipient@gmail.com"]
            )
        
        self.assertIn("From email deve ser um endereço válido", str(context.exception))
    
    def test_empty_recipients_validation(self):
        """Test validation of empty recipients list."""
        with self.assertRaises(ValueError) as context:
            EmailConfig(
                smtp_server="smtp.gmail.com",
                smtp_port=587,
                username="test@gmail.com",
                password="password123",
                from_email="test@gmail.com",
                to_emails=[]
            )
        
        self.assertIn("Lista de destinatários não pode estar vazia", str(context.exception))


class TestEmailTemplateFormatter(unittest.TestCase):
    """Test cases for EmailTemplateFormatter utility class."""
    
    def test_format_price_alert_html(self):
        """Test HTML formatting for price alerts."""
        product = ProductConfig(
            nome="Produto Teste",
            url="https://example.com/produto",
            preco_alvo=100.0
        )
        current_price = 85.0
        
        html = EmailTemplateFormatter.format_price_alert_html(product, current_price)
        
        # Check HTML structure
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html>", html)
        self.assertIn("</html>", html)
        
        # Check content
        self.assertIn("ALERTA DE PREÇO", html)
        self.assertIn("Produto Teste", html)
        self.assertIn("R$ 85,00", html)
        self.assertIn("R$ 100,00", html)
        self.assertIn("R$ 15,00", html)
        self.assertIn("15.0%", html)
        self.assertIn("https://example.com/produto", html)
        
        # Check styling
        self.assertIn("background-color:", html)
        self.assertIn("font-family:", html)
    
    def test_format_system_alert_html(self):
        """Test HTML formatting for system alerts."""
        message = "Sistema iniciado com sucesso"
        level = NotificationLevel.INFO
        
        html = EmailTemplateFormatter.format_system_alert_html(message, level)
        
        # Check HTML structure
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html>", html)
        self.assertIn("</html>", html)
        
        # Check content
        self.assertIn("ALERTA DO SISTEMA", html)
        self.assertIn("INFO", html)
        self.assertIn(message, html)
        
        # Check styling
        self.assertIn("background-color:", html)
        self.assertIn("#28a745", html)  # INFO color
    
    def test_different_alert_levels_html(self):
        """Test HTML formatting for different alert levels."""
        levels_to_test = [
            (NotificationLevel.WARNING, "#ffc107"),
            (NotificationLevel.ERROR, "#dc3545"),
            (NotificationLevel.CRITICAL, "#6f42c1")
        ]
        
        for level, expected_color in levels_to_test:
            html = EmailTemplateFormatter.format_system_alert_html("Test message", level)
            self.assertIn(expected_color, html)
            self.assertIn(level.value, html)


class TestEmailNotifier(unittest.TestCase):
    """Test cases for EmailNotifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.email_config = EmailConfig(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="test@gmail.com",
            password="password123",
            from_email="test@gmail.com",
            to_emails=["recipient@gmail.com"]
        )
        self.notifier = EmailNotifier(self.email_config)
        self.test_message = NotificationMessage(
            title="Test Alert",
            content="This is a test message",
            level=NotificationLevel.INFO,
            timestamp=datetime(2024, 1, 15, 14, 30, 45)
        )
    
    def test_initialization(self):
        """Test email notifier initialization."""
        self.assertEqual(self.notifier.email_config, self.email_config)
        self.assertTrue(self.notifier.is_enabled())
    
    def test_send_notification_disabled(self):
        """Test notification sending when notifier is disabled."""
        self.notifier.disable()
        result = self.notifier.send_notification(self.test_message)
        
        self.assertFalse(result)
    
    @patch('smtplib.SMTP')
    def test_send_notification_success(self, mock_smtp):
        """Test successful email notification sending."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = self.notifier.send_notification(self.test_message)
        
        self.assertTrue(result)
        
        # Verify SMTP calls
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "password123")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_notification_smtp_auth_error(self, mock_smtp):
        """Test handling of SMTP authentication errors."""
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value = mock_server
        
        result = self.notifier.send_notification(self.test_message)
        
        self.assertFalse(result)
    
    @patch('smtplib.SMTP')
    def test_send_notification_recipients_refused(self, mock_smtp):
        """Test handling of recipients refused errors."""
        mock_server = Mock()
        mock_server.sendmail.side_effect = smtplib.SMTPRecipientsRefused({"recipient@gmail.com": (550, "User unknown")})
        mock_smtp.return_value = mock_server
        
        result = self.notifier.send_notification(self.test_message)
        
        self.assertFalse(result)
    
    @patch('smtplib.SMTP')
    def test_send_price_alert_email(self, mock_smtp):
        """Test sending price alert email with metadata."""
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        # Create price alert message with metadata
        price_message = NotificationMessage(
            title="🎯 ALERTA DE PREÇO: Produto Teste",
            content="Price alert content",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(),
            metadata={
                "product_name": "Produto Teste",
                "current_price": 85.0,
                "target_price": 100.0,
                "url": "https://example.com/produto"
            }
        )
        
        result = self.notifier.send_notification(price_message)
        
        self.assertTrue(result)
        mock_server.sendmail.assert_called_once()
        
        # Check that sendmail was called with proper arguments
        args, kwargs = mock_server.sendmail.call_args
        self.assertEqual(args[0], "test@gmail.com")  # from_email
        self.assertEqual(args[1], ["recipient@gmail.com"])  # to_emails
        # Check that the email content is a string (basic validation)
        email_content = args[2]
        self.assertIsInstance(email_content, str)
        self.assertIn("Subject:", email_content)
        self.assertIn("Content-Type:", email_content)
    
    @patch('smtplib.SMTP')
    def test_test_connection_success(self, mock_smtp):
        """Test successful SMTP connection test."""
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = self.notifier.test_connection()
        
        self.assertTrue(result)
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "password123")
        mock_server.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_test_connection_failure(self, mock_smtp):
        """Test SMTP connection test failure."""
        mock_smtp.side_effect = Exception("Connection failed")
        
        result = self.notifier.test_connection()
        
        self.assertFalse(result)
    
    def test_create_email_message_system_alert(self):
        """Test creating email message for system alert."""
        email_msg = self.notifier._create_email_message(self.test_message)
        
        self.assertEqual(email_msg["Subject"], "Test Alert")
        self.assertEqual(email_msg["From"], "test@gmail.com")
        self.assertEqual(email_msg["To"], "recipient@gmail.com")
        
        # Check that message has both text and HTML parts
        parts = email_msg.get_payload()
        self.assertEqual(len(parts), 2)
        
        # Check text part
        text_part = parts[0]
        self.assertEqual(text_part.get_content_type(), "text/plain")
        # Decode base64 content for testing
        import base64
        text_content = base64.b64decode(text_part.get_payload()).decode('utf-8')
        self.assertIn("Test Alert", text_content)
        
        # Check HTML part
        html_part = parts[1]
        self.assertEqual(html_part.get_content_type(), "text/html")
        # Decode base64 content for testing
        html_content = base64.b64decode(html_part.get_payload()).decode('utf-8')
        self.assertIn("<!DOCTYPE html>", html_content)
    
    def test_create_email_message_price_alert(self):
        """Test creating email message for price alert."""
        price_message = NotificationMessage(
            title="🎯 ALERTA DE PREÇO: Produto Teste",
            content="Price alert content",
            level=NotificationLevel.INFO,
            timestamp=datetime.now(),
            metadata={
                "product_name": "Produto Teste",
                "current_price": 85.0,
                "target_price": 100.0,
                "url": "https://example.com/produto"
            }
        )
        
        email_msg = self.notifier._create_email_message(price_message)
        
        # Check that message has both text and HTML parts
        parts = email_msg.get_payload()
        self.assertEqual(len(parts), 2)
        
        # Check HTML part contains price alert specific content
        html_part = parts[1]
        # Decode base64 content for testing
        import base64
        html_content = base64.b64decode(html_part.get_payload()).decode('utf-8')
        self.assertIn("Produto Teste", html_content)
        self.assertIn("R$ 85,00", html_content)
        self.assertIn("R$ 100,00", html_content)


class TestNotificationServiceWithEmail(unittest.TestCase):
    """Test cases for NotificationService with email integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = NotificationService()
        self.email_config = EmailConfig(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="test@gmail.com",
            password="password123",
            from_email="test@gmail.com",
            to_emails=["recipient@gmail.com"]
        )
        self.test_product = ProductConfig(
            nome="Produto Teste",
            url="https://example.com/produto",
            preco_alvo=100.0
        )
    
    @patch('smtplib.SMTP')
    def test_add_email_notifier(self, mock_smtp):
        """Test adding email notifier to service."""
        email_notifier = EmailNotifier(self.email_config)
        self.service.add_notifier("email", email_notifier)
        
        self.assertIn("email", self.service.notifiers)
        self.assertIsInstance(self.service.get_notifier("email"), EmailNotifier)
    
    @patch('smtplib.SMTP')
    @patch('sys.stdout', new_callable=StringIO)
    def test_send_alert_to_multiple_notifiers(self, mock_stdout, mock_smtp):
        """Test sending alerts to both console and email notifiers."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        # Add email notifier
        email_notifier = EmailNotifier(self.email_config)
        self.service.add_notifier("email", email_notifier)
        
        # Send price alert
        self.service.send_price_alert(self.test_product, 85.0)
        
        # Check console output
        console_output = mock_stdout.getvalue()
        self.assertIn("ALERTA DE PREÇO", console_output)
        
        # Check email was sent
        mock_server.sendmail.assert_called_once()


if __name__ == '__main__':
    unittest.main()