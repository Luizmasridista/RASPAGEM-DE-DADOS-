"""
Versão de debug ultra-simples do upload para identificar o problema.
"""

import streamlit as st
import os

def mostrar_upload_planilhas():
    """Versão debug ultra-simples do upload."""
    
    st.title("🔧 Upload Debug - Versão Simples")
    st.write("Esta é uma versão simplificada para debug")
    
    # Upload básico
    uploaded_files = st.file_uploader(
        "Selecione planilhas para teste",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        key="debug_upload"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")
        
        for i, file in enumerate(uploaded_files):
            st.write(f"{i+1}. {file.name} ({file.size} bytes)")
        
        if st.button("💾 SALVAR AGORA", type="primary"):
            st.write("🔄 Iniciando salvamento...")
            
            # Criar pasta
            pasta = "planilhas_originais"
            try:
                os.makedirs(pasta, exist_ok=True)
                st.write(f"✅ Pasta {pasta} criada/verificada")
            except Exception as e:
                st.error(f"❌ Erro ao criar pasta: {e}")
                return
            
            # Salvar cada arquivo
            for file in uploaded_files:
                try:
                    caminho = os.path.join(pasta, file.name)
                    st.write(f"📝 Salvando {file.name} em {caminho}")
                    
                    # Salvar
                    with open(caminho, "wb") as f:
                        f.write(file.getvalue())
                    
                    # Verificar
                    if os.path.exists(caminho):
                        tamanho = os.path.getsize(caminho)
                        st.write(f"✅ {file.name} salvo! Tamanho: {tamanho} bytes")
                    else:
                        st.error(f"❌ {file.name} NÃO foi salvo!")
                        
                except Exception as e:
                    st.error(f"❌ Erro ao salvar {file.name}: {e}")
            
            st.success("🎉 Processo concluído!")
            
            # Listar arquivos salvos
            try:
                arquivos = os.listdir(pasta)
                st.write(f"📁 Arquivos na pasta {pasta}:")
                for arq in arquivos:
                    st.write(f"• {arq}")
            except Exception as e:
                st.error(f"❌ Erro ao listar pasta: {e}")
    
    # Status atual
    st.markdown("---")
    st.subheader("📊 Status Atual")
    
    pasta = "planilhas_originais"
    if os.path.exists(pasta):
        arquivos = [f for f in os.listdir(pasta) if f.endswith(('.xlsx', '.xls'))]
        st.write(f"📁 Planilhas encontradas: {len(arquivos)}")
        for arq in arquivos:
            st.write(f"• {arq}")
    else:
        st.write("📁 Pasta planilhas_originais não existe")
