"""
Módulo responsável pela consolidação das planilhas de treinamento.
"""

import os
import shutil
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path

from backend.config import (
    PLANILHAS_ORIGINAIS_DIR,
    PLANILHA_MESTRE_DIR,
    BACKUPS_DIR,
    PLANILHA_MESTRE_PATH,
    TIMESTAMP_FORMAT,
    ESTRUTURAS,
    COLUNAS_OBRIGATORIAS
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("consolidacao.log")
    ]
)

logger = logging.getLogger("consolidador")

def validar_planilha(df, nome_planilha):
    """
    Valida se a planilha possui todas as colunas obrigatórias.
    """
    colunas_faltantes = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
    if colunas_faltantes:
        logger.warning(f"Planilha {nome_planilha} não possui as colunas obrigatórias: {', '.join(colunas_faltantes)}")
        # Permitir processamento parcial, mas registrar aviso
        return False, colunas_faltantes
    return True, []

def criar_backup_mestre():
    """
    Cria um backup da planilha mestre com timestamp.
    """
    if not os.path.exists(PLANILHA_MESTRE_PATH):
        logger.warning("Planilha mestre não encontrada para backup")
        return None
    
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    backup_filename = f"planilha_mestre_backup_{timestamp}.xlsx"
    backup_path = os.path.join(BACKUPS_DIR, backup_filename)
    
    # Garantir que o diretório de backup existe
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    
    # Copiar o arquivo mestre para o backup
    shutil.copy2(PLANILHA_MESTRE_PATH, backup_path)
    logger.info(f"Backup criado: {backup_filename}")
    
    return backup_path

def listar_backups():
    """
    Lista todos os backups disponíveis.
    """
    if not os.path.exists(BACKUPS_DIR):
        return []
    
    backups = []
    for arquivo in os.listdir(BACKUPS_DIR):
        if arquivo.startswith("planilha_mestre_backup_") and arquivo.endswith(".xlsx"):
            caminho_completo = os.path.join(BACKUPS_DIR, arquivo)
            data_modificacao = datetime.fromtimestamp(os.path.getmtime(caminho_completo))
            tamanho = os.path.getsize(caminho_completo)
            
            backups.append({
                "nome": arquivo,
                "caminho": caminho_completo,
                "data": data_modificacao.strftime("%d/%m/%Y %H:%M:%S"),
                "tamanho_kb": round(tamanho / 1024, 2)
            })
    
    # Ordenar por data de modificação (mais recente primeiro)
    backups.sort(key=lambda x: x["nome"], reverse=True)
    return backups

def processar_planilha_estruturada(caminho_planilha, nome_planilha, colunas_padrao=None):
    """
    Processa uma planilha com estrutura específica onde os cabeçalhos podem estar em linhas diferentes.
    Padroniza as colunas para evitar duplicação de cabeçalhos.
    """
    try:
        # Ler a planilha completa primeiro
        df_raw = pd.read_excel(caminho_planilha)
        logger.info(f"Processando {nome_planilha}: {df_raw.shape[0]} linhas, {df_raw.shape[1]} colunas")
        
        # Procurar pela linha que contém os cabeçalhos reais
        header_row = None
        for idx, row in df_raw.iterrows():
            # Verificar se a linha contém palavras-chave típicas de cabeçalho
            row_str = ' '.join([str(val).upper() for val in row.values if pd.notna(val)])
            if any(keyword in row_str for keyword in ['LÍDER', 'STATUS', 'DATA', 'INICIO', 'COLABORADOR', 'DEPARTAMENTO']):
                header_row = idx
                break
        
        if header_row is not None:
            # Usar a linha encontrada como cabeçalho
            df = pd.read_excel(caminho_planilha, header=header_row)
            # Remover linhas vazias
            df = df.dropna(how='all')
            
            # CORREÇÃO IMPORTANTE: Remover linhas que ainda contêm cabeçalhos como dados
            # Identificar e remover linhas que são na verdade cabeçalhos repetidos
            linhas_para_remover = []
            for idx, row in df.iterrows():
                # Verificar se a linha contém palavras típicas de cabeçalho
                row_str = ' '.join([str(val).upper() for val in row.values if pd.notna(val)])
                if any(keyword in row_str for keyword in ['LÍDER', 'STATUS', 'DATA ADM', 'INICIO', 'COLABORADOR']):
                    # Se mais de 50% dos valores são palavras de cabeçalho, remover a linha
                    palavras_cabecalho = sum(1 for val in row.values if pd.notna(val) and 
                                           any(kw in str(val).upper() for kw in ['LÍDER', 'STATUS', 'DATA', 'INICIO', 'COLABORADOR', 'DEPARTAMENTO', 'CANAL', 'TIPO', 'CAPACITY']))
                    total_valores = sum(1 for val in row.values if pd.notna(val))
                    if total_valores > 0 and palavras_cabecalho / total_valores > 0.4:
                        linhas_para_remover.append(idx)
                        logger.info(f"Removendo linha de cabeçalho duplicado: {idx}")
            
            # Remover as linhas identificadas como cabeçalhos
            if linhas_para_remover:
                df = df.drop(linhas_para_remover)
                df = df.reset_index(drop=True)
            
            logger.info(f"Cabeçalho encontrado na linha {header_row}. Dados processados: {len(df)} registros (após limpeza)")
        else:
            # Se não encontrar cabeçalho específico, tentar processar como está
            df = df_raw.copy()
            logger.warning(f"Cabeçalho não identificado em {nome_planilha}, processando como está")
        
        # Remover linhas completamente vazias
        df = df.dropna(how='all')
        
        if len(df) == 0:
            logger.warning(f"Planilha {nome_planilha} não possui dados válidos após processamento")
            return None
        
        # PADRONIZAR COLUNAS - Esta é a correção principal!
        if colunas_padrao is not None:
            # Criar um novo DataFrame com as colunas padronizadas
            df_padronizado = pd.DataFrame(columns=colunas_padrao)
            
            # Mapear as colunas existentes para as padronizadas
            mapeamento_colunas = {}
            colunas_originais = [str(col).strip().upper() for col in df.columns]
            
            # Tentar mapear automaticamente baseado em palavras-chave
            for i, col_original in enumerate(df.columns):
                col_str = str(col_original).strip().upper()
                
                # Mapeamento baseado em palavras-chave (CONFORME IMAGENS)
                if any(keyword in col_str for keyword in ['LÍDER', 'LIDER']):
                    mapeamento_colunas['LÍDER'] = col_original
                elif any(keyword in col_str for keyword in ['STATUS']):
                    mapeamento_colunas['STATUS'] = col_original
                elif any(keyword in col_str for keyword in ['DATA ADM', 'ADM']):
                    mapeamento_colunas['DATA ADM'] = col_original
                elif any(keyword in col_str for keyword in ['INICIO']):
                    mapeamento_colunas['INICIO'] = col_original
                elif any(keyword in col_str for keyword in ['DATA ALÔ', 'ALO']):
                    mapeamento_colunas['DATA ALÔ'] = col_original
                elif any(keyword in col_str for keyword in ['TIPO']):
                    mapeamento_colunas['TIPO'] = col_original
                elif any(keyword in col_str for keyword in ['CANAL']):
                    mapeamento_colunas['CANAL'] = col_original
                elif any(keyword in col_str for keyword in ['CÉLULA', 'CELULA']):
                    mapeamento_colunas['CÉLULA'] = col_original
                elif any(keyword in col_str for keyword in ['CAPACITY']):
                    mapeamento_colunas['CAPACITY'] = col_original
                elif any(keyword in col_str for keyword in ['INICIOU']):
                    mapeamento_colunas['INICIOU'] = col_original
                elif any(keyword in col_str for keyword in ['PREVISTO']):
                    mapeamento_colunas['PREVISTO'] = col_original
                elif any(keyword in col_str for keyword in ['ENTREGUE']):
                    mapeamento_colunas['ENTREGUE'] = col_original
                elif any(keyword in col_str for keyword in ['REPRESADO']):
                    mapeamento_colunas['REPRESADO'] = col_original
                else:
                    # Para colunas não mapeadas, tentar usar posição
                    if col_original not in ['Planilha_Origem'] and len(mapeamento_colunas) < len(colunas_padrao):
                        coluna_disponivel = None
                        for col_pad in colunas_padrao:
                            if col_pad not in mapeamento_colunas:
                                coluna_disponivel = col_pad
                                break
                        if coluna_disponivel:
                            mapeamento_colunas[coluna_disponivel] = col_original
            
            # Copiar os dados mapeados
            for col_padrao, col_original in mapeamento_colunas.items():
                if col_padrao in colunas_padrao and col_original in df.columns:
                    df_padronizado[col_padrao] = df[col_original]
            
            # Copiar dados não mapeados para colunas genéricas
            for col in df.columns:
                if col not in mapeamento_colunas.values():
                    nome_generico = f'Dados_{len(df_padronizado.columns)}'
                    if nome_generico not in df_padronizado.columns:
                        df_padronizado[nome_generico] = df[col]
            
            df = df_padronizado
        
        # Adicionar coluna de origem
        df['Planilha_Origem'] = nome_planilha
        
        logger.info(f"Planilha {nome_planilha} processada e padronizada: {len(df)} registros")
        return df
        
    except Exception as e:
        logger.error(f"Erro ao processar planilha {nome_planilha}: {str(e)}")
        return None

def consolidar_planilhas():
    """
    Nova lógica para consolidar todas as planilhas subordinadas em uma planilha mestre.
    """
    try:
        logger.info("=== INICIANDO PROCESSO DE CONSOLIDAÇÃO ===")
        
        # 1. CRIAR BACKUP DA PLANILHA MESTRE EXISTENTE (SE HOUVER)
        backup_criado = False
        if os.path.exists(PLANILHA_MESTRE_PATH):
            backup_path = criar_backup_mestre()
            if backup_path:
                backup_criado = True
                logger.info(f"Backup da planilha mestre criado: {backup_path}")
        
        # 2. VERIFICAR DIRETÓRIO DE PLANILHAS ORIGINAIS
        if not os.path.exists(PLANILHAS_ORIGINAIS_DIR):
            logger.error(f"Diretório de planilhas originais não encontrado: {PLANILHAS_ORIGINAIS_DIR}")
            return False, "Diretório de planilhas originais não encontrado"

        # 3. LISTAR PLANILHAS DISPONÍVEIS
        planilhas = [f for f in os.listdir(PLANILHAS_ORIGINAIS_DIR) 
                    if f.endswith(('.xlsx', '.xls')) and not f.startswith('~$')]

        if not planilhas:
            logger.warning("Nenhuma planilha encontrada para consolidação")
            return False, "Nenhuma planilha encontrada para consolidação"
        
        logger.info(f"Planilhas encontradas: {planilhas}")

        # 4. DEFINIR COLUNAS PADRONIZADAS (CONFORME IMAGENS)
        colunas_padrao = [
            'LÍDER', 'STATUS', 'DATA ADM', 'INICIO', 'DATA ALÔ', 
            'TIPO', 'CANAL', 'CÉLULA', 'CAPACITY', 'INICIOU',
            'PREVISTO', 'ENTREGUE', 'REPRESADO'
        ]
        
        # 5. PROCESSAR CADA PLANILHA COM PADRONIZAÇÃO
        dfs_processados = []
        planilhas_processadas = []
        
        for planilha in planilhas:
            caminho_planilha = os.path.join(PLANILHAS_ORIGINAIS_DIR, planilha)
            df_processado = processar_planilha_estruturada(caminho_planilha, planilha, colunas_padrao)
            
            if df_processado is not None and not df_processado.empty:
                dfs_processados.append(df_processado)
                planilhas_processadas.append(planilha)
                logger.info(f"[OK] {planilha}: {len(df_processado)} registros adicionados")
            else:
                logger.warning(f"[ERRO] {planilha}: Ignorada (vazia ou com erro)")

        # 6. VERIFICAR SE HÁ DADOS PARA CONSOLIDAR
        if not dfs_processados:
            logger.error("Nenhuma planilha válida encontrada para consolidação")
            return False, "Nenhuma planilha válida encontrada para consolidação"

        # 7. CONSOLIDAR TODOS OS DATAFRAMES COM CABEÇALHO ÚNICO
        logger.info("Consolidando dados...")
        df_consolidado = pd.concat(dfs_processados, ignore_index=True, sort=False)

        if df_consolidado.empty:
            logger.error("Resultado da consolidação está vazio")
            return False, "Nenhum dado válido para consolidar. Verifique as planilhas de origem."

        # 8. ADICIONAR METADADOS
        df_consolidado['Data_Consolidacao'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        df_consolidado['ID_Consolidacao'] = range(1, len(df_consolidado) + 1)

        # 9. GARANTIR DIRETÓRIO E SALVAR
        os.makedirs(PLANILHA_MESTRE_DIR, exist_ok=True)
        
        # Salvar a planilha mestre
        df_consolidado.to_excel(PLANILHA_MESTRE_PATH, index=False)
        
        # Verificar se o arquivo foi realmente criado
        if not os.path.exists(PLANILHA_MESTRE_PATH):
            logger.error("Falha ao criar arquivo da planilha mestre")
            return False, "Erro ao salvar planilha mestre"
        
        tamanho_arquivo = os.path.getsize(PLANILHA_MESTRE_PATH)
        logger.info(f"[SUCESSO] Planilha mestre criada: {PLANILHA_MESTRE_PATH} ({tamanho_arquivo} bytes)")
        logger.info(f"[SUCESSO] Total de registros consolidados: {len(df_consolidado)}")
        logger.info(f"[SUCESSO] Colunas na planilha mestre: {list(df_consolidado.columns)}")
        
        return True, {
            "total_registros": len(df_consolidado),
            "planilhas_processadas": planilhas_processadas,
            "colunas": list(df_consolidado.columns),
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "backup_criado": backup_criado,
            "tamanho_arquivo_bytes": tamanho_arquivo,
            "caminho_arquivo": PLANILHA_MESTRE_PATH
        }

    except Exception as e:
        logger.error(f"Erro durante a consolidação: {str(e)}")
        return False, f"Erro durante a consolidação: {str(e)}"

def obter_planilha_mestre():
    """
    Retorna o caminho da planilha mestre se existir.
    """
    if os.path.exists(PLANILHA_MESTRE_PATH):
        return PLANILHA_MESTRE_PATH
    return None
