#!/usr/bin/env python3
"""
Demo script to test the notification service functionality.
"""
from services.notification_service import NotificationService
from models.data_models import ProductConfig

def main():
    """Test the notification service with sample data."""
    print("=== Testando Serviço de Notificações ===\n")
    
    # Create notification service
    service = NotificationService()
    
    # Test system alert
    print("1. Testando alerta de sistema:")
    service.send_system_alert("Sistema de monitoramento iniciado com sucesso", "INFO")
    
    print("\n" + "="*60 + "\n")
    
    # Test price alert
    print("2. Testando alerta de preço:")
    product = ProductConfig(
        nome="Smartphone Samsung Galaxy S24",
        url="https://example.com/samsung-s24",
        preco_alvo=2500.00
    )
    
    current_price = 2199.99
    service.send_price_alert(product, current_price)
    
    print("\n" + "="*60 + "\n")
    
    # Test warning alert
    print("3. Testando alerta de warning:")
    service.send_system_alert("Taxa de falhas de scraping acima de 10%", "WARNING")
    
    print("\n" + "="*60 + "\n")
    
    # Test error alert
    print("4. Testando alerta de erro:")
    service.send_system_alert("Falha ao conectar com o banco de dados", "ERROR")
    
    print("\n=== Teste concluído ===")

if __name__ == "__main__":
    main()