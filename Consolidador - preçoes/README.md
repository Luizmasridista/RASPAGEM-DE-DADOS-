# 🛒 Sistema de Monitoramento de Preços Online

Um sistema automatizado para monitorar preços de produtos em e-commerces, com notificações por email e armazenamento histórico de dados.

## 🚀 Funcionalidades

### ✅ **Monitoramento Automático**
- Web scraping inteligente com múltiplos seletores
- Retry automático com backoff exponencial
- Suporte a diferentes estruturas de HTML
- Validação robusta de dados extraídos

### 📧 **Sistema de Notificações**
- **Console**: Notificações coloridas no terminal
- **Email**: Templates HTML profissionais com:
  - Alertas de preço com comparação visual
  - Cálculo automático de economia
  - Links diretos para produtos
  - Alertas de sistema com níveis de severidade

### 💾 **Armazenamento de Dados**
- Banco de dados SQLite para histórico
- Transações seguras
- Backup automático de dados
- Consultas otimizadas

### ⚙️ **Configuração Flexível**
- Arquivo JSON para configuração de produtos
- Validação automática de configurações
- Suporte a múltiplos produtos
- Configuração de intervalos personalizados

## 📁 Estrutura do Projeto

```
sistema-monitoramento-precos/
├── .kiro/specs/                    # Especificações do projeto
├── components/                     # Componentes de configuração
├── models/                         # Modelos de dados e interfaces
├── services/                       # Serviços principais
│   ├── web_scraper.py             # Web scraping
│   ├── database_manager.py        # Gerenciamento de BD
│   ├── notification_service.py    # Sistema de notificações
│   ├── html_parser.py             # Parser HTML
│   └── http_client.py             # Cliente HTTP
├── tests/                         # Testes unitários
├── config.json                    # Configuração do sistema
├── produtos.json                  # Configuração de produtos
└── requirements.txt               # Dependências
```

## 🛠️ Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/Luizmasridista/RASPAGEM-DE-DADOS-.git
cd RASPAGEM-DE-DADOS-
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure os produtos** (edite `produtos.json`):
```json
{
  "produtos": [
    {
      "nome": "Smartphone Samsung Galaxy S24",
      "url": "https://example.com/produto",
      "preco_alvo": 2500.00
    }
  ]
}
```

4. **Configure email** (opcional, edite `config.json`):
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "seu_email@gmail.com",
    "password": "sua_senha_app",
    "from_email": "seu_email@gmail.com",
    "to_emails": ["destinatario@gmail.com"]
  }
}
```

## 🚀 Uso

### Execução Básica
```bash
python -m services.web_scraper
```

### Testes
```bash
# Executar todos os testes
python -m pytest tests/ -v

# Testar componente específico
python -m pytest tests/test_notification_service.py -v
```

### Demos
```bash
# Demo do sistema de notificações
python test_notification_demo.py

# Demo específico de email
python test_email_notification_demo.py
```

## 📊 Exemplos de Uso

### Configuração de Produto
```python
from models.data_models import ProductConfig

produto = ProductConfig(
    nome="Notebook Dell Inspiron 15",
    url="https://example.com/notebook",
    preco_alvo=3000.00
)
```

### Sistema de Notificações
```python
from services.notification_service import NotificationService, EmailConfig, EmailNotifier

# Criar serviço
service = NotificationService()

# Adicionar notificador de email
email_config = EmailConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="seu_email@gmail.com",
    password="sua_senha",
    from_email="seu_email@gmail.com",
    to_emails=["destinatario@gmail.com"]
)

email_notifier = EmailNotifier(email_config)
service.add_notifier("email", email_notifier)

# Enviar alerta de preço
service.send_price_alert(produto, 2799.99)
```

## 🧪 Testes

O projeto inclui **41 testes unitários** cobrindo:

- ✅ Web scraping e parsing HTML
- ✅ Gerenciamento de banco de dados
- ✅ Sistema de notificações (console + email)
- ✅ Configuração e validação
- ✅ Tratamento de erros
- ✅ Templates de email

```bash
# Executar todos os testes
python -m pytest tests/ -v

# Cobertura de testes
python -m pytest tests/ --cov=services --cov=models --cov=components
```

## 📧 Templates de Email

### Alerta de Preço
- Design responsivo e profissional
- Comparação visual de preços
- Cálculo automático de economia
- Botão direto para o produto
- Formatação em moeda brasileira (R$)

### Alertas de Sistema
- Códigos de cor por severidade
- Timestamps automáticos
- Mensagens claras e informativas
- Design consistente

## 🔧 Tecnologias Utilizadas

- **Python 3.12+**
- **Requests** - Cliente HTTP
- **BeautifulSoup4** - Parsing HTML
- **SQLite** - Banco de dados
- **SMTP** - Envio de emails
- **Pytest** - Testes unitários
- **JSON** - Configuração

## 📈 Funcionalidades Avançadas

### Web Scraping Inteligente
- Múltiplos seletores CSS para maior compatibilidade
- Retry automático com backoff exponencial
- Headers personalizados para evitar bloqueios
- Validação de dados extraídos

### Sistema de Notificações Robusto
- Suporte a múltiplos canais (console, email)
- Templates HTML responsivos
- Tratamento de falhas gracioso
- Logs detalhados

### Gerenciamento de Dados
- Transações SQLite seguras
- Histórico completo de preços
- Consultas otimizadas
- Backup automático

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Luiz Eduardo** - [@luizmasridista](https://github.com/Luizmasridista)

## 🎯 Roadmap

- [ ] Interface web com Streamlit
- [ ] Suporte a mais e-commerces
- [ ] Notificações via Telegram
- [ ] Dashboard de analytics
- [ ] API REST
- [ ] Docker containerization
- [ ] Agendamento automático

---

⭐ **Se este projeto foi útil para você, considere dar uma estrela!**