# Script para limpar o repositório Git

# 1. Parar de rastrear todos os arquivos
git rm -r --cached .

# 2. Adicionar apenas os arquivos que queremos manter
git add .

# 3. Fazer commit das mudanças
git commit -m "Limpeza do repositório e aplicação do .gitignore"

# 4. Forçar push para o repositório remoto
git push -f origin master

Write-Host "Repositório limpo com sucesso!" -ForegroundColor Green
