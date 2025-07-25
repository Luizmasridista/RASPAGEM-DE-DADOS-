# Sistema de Consolidação de Planilhas de Treinamento

Sistema para automatizar a consolidação de planilhas de treinamento de 4 estruturas diferentes da empresa.

## Funcionalidades

- Consolidação automática de planilhas das 4 estruturas
- Atualização automática dos dados
- Backup automático com timestamp
- Preservação da estrutura e layout das planilhas originais
- Interface web amigável para gerenciamento

## Estrutura do Projeto

```
.
├── backend/                  # API REST em FastAPI
│   ├── __init__.py
│   ├── config.py             # Configurações do sistema
│   ├── consolidador.py       # Lógica de consolidação
│   └── main.py               # Endpoints da API
├── frontend/                 # Interface web em Streamlit
│   └── app.py                # Aplicação Streamlit
├── planilhas_originais/      # Pasta para as planilhas das 4 estruturas
├── planilha_mestre/          # Pasta para o arquivo consolidado
├── backups/                  # Pasta para backups automáticos
├── planilhas_exemplo/        # Planilhas de exemplo para testes
├── start.py                  # Script para iniciar o sistema
├── test_sistema.py           # Testes automatizados
└── requirements.txt          # Dependências do projeto
```

## Requisitos

- Python 3.7+
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Uso

1. Inicie o sistema:

```bash
python start.py
```

2. Acesse a interface web em: http://localhost:8501
3. A documentação da API estará disponível em: http://localhost:8000/docs

## Fluxo de Trabalho

1. Faça upload das planilhas das 4 estruturas na seção "Upload de Planilhas"
2. Inicie a consolidação na seção "Consolidação"
3. Visualize estatísticas e baixe a planilha mestre no "Dashboard"
4. Acesse backups anteriores na seção "Backups"

## Testes

Execute os testes automatizados com:

```bash
python test_sistema.py
```

## Estrutura das Planilhas

As planilhas devem conter as seguintes colunas:
- Colaborador
- Departamento
- Treinamento
- Carga_Horaria
- Data_Inicio
- Data_Fim
- Status
