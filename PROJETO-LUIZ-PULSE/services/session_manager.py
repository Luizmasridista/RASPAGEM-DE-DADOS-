from typing import List, Optional, Callable
from models.consolidation_model import ConsolidationConfig, FileInfo, ConsolidationResult
from services.consolidation_service import ConsolidationService

class SessionManager:
    """Gerenciador de sessão da aplicação"""
    
    def __init__(self):
        self.consolidation_service = ConsolidationService()
        self.master_file: Optional[FileInfo] = None
        self.subordinate_files: List[FileInfo] = []
        self.config: Optional[ConsolidationConfig] = None
        self.current_step = 1
        self.max_steps = 5
    
    def set_master_file(self, file_info: FileInfo):
        """Define o arquivo mestre"""
        self.master_file = file_info
    
    def add_subordinate_file(self, file_info: FileInfo):
        """Adiciona arquivo subordinado"""
        if file_info not in self.subordinate_files:
            self.subordinate_files.append(file_info)
    
    def remove_subordinate_file(self, file_path: str):
        """Remove arquivo subordinado"""
        self.subordinate_files = [f for f in self.subordinate_files if f.path != file_path]
    
    def set_consolidation_config(self, config: ConsolidationConfig):
        """Define a configuração da consolidação"""
        self.config = config
    
    def get_current_step(self) -> int:
        """Retorna o passo atual"""
        return self.current_step
    
    def set_current_step(self, step: int):
        """Define o passo atual"""
        if 1 <= step <= self.max_steps:
            self.current_step = step
    
    def next_step(self):
        """Avança para o próximo passo"""
        if self.current_step < self.max_steps:
            self.current_step += 1
    
    def previous_step(self):
        """Volta para o passo anterior"""
        if self.current_step > 1:
            self.current_step -= 1
    
    def can_proceed_to_step(self, step: int) -> bool:
        """Verifica se pode prosseguir para um passo específico"""
        if step == 1:
            return True
        elif step == 2:
            return self.master_file is not None
        elif step == 3:
            return self.master_file is not None and len(self.subordinate_files) > 0
        elif step == 4:
            return (self.master_file is not None and 
                   len(self.subordinate_files) > 0 and 
                   self.config is not None)
        elif step == 5:
            return (self.master_file is not None and 
                   len(self.subordinate_files) > 0 and 
                   self.config is not None)
        return False
    
    def start_consolidation(self, progress_callback: Callable[[int, str, float], None] = None) -> ConsolidationResult:
        """Inicia o processo de consolidação"""
        if not self.config or not self.master_file or not self.subordinate_files:
            return ConsolidationResult(
                success=False,
                total_files_processed=0,
                total_rows_added=0,
                backup_path=None,
                execution_time=0.0,
                errors=["Configuração incompleta"],
                steps=[]
            )
        
        return self.consolidation_service.consolidate_data(
            self.config,
            self.subordinate_files,
            progress_callback
        )
    
    def get_session_summary(self) -> dict:
        """Retorna resumo da sessão atual"""
        return {
            "master_file": self.master_file.name if self.master_file else None,
            "subordinate_files_count": len(self.subordinate_files),
            "subordinate_files": [f.name for f in self.subordinate_files],
            "current_step": self.current_step,
            "config_set": self.config is not None,
            "ready_for_consolidation": self.can_proceed_to_step(4)
        }
    
    def reset_session(self):
        """Reseta a sessão"""
        self.master_file = None
        self.subordinate_files = []
        self.config = None
        self.current_step = 1