"""
Unit tests for ConfigManager class.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

from components.config_manager import ConfigManager
from models.data_models import ProductConfig, SystemConfig


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.products_config_path = Path(self.temp_dir) / "produtos.json"
        self.system_config_path = Path(self.temp_dir) / "config.json"
        
        # Create ConfigManager with temporary paths
        with patch.object(ConfigManager, '_ensure_config_files_exist'):
            self.config_manager = ConfigManager(
                str(self.products_config_path),
                str(self.system_config_path)
            )
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        if self.products_config_path.exists():
            self.products_config_path.unlink()
        if self.system_config_path.exists():
            self.system_config_path.unlink()
        os.rmdir(self.temp_dir)
    
    def test_load_products_config_success(self):
        """Test successful loading of products configuration."""
        # Create test data
        test_data = {
            "produtos": [
                {
                    "nome": "Produto Teste",
                    "url": "https://example.com/produto",
                    "preco_alvo": 100.0,
                    "ativo": True,
                    "seletores_personalizados": None,
                    "intervalo_minimo": 3600
                }
            ]
        }
        
        # Write test data to file
        with open(self.products_config_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Load configuration
        products = self.config_manager.load_products_config()
        
        # Assertions
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].nome, "Produto Teste")
        self.assertEqual(products[0].url, "https://example.com/produto")
        self.assertEqual(products[0].preco_alvo, 100.0)
        self.assertTrue(products[0].ativo)
    
    def test_load_products_config_file_not_found(self):
        """Test loading when products config file doesn't exist."""
        # Ensure file doesn't exist
        if self.products_config_path.exists():
            self.products_config_path.unlink()
        
        with patch.object(self.config_manager, '_create_default_products_config'):
            products = self.config_manager.load_products_config()
            self.assertEqual(len(products), 0)
    
    def test_load_products_config_invalid_json(self):
        """Test loading with invalid JSON."""
        # Write invalid JSON
        with open(self.products_config_path, 'w') as f:
            f.write("invalid json content")
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.config_manager.load_products_config()
        
        self.assertIn("Erro ao decodificar JSON", str(context.exception))
    
    def test_load_products_config_missing_produtos_key(self):
        """Test loading with missing 'produtos' key."""
        # Write data without 'produtos' key
        test_data = {"other_key": "value"}
        with open(self.products_config_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.config_manager.load_products_config()
        
        self.assertIn("deve conter uma chave 'produtos'", str(context.exception))
    
    def test_load_products_config_invalid_product_data(self):
        """Test loading with invalid product data."""
        # Create test data with invalid product
        test_data = {
            "produtos": [
                {
                    "nome": "Produto Válido",
                    "url": "https://example.com/produto",
                    "preco_alvo": 100.0
                },
                {
                    "nome": "",  # Invalid: empty name
                    "url": "https://example.com/produto2",
                    "preco_alvo": 50.0
                }
            ]
        }
        
        with open(self.products_config_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Should load valid products and skip invalid ones
        products = self.config_manager.load_products_config()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].nome, "Produto Válido")
    
    def test_save_products_config_success(self):
        """Test successful saving of products configuration."""
        # Create test products
        products = [
            ProductConfig(
                nome="Produto 1",
                url="https://example.com/produto1",
                preco_alvo=100.0
            ),
            ProductConfig(
                nome="Produto 2",
                url="https://example.com/produto2",
                preco_alvo=200.0,
                ativo=False
            )
        ]
        
        # Save configuration
        self.config_manager.save_products_config(products)
        
        # Verify file was created and contains correct data
        self.assertTrue(self.products_config_path.exists())
        
        with open(self.products_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn('produtos', data)
        self.assertEqual(len(data['produtos']), 2)
        self.assertEqual(data['produtos'][0]['nome'], "Produto 1")
        self.assertEqual(data['produtos'][1]['ativo'], False)
    
    def test_save_products_config_invalid_product(self):
        """Test saving with invalid product data."""
        # Create invalid product (this should fail during validation)
        with self.assertRaises(ValueError):
            invalid_product = ProductConfig(
                nome="",  # Invalid: empty name
                url="https://example.com/produto",
                preco_alvo=100.0
            )
    
    def test_get_system_config_default(self):
        """Test getting system configuration with defaults."""
        # Ensure file doesn't exist
        if self.system_config_path.exists():
            self.system_config_path.unlink()
        
        config = self.config_manager.get_system_config()
        
        # Should return default SystemConfig
        self.assertIsInstance(config, SystemConfig)
        self.assertEqual(config.intervalo_execucao, 3600)
        self.assertEqual(config.timeout_requisicao, 10)
        self.assertEqual(config.log_level, "INFO")
    
    def test_get_system_config_from_file(self):
        """Test getting system configuration from file."""
        # Create test system config
        test_config = {
            "intervalo_execucao": 1800,
            "timeout_requisicao": 15,
            "max_retries": 5,
            "log_level": "DEBUG",
            "email_enabled": True,
            "smtp_server": "smtp.test.com",
            "smtp_port": 587,
            "smtp_username": "test@test.com",
            "smtp_password": "password",
            "db_path": "test.db"
        }
        
        with open(self.system_config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        config = self.config_manager.get_system_config()
        
        self.assertEqual(config.intervalo_execucao, 1800)
        self.assertEqual(config.timeout_requisicao, 15)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertTrue(config.email_enabled)
    
    def test_get_system_config_invalid_json(self):
        """Test getting system config with invalid JSON."""
        # Write invalid JSON
        with open(self.system_config_path, 'w') as f:
            f.write("invalid json")
        
        # Should return default config
        config = self.config_manager.get_system_config()
        self.assertIsInstance(config, SystemConfig)
        self.assertEqual(config.intervalo_execucao, 3600)  # default value
    
    def test_save_system_config_success(self):
        """Test successful saving of system configuration."""
        # Create test config
        config = SystemConfig(
            intervalo_execucao=1800,
            timeout_requisicao=15,
            log_level="DEBUG",
            email_enabled=True,
            smtp_server="smtp.test.com"
        )
        
        # Save configuration
        self.config_manager.save_system_config(config)
        
        # Verify file was created and contains correct data
        self.assertTrue(self.system_config_path.exists())
        
        with open(self.system_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['intervalo_execucao'], 1800)
        self.assertEqual(data['log_level'], "DEBUG")
        self.assertTrue(data['email_enabled'])
    
    def test_validate_product_config_valid(self):
        """Test validation of valid product configuration."""
        product = ProductConfig(
            nome="Produto Teste",
            url="https://example.com/produto",
            preco_alvo=100.0
        )
        
        result = self.config_manager.validate_product_config(product)
        self.assertTrue(result)
    
    def test_validate_product_config_invalid(self):
        """Test validation of invalid product configuration."""
        # Create product with invalid data
        product = ProductConfig(
            nome="Produto Teste",
            url="https://example.com/produto",
            preco_alvo=100.0
        )
        
        # Manually set invalid data to bypass __post_init__ validation
        product.preco_alvo = -10.0  # Invalid price
        
        result = self.config_manager.validate_product_config(product)
        self.assertFalse(result)
    
    def test_create_default_products_config(self):
        """Test creation of default products configuration."""
        # Ensure file doesn't exist
        if self.products_config_path.exists():
            self.products_config_path.unlink()
        
        # Create default config
        self.config_manager._create_default_products_config()
        
        # Verify file was created
        self.assertTrue(self.products_config_path.exists())
        
        # Verify content
        with open(self.products_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn('produtos', data)
        self.assertEqual(len(data['produtos']), 1)
        self.assertEqual(data['produtos'][0]['nome'], "Exemplo - Smartphone")
    
    def test_create_default_system_config(self):
        """Test creation of default system configuration."""
        # Ensure file doesn't exist
        if self.system_config_path.exists():
            self.system_config_path.unlink()
        
        # Create default config
        self.config_manager._create_default_system_config()
        
        # Verify file was created
        self.assertTrue(self.system_config_path.exists())
        
        # Verify content
        with open(self.system_config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['intervalo_execucao'], 3600)
        self.assertEqual(data['log_level'], "INFO")


if __name__ == '__main__':
    unittest.main()