#!/usr/bin/env python3
"""
Script para testar a consolidação corrigida
"""

import sys
sys.path.append('.')

from backend.consolidador import consolidar_planilhas
import pandas as pd
import os

def testar_consolidacao():
    print("=== TESTANDO CONSOLIDAÇÃO CORRIGIDA ===")
    
    # Executar consolidação
    sucesso, resultado = consolidar_planilhas()
    
    print(f"Sucesso: {sucesso}")
    
    if sucesso:
        print(f"Total de registros: {resultado.get('total_registros', 0)}")
        print(f"Planilhas processadas: {resultado.get('planilhas_processadas', [])}")
        print(f"Backup criado: {resultado.get('backup_criado', False)}")
        print(f"Tamanho do arquivo: {resultado.get('tamanho_arquivo_bytes', 0)} bytes")
        
        # Verificar as colunas da planilha mestre
        colunas = resultado.get('colunas', [])
        print(f"\nColunas na planilha mestre ({len(colunas)} total):")
        for i, col in enumerate(colunas[:15]):  # Mostrar apenas as primeiras 15
            print(f"  {i+1}. {col}")
        if len(colunas) > 15:
            print(f"  ... e mais {len(colunas) - 15} colunas")
        
        # Verificar se a planilha foi criada
        planilha_path = resultado.get('caminho_arquivo', '')
        if os.path.exists(planilha_path):
            print(f"\n✓ Planilha mestre criada com sucesso: {planilha_path}")
            
            # Ler algumas linhas para verificar a estrutura
            try:
                df = pd.read_excel(planilha_path)
                print(f"\nPrimeiras 3 linhas da planilha consolidada:")
                print(df.head(3).to_string())
                
                # Verificar se há duplicação de cabeçalhos
                print(f"\nVerificando duplicação de cabeçalhos...")
                colunas_duplicadas = df.columns[df.columns.duplicated()].tolist()
                if colunas_duplicadas:
                    print(f"⚠️  Colunas duplicadas encontradas: {colunas_duplicadas}")
                else:
                    print("✓ Nenhuma coluna duplicada encontrada!")
                    
            except Exception as e:
                print(f"Erro ao ler planilha mestre: {e}")
        else:
            print(f"✗ Planilha mestre não foi criada: {planilha_path}")
    else:
        print(f"Erro na consolidação: {resultado}")

if __name__ == "__main__":
    testar_consolidacao()
