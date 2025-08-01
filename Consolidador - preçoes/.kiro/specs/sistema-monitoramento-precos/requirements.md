# Requirements Document

## Introduction

O Sistema de Monitoramento de Preços Online é uma ferramenta automatizada que monitora preços de produtos específicos em e-commerces, armazena dados históricos e envia notificações quando preços atingem valores pré-definidos. O sistema demonstra competências em automação, web scraping, manipulação de banco de dados e programação orientada a dados, servindo como um excelente projeto de portfólio.

## Requirements

### Requirement 1

**User Story:** Como um usuário, eu quero configurar produtos para monitoramento através de um arquivo JSON, para que eu possa definir quais produtos monitorar e seus preços alvo.

#### Acceptance Criteria

1. WHEN o sistema é inicializado THEN o sistema SHALL carregar a configuração de produtos do arquivo produtos.json
2. IF o arquivo produtos.json não existir THEN o sistema SHALL criar um arquivo de exemplo com estrutura válida
3. WHEN um produto é configurado THEN o sistema SHALL validar que contém nome, url e preco_alvo
4. IF a configuração de um produto estiver inválida THEN o sistema SHALL exibir erro específico e pular o produto

### Requirement 2

**User Story:** Como um usuário, eu quero que o sistema colete automaticamente dados de preço de páginas web, para que eu não precise verificar manualmente os preços.

#### Acceptance Criteria

1. WHEN o sistema acessa uma URL de produto THEN o sistema SHALL extrair o nome e preço do produto usando web scraping
2. IF uma página não responder THEN o sistema SHALL registrar o erro e continuar com outros produtos
3. WHEN dados são extraídos THEN o sistema SHALL validar que o preço é um valor numérico válido
4. IF o HTML da página mudar THEN o sistema SHALL tentar múltiplos seletores para encontrar o preço
5. WHEN uma requisição falha THEN o sistema SHALL implementar retry com backoff exponencial

### Requirement 3

**User Story:** Como um usuário, eu quero que o sistema armazene o histórico de preços em um banco de dados, para que eu possa acompanhar a evolução dos preços ao longo do tempo.

#### Acceptance Criteria

1. WHEN o sistema é inicializado THEN o sistema SHALL criar o banco de dados SQLite se não existir
2. WHEN dados de preço são coletados THEN o sistema SHALL inserir os dados na tabela precos com timestamp
3. WHEN dados são inseridos THEN o sistema SHALL incluir id, nome_produto, preco, data_hora
4. IF a inserção no banco falhar THEN o sistema SHALL registrar o erro e continuar operação
5. WHEN o banco é acessado THEN o sistema SHALL usar transações para garantir integridade dos dados

### Requirement 4

**User Story:** Como um usuário, eu quero receber notificações quando um produto atingir o preço alvo, para que eu possa aproveitar oportunidades de compra.

#### Acceptance Criteria

1. WHEN um preço coletado é menor ou igual ao preço alvo THEN o sistema SHALL enviar notificação
2. WHEN uma notificação é enviada THEN o sistema SHALL exibir alerta no console com detalhes do produto
3. IF configurado THEN o sistema SHALL enviar notificação por email
4. WHEN múltiplos produtos atingem preço alvo THEN o sistema SHALL enviar notificações para todos
5. IF o envio de notificação falhar THEN o sistema SHALL registrar o erro mas continuar operação

### Requirement 5

**User Story:** Como um usuário, eu quero que o sistema execute automaticamente em intervalos regulares, para que o monitoramento seja contínuo sem intervenção manual.

#### Acceptance Criteria

1. WHEN o sistema é iniciado THEN o sistema SHALL agendar execução periódica usando schedule
2. WHEN o agendamento é configurado THEN o sistema SHALL permitir configurar intervalo de execução
3. WHEN uma execução agendada inicia THEN o sistema SHALL processar todos os produtos configurados
4. IF uma execução agendada falhar THEN o sistema SHALL registrar erro e continuar com próxima execução
5. WHEN o sistema está rodando THEN o sistema SHALL manter log de todas as execuções

### Requirement 6

**User Story:** Como um usuário, eu quero visualizar os dados coletados através de uma interface web, para que eu possa acompanhar graficamente a evolução dos preços.

#### Acceptance Criteria

1. WHEN o sistema web é iniciado THEN o sistema SHALL servir interface Streamlit
2. WHEN a interface é acessada THEN o sistema SHALL exibir lista de produtos monitorados
3. WHEN um produto é selecionado THEN o sistema SHALL exibir gráfico histórico de preços
4. WHEN dados são atualizados THEN o sistema SHALL refletir mudanças na interface em tempo real
5. IF não houver dados THEN o sistema SHALL exibir mensagem informativa

### Requirement 7

**User Story:** Como um usuário, eu quero que o sistema trate erros graciosamente, para que falhas pontuais não interrompam o monitoramento completo.

#### Acceptance Criteria

1. WHEN ocorre erro de rede THEN o sistema SHALL registrar erro e continuar com próximo produto
2. WHEN ocorre erro de parsing HTML THEN o sistema SHALL tentar seletores alternativos
3. WHEN ocorre erro de banco de dados THEN o sistema SHALL registrar erro e tentar reconectar
4. IF múltiplos erros consecutivos ocorrem THEN o sistema SHALL enviar alerta de sistema
5. WHEN o sistema recupera de erro THEN o sistema SHALL registrar recuperação no log

### Requirement 8

**User Story:** Como um desenvolvedor, eu quero que o sistema tenha logs detalhados, para que eu possa diagnosticar problemas e monitorar performance.

#### Acceptance Criteria

1. WHEN qualquer operação é executada THEN o sistema SHALL registrar log com timestamp e nível apropriado
2. WHEN erro ocorre THEN o sistema SHALL registrar stack trace completo
3. WHEN dados são coletados THEN o sistema SHALL registrar estatísticas de performance
4. IF configurado THEN o sistema SHALL rotacionar logs automaticamente
5. WHEN sistema inicia THEN o sistema SHALL registrar configuração e status inicial