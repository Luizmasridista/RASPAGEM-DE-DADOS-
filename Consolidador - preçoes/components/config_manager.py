"""
Configuration management for the price monitoring system.
"""
import json
import os
import logging
from typing import List, Dict, Any
from pathlib import Path

from models.data_models import ProductConfig, SystemConfig
from models.interfaces import ConfigManagerInterface


logger = logging.getLogger(__name__)


class ConfigManager(ConfigManagerInterface):
    """Manages configuration loading, saving, and validation."""
    
    def __init__(self, products_config_path: str = "produtos.json", 
                 system_config_path: str = "config.json"):
        """Initialize ConfigManager with configuration file paths."""
        self.products_config_path = Path(products_config_path)
        self.system_config_path = Path(system_config_path)
        
        # Ensure config files exist
        self._ensure_config_files_exist()
    
    def load_products_config(self) -> List[ProductConfig]:
        """Load product configurations from JSON file."""
        try:
            logger.info(f"Loading products configuration from {self.products_config_path}")
            
            if not self.products_config_path.exists():
                logger.warning("Products config file not found, creating default")
                self._create_default_products_config()
                return []
            
            with open(self.products_config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = []
            errors = []
            
            if not isinstance(data, dict) or 'produtos' not in data:
                raise ValueError("Arquivo de configuração deve conter uma chave 'produtos'")
            
            for i, product_data in enumerate(data['produtos']):
                try:
                    # Validate required fields
                    if not isinstance(product_data, dict):
                        errors.append(f"Produto {i+1}: deve ser um objeto")
                        continue
                    
                    # Create ProductConfig with validation
                    product = ProductConfig(**product_data)
                    products.append(product)
                    logger.debug(f"Loaded product: {product.nome}")
                    
                except (TypeError, ValueError) as e:
                    error_msg = f"Produto {i+1} ({product_data.get('nome', 'sem nome')}): {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            if errors:
                logger.warning(f"Loaded {len(products)} products with {len(errors)} errors")
                for error in errors:
                    logger.warning(f"Configuration error: {error}")
            else:
                logger.info(f"Successfully loaded {len(products)} products")
            
            return products
            
        except json.JSONDecodeError as e:
            error_msg = f"Erro ao decodificar JSON do arquivo {self.products_config_path}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Erro ao carregar configuração de produtos: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def save_products_config(self, products: List[ProductConfig]) -> None:
        """Save product configurations to JSON file."""
        try:
            logger.info(f"Saving {len(products)} products to {self.products_config_path}")
            
            # Validate all products before saving
            for i, product in enumerate(products):
                try:
                    product.validate()
                except ValueError as e:
                    raise ValueError(f"Produto {i+1} ({product.nome}): {str(e)}")
            
            # Convert to dict format
            data = {
                "produtos": [
                    {
                        "nome": p.nome,
                        "url": p.url,
                        "preco_alvo": p.preco_alvo,
                        "ativo": p.ativo,
                        "seletores_personalizados": p.seletores_personalizados,
                        "intervalo_minimo": p.intervalo_minimo
                    }
                    for p in products
                ]
            }
            
            # Create backup if file exists
            if self.products_config_path.exists():
                backup_path = self.products_config_path.with_suffix('.json.backup')
                self.products_config_path.rename(backup_path)
                logger.debug(f"Created backup at {backup_path}")
            
            # Save to file
            with open(self.products_config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved products configuration")
            
        except Exception as e:
            error_msg = f"Erro ao salvar configuração de produtos: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def get_system_config(self) -> SystemConfig:
        """Get system configuration from file or defaults."""
        try:
            logger.debug(f"Loading system configuration from {self.system_config_path}")
            
            if not self.system_config_path.exists():
                logger.info("System config file not found, using defaults")
                return SystemConfig()
            
            with open(self.system_config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create SystemConfig with loaded data
            config = SystemConfig(**data)
            logger.info("Successfully loaded system configuration")
            return config
            
        except json.JSONDecodeError as e:
            error_msg = f"Erro ao decodificar JSON do arquivo {self.system_config_path}: {str(e)}"
            logger.error(error_msg)
            logger.info("Using default system configuration")
            return SystemConfig()
        except (TypeError, ValueError) as e:
            error_msg = f"Erro na configuração do sistema: {str(e)}"
            logger.error(error_msg)
            logger.info("Using default system configuration")
            return SystemConfig()
        except Exception as e:
            error_msg = f"Erro ao carregar configuração do sistema: {str(e)}"
            logger.error(error_msg)
            logger.info("Using default system configuration")
            return SystemConfig()
    
    def save_system_config(self, config: SystemConfig) -> None:
        """Save system configuration to JSON file."""
        try:
            logger.info(f"Saving system configuration to {self.system_config_path}")
            
            # Validate configuration
            config.validate()
            
            # Convert to dict
            data = {
                "intervalo_execucao": config.intervalo_execucao,
                "timeout_requisicao": config.timeout_requisicao,
                "max_retries": config.max_retries,
                "log_level": config.log_level,
                "email_enabled": config.email_enabled,
                "smtp_server": config.smtp_server,
                "smtp_port": config.smtp_port,
                "smtp_username": config.smtp_username,
                "smtp_password": config.smtp_password,
                "db_path": config.db_path
            }
            
            # Create backup if file exists
            if self.system_config_path.exists():
                backup_path = self.system_config_path.with_suffix('.json.backup')
                self.system_config_path.rename(backup_path)
                logger.debug(f"Created backup at {backup_path}")
            
            # Save to file
            with open(self.system_config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info("Successfully saved system configuration")
            
        except Exception as e:
            error_msg = f"Erro ao salvar configuração do sistema: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def validate_product_config(self, product: ProductConfig) -> bool:
        """Validate a product configuration."""
        try:
            product.validate()
            return True
        except ValueError as e:
            logger.error(f"Product validation failed: {str(e)}")
            return False
    
    def _ensure_config_files_exist(self) -> None:
        """Ensure configuration files exist, create defaults if not."""
        if not self.products_config_path.exists():
            self._create_default_products_config()
        
        if not self.system_config_path.exists():
            self._create_default_system_config()
    
    def _create_default_products_config(self) -> None:
        """Create default products configuration file."""
        try:
            logger.info(f"Creating default products configuration at {self.products_config_path}")
            
            default_config = {
                "produtos": [
                    {
                        "nome": "Exemplo - Smartphone",
                        "url": "https://example.com/smartphone",
                        "preco_alvo": 500.0,
                        "ativo": False,
                        "seletores_personalizados": None,
                        "intervalo_minimo": 3600
                    }
                ]
            }
            
            # Ensure directory exists
            self.products_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.products_config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            logger.info("Default products configuration created")
            
        except Exception as e:
            logger.error(f"Failed to create default products config: {str(e)}")
    
    def _create_default_system_config(self) -> None:
        """Create default system configuration file."""
        try:
            logger.info(f"Creating default system configuration at {self.system_config_path}")
            
            default_config = SystemConfig()
            self.save_system_config(default_config)
            
            logger.info("Default system configuration created")
            
        except Exception as e:
            logger.error(f"Failed to create default system config: {str(e)}")