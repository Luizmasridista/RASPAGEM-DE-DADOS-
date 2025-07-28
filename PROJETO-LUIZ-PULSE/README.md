# Sistema de Consolidação de Dados

Sistema MVP para consolidação de planilhas Excel usando Flet e Python.

## Funcionalidades

- Upload de planilhas subordinadas
- Consolidação automática em planilha mestre
- Backup automático com timestamp
- Interface step-by-step com sidebar
- Sistema modularizado e organizado

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python main.py
```

## Estrutura do Projeto

- `main.py` - Aplicação principal
- `models/` - Modelos de dados
- `services/` - Lógica de negócio
- `ui/` - Componentes de interface
- `utils/` - Utilitários
- `backups/` - Pasta para backups automáticos

## Como usar

1. Execute a aplicação
2. Siga os passos no sidebar:
   - Configurar planilha mestre
   - Upload de planilhas subordinadas
   - Configurar consolidação
   - Executar consolidação
   - Visualizar resultados

---

## Resumo prático

1. **Selecione o interpretador Python correto no VSCode.**
2. **Garanta que as dependências estão instaladas nesse ambiente.**
3. **Reinicie o VSCode ou recarregue a janela.**

Se mesmo assim o erro persistir, me envie:
- O caminho do Python que aparece no terminal do VSCode (`python -c "import sys; print(sys.executable)"`)
- O caminho do Python selecionado no VSCode (canto inferior direito)

Assim posso te ajudar a resolver de forma definitiva!
