import pandas as pd
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional
from models.consolidation_model import FileInfo

class FileService:
    """Serviço para manipulação de arquivos"""

    UPLOAD_ROOT = os.path.join(os.getcwd(), "uploads")
    PASTA_MESTRES = os.path.join(os.getcwd(), "ARQUIVO_MESTRE")
    PASTA_SUBORDINADAS = os.path.join(os.getcwd(), "ARQUIVOS_SUBORDINADOS")

    @staticmethod
    def ensure_upload_dirs():
        """Garante que as pastas de upload existem"""
        os.makedirs(FileService.PASTA_MESTRES, exist_ok=True)
        os.makedirs(FileService.PASTA_SUBORDINADAS, exist_ok=True)

    @staticmethod
    def save_uploaded_file(orig_path: str, tipo: str) -> str:
        """Salva o arquivo enviado na pasta correta ('mestre' ou 'subordinado') e retorna o novo caminho"""
        FileService.ensure_upload_dirs()
        if tipo == 'mestre':
            dest_dir = FileService.PASTA_MESTRES
        elif tipo == 'subordinado':
            dest_dir = FileService.PASTA_SUBORDINADAS
        else:
            raise ValueError("Tipo de arquivo deve ser 'mestre' ou 'subordinado'")
        filename = os.path.basename(orig_path)
        dest_path = os.path.join(dest_dir, filename)
        import shutil
        shutil.copy2(orig_path, dest_path)
        return dest_path
    
    @staticmethod
    def validate_excel_file(file_path: str) -> bool:
        """Valida se o arquivo é um Excel válido"""
        try:
            pd.read_excel(file_path, nrows=0)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Optional[FileInfo]:
        """Obtém informações detalhadas do arquivo"""
        try:
            if not os.path.exists(file_path):
                return None
            
            # Lê o arquivo para obter informações
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # Lê a primeira planilha para obter dimensões
            df = pd.read_excel(file_path, sheet_name=sheet_names[0])
            
            file_stats = os.stat(file_path)
            
            return FileInfo(
                name=os.path.basename(file_path),
                path=file_path,
                size=file_stats.st_size,
                upload_time=datetime.fromtimestamp(file_stats.st_mtime, tz=ZoneInfo('UTC')),
                sheet_names=sheet_names,
                rows_count=len(df),
                columns_count=len(df.columns)
            )
        except Exception as e:
            print(f"Erro ao obter informações do arquivo: {e}")
            return None
    
    @staticmethod
    def read_excel_data(file_path: str, sheet_name: str = None) -> Optional[pd.DataFrame]:
        """Lê dados de um arquivo Excel"""
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            print(f"Erro ao ler arquivo Excel: {e}")
            return None
    
    @staticmethod
    def create_backup(file_path: str, backup_dir: str = "backups") -> str:
        """Cria backup do arquivo com timestamp"""
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now(tz=ZoneInfo('UTC')).strftime("%Y%m%d_%H%M")
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            backup_filename = f"Backup_Consolidado_{timestamp}{ext}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copia o arquivo
            import shutil
            shutil.copy2(file_path, backup_path)
            
            return backup_path
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
            return ""
    
    @staticmethod
    def save_excel_data(df: pd.DataFrame, file_path: str, sheet_name: str = "Sheet1") -> bool:
        """Salva DataFrame em arquivo Excel"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo Excel: {e}")
            return False

    @staticmethod
    def move_to_subordinate_folder(file_path: str) -> str:
        """Move um arquivo para a pasta de arquivos subordinados"""
        try:
            destination = os.path.join(FileService.PASTA_SUBORDINADAS, os.path.basename(file_path))
            if not os.path.exists(destination):
                import shutil
                shutil.copy2(file_path, destination)
                return destination
            return file_path
        except Exception as e:
            print(f"Erro ao mover arquivo para subordinados: {e}")
            return ""