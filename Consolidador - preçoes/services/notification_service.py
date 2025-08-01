"""
Notification service implementation for the price monitoring system.
"""
import logging
import smtplib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from models.data_models import ProductConfig, SystemConfig
from models.interfaces import NotificationServiceInterface


class NotificationLevel(Enum):
    """Notification severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NotificationColor(Enum):
    """ANSI color codes for console output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


@dataclass
class NotificationMessage:
    """Structured notification message."""
    title: str
    content: str
    level: NotificationLevel
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate notification message after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Título da notificação não pode estar vazio")
        if not self.content or not self.content.strip():
            raise ValueError("Conteúdo da notificação não pode estar vazio")


class BaseNotifier(ABC):
    """Abstract base class for notification implementations."""
    
    def __init__(self, enabled: bool = True):
        """Initialize base notifier.
        
        Args:
            enabled: Whether this notifier is enabled
        """
        self.enabled = enabled
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def send_notification(self, message: NotificationMessage) -> bool:
        """Send a notification message.
        
        Args:
            message: The notification message to send
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if this notifier is enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable this notifier."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable this notifier."""
        self.enabled = False


class NotificationFormatter:
    """Utility class for formatting notification messages."""
    
    @staticmethod
    def format_price(price: float) -> str:
        """Format price with Brazilian currency format.
        
        Args:
            price: Price value to format
            
        Returns:
            Formatted price string
        """
        return f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    @staticmethod
    def format_timestamp(timestamp: datetime) -> str:
        """Format timestamp for display.
        
        Args:
            timestamp: Datetime to format
            
        Returns:
            Formatted timestamp string
        """
        return timestamp.strftime("%d/%m/%Y %H:%M:%S")
    
    @staticmethod
    def format_product_alert(product: ProductConfig, current_price: float) -> Dict[str, str]:
        """Format product price alert message.
        
        Args:
            product: Product configuration
            current_price: Current price found
            
        Returns:
            Dictionary with formatted title and content
        """
        savings = product.preco_alvo - current_price
        savings_percent = (savings / product.preco_alvo) * 100
        
        title = f"🎯 ALERTA DE PREÇO: {product.nome}"
        
        content = (
            f"O produto '{product.nome}' atingiu o preço alvo!\n\n"
            f"💰 Preço atual: {NotificationFormatter.format_price(current_price)}\n"
            f"🎯 Preço alvo: {NotificationFormatter.format_price(product.preco_alvo)}\n"
            f"💸 Economia: {NotificationFormatter.format_price(savings)} ({savings_percent:.1f}%)\n"
            f"🔗 Link: {product.url}\n"
            f"⏰ Verificado em: {NotificationFormatter.format_timestamp(datetime.now())}"
        )
        
        return {"title": title, "content": content}
    
    @staticmethod
    def format_system_alert(message: str, level: NotificationLevel) -> Dict[str, str]:
        """Format system alert message.
        
        Args:
            message: System message
            level: Alert level
            
        Returns:
            Dictionary with formatted title and content
        """
        level_icons = {
            NotificationLevel.DEBUG: "🔍",
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨"
        }
        
        icon = level_icons.get(level, "📢")
        title = f"{icon} SISTEMA - {level.value}"
        
        content = (
            f"{message}\n"
            f"⏰ {NotificationFormatter.format_timestamp(datetime.now())}"
        )
        
        return {"title": title, "content": content}
    
    @staticmethod
    def colorize_text(text: str, color: NotificationColor, bold: bool = False) -> str:
        """Add ANSI color codes to text.
        
        Args:
            text: Text to colorize
            color: Color to apply
            bold: Whether to make text bold
            
        Returns:
            Colorized text string
        """
        result = color.value + text + NotificationColor.RESET.value
        if bold:
            result = NotificationColor.BOLD.value + result
        return result


class ConsoleNotifier(BaseNotifier):
    """Console-based notification implementation with colored output."""
    
    def __init__(self, enabled: bool = True, use_colors: bool = True):
        """Initialize console notifier.
        
        Args:
            enabled: Whether this notifier is enabled
            use_colors: Whether to use colored output
        """
        super().__init__(enabled)
        self.use_colors = use_colors
        self.level_colors = {
            NotificationLevel.DEBUG: NotificationColor.CYAN,
            NotificationLevel.INFO: NotificationColor.GREEN,
            NotificationLevel.WARNING: NotificationColor.YELLOW,
            NotificationLevel.ERROR: NotificationColor.RED,
            NotificationLevel.CRITICAL: NotificationColor.MAGENTA
        }
    
    def send_notification(self, message: NotificationMessage) -> bool:
        """Send notification to console with colored output.
        
        Args:
            message: The notification message to send
            
        Returns:
            True if notification was printed successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Format the notification
            formatted_message = self._format_console_message(message)
            
            # Print to console
            print(formatted_message)
            
            # Also log the message
            log_level = getattr(logging, message.level.value)
            self.logger.log(log_level, f"{message.title}: {message.content}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação para console: {e}")
            return False
    
    def _format_console_message(self, message: NotificationMessage) -> str:
        """Format message for console display.
        
        Args:
            message: Message to format
            
        Returns:
            Formatted console message
        """
        separator = "=" * 60
        timestamp = NotificationFormatter.format_timestamp(message.timestamp)
        
        # Choose color based on level
        color = self.level_colors.get(message.level, NotificationColor.WHITE)
        
        if self.use_colors:
            title = NotificationFormatter.colorize_text(message.title, color, bold=True)
            level_text = NotificationFormatter.colorize_text(f"[{message.level.value}]", color)
            separator_colored = NotificationFormatter.colorize_text(separator, color)
        else:
            title = message.title
            level_text = f"[{message.level.value}]"
            separator_colored = separator
        
        formatted = (
            f"\n{separator_colored}\n"
            f"{level_text} {title}\n"
            f"⏰ {timestamp}\n"
            f"{separator_colored}\n"
            f"{message.content}\n"
            f"{separator_colored}\n"
        )
        
        return formatted


@dataclass
class EmailConfig:
    """Email configuration settings."""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    to_emails: list[str]
    use_tls: bool = True
    
    def __post_init__(self):
        """Validate email configuration after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """Validate email configuration integrity."""
        errors = []
        
        if not self.smtp_server or not self.smtp_server.strip():
            errors.append("SMTP server não pode estar vazio")
        
        if self.smtp_port <= 0 or self.smtp_port > 65535:
            errors.append("SMTP port deve estar entre 1 e 65535")
        
        if not self.username or not self.username.strip():
            errors.append("Username não pode estar vazio")
        
        if not self.password or not self.password.strip():
            errors.append("Password não pode estar vazio")
        
        if not self.from_email or not self.from_email.strip():
            errors.append("From email não pode estar vazio")
        elif "@" not in self.from_email:
            errors.append("From email deve ser um endereço válido")
        
        if not self.to_emails or len(self.to_emails) == 0:
            errors.append("Lista de destinatários não pode estar vazia")
        else:
            for email in self.to_emails:
                if not email or "@" not in email:
                    errors.append(f"Email destinatário inválido: {email}")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return True


class EmailTemplateFormatter:
    """Utility class for formatting email templates."""
    
    @staticmethod
    def format_price_alert_html(product: ProductConfig, current_price: float) -> str:
        """Format price alert as HTML email.
        
        Args:
            product: Product configuration
            current_price: Current price found
            
        Returns:
            HTML formatted email content
        """
        savings = product.preco_alvo - current_price
        savings_percent = (savings / product.preco_alvo) * 100
        timestamp = NotificationFormatter.format_timestamp(datetime.now())
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: #28a745; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ padding: 30px; }}
                .product-info {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .price-current {{ color: #28a745; font-size: 24px; font-weight: bold; }}
                .price-target {{ color: #6c757d; font-size: 18px; }}
                .savings {{ color: #dc3545; font-size: 20px; font-weight: bold; }}
                .button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; color: #6c757d; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 ALERTA DE PREÇO</h1>
                    <h2>{product.nome}</h2>
                </div>
                
                <div class="content">
                    <p>Ótimas notícias! O produto que você está monitorando atingiu o preço alvo.</p>
                    
                    <div class="product-info">
                        <h3>📦 {product.nome}</h3>
                        
                        <p><strong>💰 Preço atual:</strong> <span class="price-current">{NotificationFormatter.format_price(current_price)}</span></p>
                        <p><strong>🎯 Preço alvo:</strong> <span class="price-target">{NotificationFormatter.format_price(product.preco_alvo)}</span></p>
                        <p><strong>💸 Economia:</strong> <span class="savings">{NotificationFormatter.format_price(savings)} ({savings_percent:.1f}%)</span></p>
                        
                        <a href="{product.url}" class="button">🛒 Ver Produto</a>
                    </div>
                    
                    <p><strong>⏰ Verificado em:</strong> {timestamp}</p>
                    
                    <p><em>Aproveite esta oportunidade antes que o preço suba novamente!</em></p>
                </div>
                
                <div class="footer">
                    <p>Sistema de Monitoramento de Preços</p>
                    <p>Este é um email automático. Não responda a esta mensagem.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    @staticmethod
    def format_system_alert_html(message: str, level: NotificationLevel) -> str:
        """Format system alert as HTML email.
        
        Args:
            message: System message
            level: Alert level
            
        Returns:
            HTML formatted email content
        """
        level_colors = {
            NotificationLevel.DEBUG: "#17a2b8",
            NotificationLevel.INFO: "#28a745",
            NotificationLevel.WARNING: "#ffc107",
            NotificationLevel.ERROR: "#dc3545",
            NotificationLevel.CRITICAL: "#6f42c1"
        }
        
        level_icons = {
            NotificationLevel.DEBUG: "🔍",
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨"
        }
        
        color = level_colors.get(level, "#6c757d")
        icon = level_icons.get(level, "📢")
        timestamp = NotificationFormatter.format_timestamp(datetime.now())
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ padding: 30px; }}
                .alert-box {{ background-color: #f8f9fa; padding: 20px; border-left: 4px solid {color}; margin: 20px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; color: #6c757d; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{icon} ALERTA DO SISTEMA</h1>
                    <h2>{level.value}</h2>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <p><strong>Mensagem:</strong></p>
                        <p>{message}</p>
                    </div>
                    
                    <p><strong>⏰ Data/Hora:</strong> {timestamp}</p>
                </div>
                
                <div class="footer">
                    <p>Sistema de Monitoramento de Preços</p>
                    <p>Este é um email automático. Não responda a esta mensagem.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template


class EmailNotifier(BaseNotifier):
    """Email-based notification implementation with HTML formatting."""
    
    def __init__(self, email_config: EmailConfig, enabled: bool = True):
        """Initialize email notifier.
        
        Args:
            email_config: Email configuration settings
            enabled: Whether this notifier is enabled
        """
        super().__init__(enabled)
        self.email_config = email_config
        self.smtp_connection = None
    
    def send_notification(self, message: NotificationMessage) -> bool:
        """Send notification via email.
        
        Args:
            message: The notification message to send
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Create email message
            email_msg = self._create_email_message(message)
            
            # Send email
            success = self._send_email(email_msg)
            
            if success:
                self.logger.info(f"Email enviado com sucesso: {message.title}")
            else:
                self.logger.error(f"Falha ao enviar email: {message.title}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificação por email: {e}")
            return False
    
    def _create_email_message(self, message: NotificationMessage) -> MIMEMultipart:
        """Create email message from notification.
        
        Args:
            message: Notification message to convert
            
        Returns:
            Email message ready to send
        """
        # Create multipart message
        email_msg = MIMEMultipart("alternative")
        email_msg["Subject"] = message.title
        email_msg["From"] = self.email_config.from_email
        email_msg["To"] = ", ".join(self.email_config.to_emails)
        
        # Create plain text version
        text_content = f"{message.title}\n\n{message.content}"
        text_part = MIMEText(text_content, "plain", "utf-8")
        
        # Create HTML version based on message type
        if message.metadata and "product_name" in message.metadata:
            # Price alert
            product = ProductConfig(
                nome=message.metadata["product_name"],
                url=message.metadata["url"],
                preco_alvo=message.metadata["target_price"]
            )
            html_content = EmailTemplateFormatter.format_price_alert_html(
                product, message.metadata["current_price"]
            )
        else:
            # System alert
            system_message = message.metadata.get("system_message", message.content) if message.metadata else message.content
            html_content = EmailTemplateFormatter.format_system_alert_html(
                system_message, message.level
            )
        
        html_part = MIMEText(html_content, "html", "utf-8")
        
        # Attach parts
        email_msg.attach(text_part)
        email_msg.attach(html_part)
        
        return email_msg
    
    def _send_email(self, email_msg: MIMEMultipart) -> bool:
        """Send email message via SMTP.
        
        Args:
            email_msg: Email message to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create SMTP connection
            server = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
            
            # Enable TLS if configured
            if self.email_config.use_tls:
                server.starttls()
            
            # Login to server
            server.login(self.email_config.username, self.email_config.password)
            
            # Send email
            text = email_msg.as_string()
            server.sendmail(
                self.email_config.from_email,
                self.email_config.to_emails,
                text
            )
            
            # Close connection
            server.quit()
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"Erro de autenticação SMTP: {e}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            self.logger.error(f"Destinatários recusados: {e}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            self.logger.error(f"Servidor SMTP desconectado: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro geral ao enviar email: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test SMTP connection and authentication.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            server = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
            
            if self.email_config.use_tls:
                server.starttls()
            
            server.login(self.email_config.username, self.email_config.password)
            server.quit()
            
            self.logger.info("Teste de conexão SMTP bem-sucedido")
            return True
            
        except Exception as e:
            self.logger.error(f"Falha no teste de conexão SMTP: {e}")
            return False


class NotificationService(NotificationServiceInterface):
    """Main notification service that coordinates multiple notifiers."""
    
    def __init__(self):
        """Initialize notification service with default console notifier."""
        self.notifiers: Dict[str, BaseNotifier] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Add default console notifier
        self.add_notifier("console", ConsoleNotifier())
    
    def add_notifier(self, name: str, notifier: BaseNotifier) -> None:
        """Add a notifier to the service.
        
        Args:
            name: Unique name for the notifier
            notifier: Notifier instance to add
        """
        self.notifiers[name] = notifier
        self.logger.info(f"Notificador '{name}' adicionado ao serviço")
    
    def remove_notifier(self, name: str) -> bool:
        """Remove a notifier from the service.
        
        Args:
            name: Name of the notifier to remove
            
        Returns:
            True if notifier was removed, False if not found
        """
        if name in self.notifiers:
            del self.notifiers[name]
            self.logger.info(f"Notificador '{name}' removido do serviço")
            return True
        return False
    
    def get_notifier(self, name: str) -> Optional[BaseNotifier]:
        """Get a notifier by name.
        
        Args:
            name: Name of the notifier
            
        Returns:
            Notifier instance or None if not found
        """
        return self.notifiers.get(name)
    
    def send_price_alert(self, product: ProductConfig, current_price: float) -> None:
        """Send a price alert notification.
        
        Args:
            product: Product configuration
            current_price: Current price that triggered the alert
        """
        try:
            # Format the alert message
            formatted = NotificationFormatter.format_product_alert(product, current_price)
            
            # Create notification message
            message = NotificationMessage(
                title=formatted["title"],
                content=formatted["content"],
                level=NotificationLevel.INFO,
                timestamp=datetime.now(),
                metadata={
                    "product_name": product.nome,
                    "current_price": current_price,
                    "target_price": product.preco_alvo,
                    "url": product.url
                }
            )
            
            # Send through all enabled notifiers
            self._send_to_all_notifiers(message)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta de preço: {e}")
    
    def send_system_alert(self, message: str, level: str = "INFO") -> None:
        """Send a system alert notification.
        
        Args:
            message: System message to send
            level: Alert level (INFO, WARNING, ERROR, etc.)
        """
        try:
            # Convert string level to enum
            notification_level = NotificationLevel(level.upper())
            
            # Format the system alert
            formatted = NotificationFormatter.format_system_alert(message, notification_level)
            
            # Create notification message
            notification = NotificationMessage(
                title=formatted["title"],
                content=formatted["content"],
                level=notification_level,
                timestamp=datetime.now(),
                metadata={"system_message": message}
            )
            
            # Send through all enabled notifiers
            self._send_to_all_notifiers(notification)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta de sistema: {e}")
    
    def _send_to_all_notifiers(self, message: NotificationMessage) -> None:
        """Send message to all enabled notifiers.
        
        Args:
            message: Message to send
        """
        sent_count = 0
        failed_count = 0
        
        for name, notifier in self.notifiers.items():
            if notifier.is_enabled():
                try:
                    success = notifier.send_notification(message)
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                        self.logger.warning(f"Falha ao enviar notificação via '{name}'")
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Erro ao enviar notificação via '{name}': {e}")
        
        self.logger.debug(f"Notificação enviada: {sent_count} sucessos, {failed_count} falhas")