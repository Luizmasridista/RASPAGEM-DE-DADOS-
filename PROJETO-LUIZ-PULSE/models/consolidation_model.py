from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class FileInfo:
    """Informações sobre arquivo carregado"""
    name: str
    path: str
    size: int
    upload_time: datetime
    sheet_names: List[str]
    rows_count: int
    columns_count: int

@dataclass
class ConsolidationConfig:
    """Configuração da consolidação"""
    master_file_path: str
    master_sheet_name: str
    target_columns: List[str]
    merge_strategy: str  # 'append', 'replace', 'update'
    backup_enabled: bool = True
    
@dataclass
class ConsolidationStep:
    """Representa um passo da consolidação"""
    id: int
    name: str
    description: str
    status: str  # 'pending', 'running', 'completed', 'error'
    progress: float = 0.0
    error_message: Optional[str] = None

@dataclass
class ConsolidationResult:
    """Resultado da consolidação"""
    success: bool
    total_files_processed: int
    total_rows_added: int
    backup_path: Optional[str]
    execution_time: float
    errors: List[str]
    steps: List[ConsolidationStep]