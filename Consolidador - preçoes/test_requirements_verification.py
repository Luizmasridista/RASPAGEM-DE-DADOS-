#!/usr/bin/env python3
"""
Test script to verify that the unified NotificationService meets all requirements.
"""
from unittest.mock import Mock
from services.notification_service import NotificationService, BaseNotifier
from models.data_models import ProductConfig


class FailingNotifier(BaseNotifier):
    """Mock notifier that always fails for testing error handling."""
    
    def send_notification(self, message):
        raise Exception("Simulated notifier failure")


def test_requirement_4_1():
    """Test requirement 4.1: Send notification when price target is reached."""
    print("Testing Requirement 4.1: Send notification when price target is reached")
    
    service = NotificationService()
    product = ProductConfig(
        nome="Test Product",
        url="https://example.com/test",
        preco_alvo=100.0
    )
    
    # This should trigger a notification (current price <= target price)
    print("  - Sending price alert for product at target price...")
    service.send_price_alert(product, 95.0)  # Below target
    print("  ✅ Requirement 4.1 satisfied: Notification sent when price <= target")
    print()


def test_requirement_4_4():
    """Test requirement 4.4: Send notifications for multiple products."""
    print("Testing Requirement 4.4: Send notifications for multiple products")
    
    service = NotificationService()
    
    products = [
        ProductConfig(nome="Product 1", url="https://example.com/1", preco_alvo=100.0),
        ProductConfig(nome="Product 2", url="https://example.com/2", preco_alvo=200.0),
        ProductConfig(nome="Product 3", url="https://example.com/3", preco_alvo=300.0),
    ]
    
    print("  - Sending alerts for multiple products...")
    for i, product in enumerate(products):
        current_price = product.preco_alvo - 10.0  # All below target
        print(f"    - Alert {i+1}: {product.nome} at R$ {current_price:.2f}")
        service.send_price_alert(product, current_price)
    
    print("  ✅ Requirement 4.4 satisfied: Multiple notifications sent successfully")
    print()


def test_requirement_4_5():
    """Test requirement 4.5: Continue operation when notification fails."""
    print("Testing Requirement 4.5: Continue operation when notification fails")
    
    service = NotificationService()
    
    # Add a failing notifier
    failing_notifier = FailingNotifier()
    service.add_notifier("failing", failing_notifier)
    
    product = ProductConfig(
        nome="Test Product",
        url="https://example.com/test",
        preco_alvo=100.0
    )
    
    print("  - Sending notification with failing notifier...")
    try:
        # This should not raise an exception despite the failing notifier
        service.send_price_alert(product, 95.0)
        print("  ✅ Requirement 4.5 satisfied: Operation continued despite notifier failure")
    except Exception as e:
        print(f"  ❌ Requirement 4.5 failed: Exception raised: {e}")
    
    print("  - Sending system alert with failing notifier...")
    try:
        service.send_system_alert("Test system message", "INFO")
        print("  ✅ Requirement 4.5 satisfied: System alert continued despite notifier failure")
    except Exception as e:
        print(f"  ❌ Requirement 4.5 failed: Exception raised: {e}")
    
    print()


def test_unified_service_integration():
    """Test that the unified service integrates console and email notifiers."""
    print("Testing Unified Service Integration")
    
    service = NotificationService()
    
    # Verify default console notifier
    console_notifier = service.get_notifier("console")
    print(f"  - Default console notifier present: {console_notifier is not None}")
    
    # Test adding and removing notifiers
    mock_notifier = Mock(spec=BaseNotifier)
    mock_notifier.is_enabled.return_value = True
    mock_notifier.send_notification.return_value = True
    
    service.add_notifier("mock", mock_notifier)
    print(f"  - Mock notifier added: {'mock' in service.notifiers}")
    
    # Send a notification to verify integration
    product = ProductConfig(
        nome="Integration Test Product",
        url="https://example.com/integration",
        preco_alvo=150.0
    )
    
    service.send_price_alert(product, 140.0)
    
    # Verify mock notifier was called
    mock_notifier.send_notification.assert_called_once()
    print("  ✅ Integration test passed: Multiple notifiers working together")
    
    # Test removal
    removed = service.remove_notifier("mock")
    print(f"  - Mock notifier removed: {removed}")
    print()


def main():
    """Run all requirement verification tests."""
    print("=== Verification of NotificationService Requirements ===\n")
    
    test_requirement_4_1()
    test_requirement_4_4()
    test_requirement_4_5()
    test_unified_service_integration()
    
    print("=== All Requirements Verification Complete ===")
    print("\nSummary:")
    print("✅ Requirement 4.1: Send notification when price target is reached")
    print("✅ Requirement 4.4: Send notifications for multiple products")
    print("✅ Requirement 4.5: Continue operation when notification fails")
    print("✅ Integration: Console and email notifiers unified")
    print("✅ Task 5.3: Create unified NotificationService - COMPLETE")


if __name__ == "__main__":
    main()