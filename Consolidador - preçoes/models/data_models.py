"""
Core data models for the price monitoring system.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from abc import ABC, abstractmethod


@dataclass
class ProductConfig:
    """Configuration for a product to be monitored."""
    nome: str
    url: str
    preco_alvo: float
    ativo: bool = True
    seletores_personalizados: Optional[Dict[str, List[str]]] = None
    intervalo_minimo: int = 3600  # segundos entre coletas
    
    def __post_init__(self):
        """Validate product configuration after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """Validate product configuration integrity."""
        errors = []
        
        if not self.nome or not self.nome.strip():
            errors.append("Nome do produto não pode estar vazio")
        
        if not self.url or not self.url.strip():
            errors.append("URL do produto não pode estar vazia")
        elif not self.url.startswith(('http://', 'https://')):
            errors.append("URL deve começar com http:// ou https://")
        
        if self.preco_alvo <= 0:
            errors.append("Preço alvo deve ser maior que zero")
        
        if self.intervalo_minimo < 60:
            errors.append("Intervalo mínimo deve ser pelo menos 60 segundos")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return True


@dataclass
class SystemConfig:
    """System-wide configuration settings."""
    intervalo_execucao: int = 3600  # segundos
    timeout_requisicao: int = 10
    max_retries: int = 3
    log_level: str = "INFO"
    email_enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    db_path: str = "precos.db"
    
    def __post_init__(self):
        """Validate system configuration after initialization."""
        self.validate()
    
    def validate(self) -> bool:
        """Validate system configuration integrity."""
        errors = []
        
        if self.intervalo_execucao < 60:
            errors.append("Intervalo de execução deve ser pelo menos 60 segundos")
        
        if self.timeout_requisicao <= 0:
            errors.append("Timeout deve ser maior que zero")
        
        if self.max_retries < 0:
            errors.append("Max retries não pode ser negativo")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append("Log level deve ser um dos: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        
        if self.email_enabled:
            if not self.smtp_server or not self.smtp_server.strip():
                errors.append("SMTP server é obrigatório quando email está habilitado")
            if self.smtp_port <= 0 or self.smtp_port > 65535:
                errors.append("SMTP port deve estar entre 1 e 65535")
        
        if not self.db_path or not self.db_path.strip():
            errors.append("Caminho do banco de dados não pode estar vazio")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return True


@dataclass
class PriceRecord:
    """Record of a price check for a product."""
    nome_produto: str
    url: str
    preco: float
    preco_alvo: float
    data_hora: datetime
    status: str = "active"
    erro: Optional[str] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validate price record after initialization."""
        if not self.nome_produto or not self.nome_produto.strip():
            raise ValueError("Nome do produto não pode estar vazio")
        if not self.url or not self.url.strip():
            raise ValueError("URL não pode estar vazia")
        if self.preco < 0:
            raise ValueError("Preço não pode ser negativo")
        if self.preco_alvo <= 0:
            raise ValueError("Preço alvo deve ser maior que zero")


@dataclass
class ProductData:
    """Data extracted from a product page."""
    nome: str
    preco: float
    url: str
    data_coleta: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate product data after initialization."""
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome do produto não pode estar vazio")
        if self.preco < 0:
            raise ValueError("Preço não pode ser negativo")


@dataclass
class ProductResult:
    """Result of monitoring a single product."""
    produto: ProductConfig
    sucesso: bool
    preco_atual: Optional[float] = None
    alerta_enviado: bool = False
    erro: Optional[str] = None
    tempo_execucao: float = 0.0


@dataclass
class MonitoringResult:
    """Result of a complete monitoring execution."""
    total_products: int
    successful_scrapes: int
    failed_scrapes: int
    alerts_sent: int
    execution_time: float
    errors: List[str] = field(default_factory=list)
    results: List[ProductResult] = field(default_factory=list)