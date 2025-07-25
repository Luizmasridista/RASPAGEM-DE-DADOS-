#!/usr/bin/env python
"""
Script de teste para o sistema de consolidação de planilhas.
Este script testa as principais funcionalidades do sistema.
"""

import os
import sys
import pandas as pd
import requests
import time
import shutil
from datetime import datetime
import unittest

# Configurações
API_URL = "http://localhost:8000"
PLANILHAS_EXEMPLO_DIR = "planilhas_exemplo"

class TestSistemaConsolidacao(unittest.TestCase):
    """Classe de teste para o sistema de consolidação de planilhas."""
    
    @classmethod
    def setUpClass(cls):
        """Preparação para os testes."""
        print("\n🔍 Iniciando testes do sistema de consolidação...")
        
        # Verificar se a API está rodando
        try:
            response = requests.get(f"{API_URL}/status")
            if response.status_code != 200:
                print("❌ API não está rodando. Inicie o sistema com 'python start.py' antes de executar os testes.")
                sys.exit(1)
        except:
            print("❌ API não está rodando. Inicie o sistema com 'python start.py' antes de executar os testes.")
            sys.exit(1)
        
        # Criar diretórios necessários
        os.makedirs("planilhas_originais", exist_ok=True)
        os.makedirs("planilha_mestre", exist_ok=True)
        os.makedirs("backups", exist_ok=True)
        
        # Criar planilhas de exemplo se não existirem
        cls.criar_planilhas_exemplo()
    
    @classmethod
    def tearDownClass(cls):
        """Limpeza após os testes."""
        print("\n🧹 Limpando arquivos de teste...")
    
    @classmethod
    def criar_planilhas_exemplo(cls):
        """Cria planilhas de exemplo para teste."""
        print("📊 Criando planilhas de exemplo para teste...")
        
        # Criar diretório para planilhas de exemplo
        os.makedirs(PLANILHAS_EXEMPLO_DIR, exist_ok=True)
        
        # Dados de exemplo para cada estrutura
        estruturas = ["Estrutura_A", "Estrutura_B", "Estrutura_C", "Estrutura_D"]
        
        for i, estrutura in enumerate(estruturas):
            # Criar DataFrame com dados de exemplo
            dados = []
            
            # Adicionar 5 registros para cada estrutura
            for j in range(1, 6):
                dados.append({
                    "Colaborador": f"Colaborador {i+1}-{j}",
                    "Departamento": f"Departamento {(i % 3) + 1}",
                    "Treinamento": f"Treinamento {(j % 4) + 1}",
                    "Carga_Horaria": (j * 4) + (i * 2),
                    "Data_Inicio": datetime.now().strftime("%d/%m/%Y"),
                    "Data_Fim": datetime.now().strftime("%d/%m/%Y"),
                    "Status": ["Em Andamento", "Concluído", "Pendente"][j % 3]
                })
            
            # Criar DataFrame
            df = pd.DataFrame(dados)
            
            # Salvar planilha
            caminho_arquivo = os.path.join(PLANILHAS_EXEMPLO_DIR, f"{estrutura}.xlsx")
            df.to_excel(caminho_arquivo, index=False)
            
            print(f"  ✅ Planilha {estrutura}.xlsx criada")
        
        print("✅ Todas as planilhas de exemplo foram criadas")
    
    def copiar_planilhas_para_originais(self):
        """Copia as planilhas de exemplo para o diretório de planilhas originais."""
        print("📋 Copiando planilhas de exemplo para o diretório de processamento...")
        
        # Limpar diretório de planilhas originais
        for arquivo in os.listdir("planilhas_originais"):
            os.remove(os.path.join("planilhas_originais", arquivo))
        
        # Copiar planilhas de exemplo
        for arquivo in os.listdir(PLANILHAS_EXEMPLO_DIR):
            if arquivo.endswith(".xlsx"):
                shutil.copy2(
                    os.path.join(PLANILHAS_EXEMPLO_DIR, arquivo),
                    os.path.join("planilhas_originais", arquivo)
                )
                print(f"  ✅ Copiado: {arquivo}")
    
    def test_01_status_api(self):
        """Testa se a API está respondendo corretamente."""
        print("\n🧪 Teste 1: Verificando status da API...")
        
        response = requests.get(f"{API_URL}/status")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "online")
        
        print("✅ API está online e respondendo corretamente")
    
    def test_02_consolidacao(self):
        """Testa o processo de consolidação de planilhas."""
        print("\n🧪 Teste 2: Testando consolidação de planilhas...")
        
        # Copiar planilhas de exemplo para o diretório de processamento
        self.copiar_planilhas_para_originais()
        
        # Chamar API de consolidação
        response = requests.post(f"{API_URL}/consolidar")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["sucesso"])
        
        # Verificar se a planilha mestre foi criada
        response = requests.get(f"{API_URL}/download-mestre")
        self.assertEqual(response.status_code, 200)
        
        print("✅ Consolidação realizada com sucesso")
        
        # Verificar estatísticas
        if "dados" in data and data["dados"]:
            print(f"  📊 Total de registros: {data['dados']['total_registros']}")
            print(f"  📊 Estruturas processadas: {', '.join(data['dados']['estruturas_processadas'])}")
    
    def test_03_backups(self):
        """Testa a funcionalidade de backups."""
        print("\n🧪 Teste 3: Testando sistema de backups...")
        
        # Listar backups
        response = requests.get(f"{API_URL}/listar-backups")
        self.assertEqual(response.status_code, 200)
        
        backups = response.json()
        self.assertIsInstance(backups, list)
        
        # Deve haver pelo menos um backup após a consolidação
        self.assertGreater(len(backups), 0)
        
        print(f"✅ Sistema de backups funcionando. {len(backups)} backups encontrados.")
        
        # Verificar se é possível baixar o backup mais recente
        if backups:
            backup_mais_recente = backups[0]["nome"]
            response = requests.get(f"{API_URL}/download-backup/{backup_mais_recente}")
            self.assertEqual(response.status_code, 200)
            print(f"✅ Download de backup funcionando corretamente")

if __name__ == "__main__":
    unittest.main()