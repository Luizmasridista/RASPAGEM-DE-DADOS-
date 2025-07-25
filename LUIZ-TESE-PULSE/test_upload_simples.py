"""
Teste simples para verificar se o upload básico funciona.
"""

import streamlit as st
import os

def test_upload_simples():
    """Teste básico de upload sem modularização."""
    
    st.title("🧪 Teste de Upload Simples")
    
    # Upload básico
    uploaded_file = st.file_uploader(
        "Teste de upload básico",
        type=['xlsx', 'xls'],
        key="test_upload"
    )
    
    if uploaded_file:
        st.write(f"Arquivo carregado: {uploaded_file.name}")
        st.write(f"Tamanho: {uploaded_file.size} bytes")
        
        if st.button("💾 Salvar Teste"):
            try:
                # Criar pasta de teste
                test_folder = "test_uploads"
                os.makedirs(test_folder, exist_ok=True)
                st.write(f"✅ Pasta {test_folder} criada/verificada")
                
                # Salvar arquivo
                file_path = os.path.join(test_folder, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                st.write(f"✅ Arquivo salvo em: {file_path}")
                
                # Verificar se existe
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    st.success(f"✅ SUCESSO! Arquivo existe no disco com {size} bytes")
                else:
                    st.error("❌ ERRO! Arquivo não foi encontrado no disco")
                    
            except Exception as e:
                st.error(f"❌ ERRO: {str(e)}")
                st.write(f"Tipo do erro: {type(e).__name__}")
    
    # Mostrar arquivos existentes
    test_folder = "test_uploads"
    if os.path.exists(test_folder):
        files = os.listdir(test_folder)
        if files:
            st.write("📁 Arquivos na pasta de teste:")
            for f in files:
                st.write(f"• {f}")
        else:
            st.write("📁 Pasta de teste vazia")

if __name__ == "__main__":
    test_upload_simples()
