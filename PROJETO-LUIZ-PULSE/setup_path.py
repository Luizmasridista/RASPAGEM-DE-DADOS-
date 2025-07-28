"""
Módulo para configurar o sys.path do projeto
Garante que as importações funcionem corretamente em qualquer ambiente
"""
import os
import sys

def setup_project_path():
    """Configura o sys.path para incluir o diretório raiz do projeto"""
    # Obtém o diretório onde este arquivo está localizado (raiz do projeto)
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Adiciona o diretório raiz ao sys.path se não estiver presente
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    return project_root

# Executa automaticamente quando o módulo é importado
setup_project_path()
