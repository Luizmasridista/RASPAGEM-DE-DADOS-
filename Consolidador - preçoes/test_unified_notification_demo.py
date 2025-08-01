#!/usr/bin/env python3
"""
Demo script to test the unified NotificationService functionality.
"""
from datetime import datetime
from services.notification_service import (
    NotificationService, EmailNotifier, EmailConfig
)
from models.data_models import ProductConfig


def test_unified_notification_service():
    """Test the unified notification service with multiple notifiers."""
    print("=== Testando NotificationService Unificado ===\n")
    
    # Create notification service (already has console notifier by default)
    service = NotificationService()
    
    # Create test product
    test_product = ProductConfig(
        nome="Smartphone Samsung Galaxy S24",
        url="https://example.com/samsung-s24",
        preco_alvo=2500.0
    )
    
    print("1. Testando alerta de preço apenas com console...")
    service.send_price_alert(test_product, 2200.0)
    
    print("\n2. Testando alerta de sistema...")
    service.send_system_alert("Sistema de monitoramento iniciado com sucesso", "INFO")
    
    print("\n3. Testando diferentes níveis de alerta...")
    service.send_system_alert("Aviso: Taxa de falhas aumentou", "WARNING")
    service.send_system_alert("Erro: Falha ao conectar com o banco de dados", "ERROR")
    
    # Test with email notifier (but don't actually send emails)
    print("\n4. Testando com notificador de email (simulado)...")
    try:
        email_config = EmailConfig(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="test@example.com",
            password="fake_password",
            from_email="test@example.com",
            to_emails=["recipient@example.com"]
        )
        
        email_notifier = EmailNotifier(email_config, enabled=False)  # Disabled to avoid actual sending
        service.add_notifier("email", email_notifier)
        
        print("   - Email notifier adicionado (desabilitado para teste)")
        print(f"   - Total de notificadores: {len(service.notifiers)}")
        
        # Test with email notifier disabled
        service.send_price_alert(test_product, 2100.0)
        
    except Exception as e:
        print(f"   - Erro ao configurar email notifier: {e}")
    
    print("\n5. Testando gerenciamento de notificadores...")
    
    # List all notifiers
    print(f"   - Notificadores ativos: {list(service.notifiers.keys())}")
    
    # Test getting notifier
    console_notifier = service.get_notifier("console")
    if console_notifier:
        print(f"   - Console notifier encontrado: {console_notifier.__class__.__name__}")
        print(f"   - Console notifier habilitado: {console_notifier.is_enabled()}")
    
    # Test disabling and enabling
    if console_notifier:
        console_notifier.disable()
        print("   - Console notifier desabilitado")
        
        service.send_system_alert("Esta mensagem não deve aparecer no console", "INFO")
        
        console_notifier.enable()
        print("   - Console notifier reabilitado")
        
        service.send_system_alert("Esta mensagem deve aparecer no console", "INFO")
    
    print("\n6. Testando remoção de notificadores...")
    if "email" in service.notifiers:
        removed = service.remove_notifier("email")
        print(f"   - Email notifier removido: {removed}")
        print(f"   - Notificadores restantes: {list(service.notifiers.keys())}")
    
    # Test removing non-existent notifier
    removed = service.remove_notifier("nonexistent")
    print(f"   - Tentativa de remover notificador inexistente: {removed}")
    
    print("\n=== Teste do NotificationService Unificado Concluído ===")


if __name__ == "__main__":
    test_unified_notification_service()