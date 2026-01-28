# Pasta de Dados de Candidaturas

Esta pasta armazena os dados históricos das candidaturas realizadas pelo bot.

## Arquivos de Dados (não versionados)

Os seguintes arquivos são gerados automaticamente pela aplicação e **não devem ser versionados** no Git:

- `all_applied_applications_history.csv` - Histórico de candidaturas bem-sucedidas
- `all_failed_applications_history.csv` - Histórico de candidaturas com falha

Estes arquivos estão no `.gitignore` para evitar conflitos e perda de dados durante `git pull/push`.

## Primeira Configuração

Se você está clonando o repositório pela primeira vez:

1. Copie os templates para criar os arquivos iniciais:
```bash
cp "all_applied_applications_history.csv.template" "all_applied_applications_history.csv"
cp "all_failed_applications_history.csv.template" "all_failed_applications_history.csv"
```

2. Ou simplesmente execute o bot - ele criará os arquivos automaticamente se não existirem.

## Backup de Dados

⚠️ **IMPORTANTE**: Faça backup regular dos arquivos CSV, pois eles contêm todo o histórico de candidaturas e não são sincronizados via Git.

Recomendamos:
- Backup local periódico
- Sincronização com cloud storage (Google Drive, Dropbox, etc.)
- Exportação para banco de dados (se necessário)
