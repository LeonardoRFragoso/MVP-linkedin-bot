# 📊 Gerenciamento de Dados - LinkedIn Job Bot

## 🎯 Problema Resolvido

Anteriormente, os arquivos CSV com histórico de candidaturas eram versionados no Git, causando perda de dados durante `git pull/push`. 

**Solução implementada:**
- Arquivos de dados agora estão no `.gitignore`
- Templates foram criados para facilitar o setup inicial
- Seus dados locais não serão mais sobrescritos

## 📁 Arquivos de Dados (Não Versionados)

Os seguintes arquivos são gerados localmente e **não são sincronizados** via Git:

```
all excels/
  ├── all_applied_applications_history.csv    ❌ Não versionado
  └── all_failed_applications_history.csv     ❌ Não versionado

logs/
  ├── log.txt                                 ❌ Não versionado
  └── screenshots/                            ❌ Não versionado

chrome_profile_linkedin_bot/                  ❌ Não versionado
```

## 🚀 Setup Inicial (Primeira vez)

### Opção 1: Script Automático
```powershell
.\setup_data_files.ps1
```

### Opção 2: Manual
```powershell
# Copiar templates
Copy-Item "all excels\all_applied_applications_history.csv.template" "all excels\all_applied_applications_history.csv"
Copy-Item "all excels\all_failed_applications_history.csv.template" "all excels\all_failed_applications_history.csv"
```

### Opção 3: Deixar o Bot Criar
Simplesmente execute o bot - ele criará os arquivos automaticamente se não existirem.

## 📤 Próximos Passos para Commit

Agora você pode fazer commit das mudanças de proteção de dados:

```powershell
# Verificar o que será commitado
git status

# Fazer commit
git commit -m "feat: proteger arquivos de dados no .gitignore

- Adicionar CSV e logs ao .gitignore para evitar perda de dados
- Criar templates para setup inicial
- Adicionar chrome_profile_linkedin_bot ao .gitignore
- Incluir documentação sobre gerenciamento de dados"

# Push para o repositório remoto
git push
```

## 💾 Backup de Dados

### ⚠️ IMPORTANTE
Seus dados de candidaturas agora estão **apenas no seu computador local**.

### Recomendações de Backup:

1. **Backup Local Periódico**
   ```powershell
   # Criar backup com data
   $date = Get-Date -Format "yyyy-MM-dd"
   Copy-Item "all excels\*.csv" "backup\backup_$date\"
   ```

2. **Cloud Storage**
   - Configure sincronização automática com Google Drive, Dropbox, OneDrive, etc.
   - Coloque a pasta `all excels` em uma pasta sincronizada

3. **Exportação para Banco de Dados**
   - Considere exportar para SQLite ou PostgreSQL para backups mais robustos

4. **Script de Backup Automático**
   ```powershell
   # Adicione ao seu Task Scheduler do Windows
   $backupDir = "D:\Backups\LinkedIn_Bot"
   $date = Get-Date -Format "yyyy-MM-dd_HH-mm"
   New-Item -Path "$backupDir\$date" -ItemType Directory -Force
   Copy-Item "all excels\*.csv" "$backupDir\$date\"
   Copy-Item "logs\log.txt" "$backupDir\$date\"
   ```

## 🔄 Workflow Recomendado

### Antes de Pull/Push:
```powershell
# Suas mudanças de código
git add .
git commit -m "feat: sua feature"
git pull
git push
```

**Seus arquivos CSV estão seguros!** Eles não serão afetados por pull/push.

### Sincronizar Dados Entre Máquinas:
Se você trabalha em múltiplas máquinas, use:
- Google Drive / Dropbox para sincronizar a pasta `all excels`
- Banco de dados compartilhado (PostgreSQL, MySQL)
- Script de backup/restore personalizado

## 📋 Checklist de Segurança

- [x] `.gitignore` configurado corretamente
- [x] Arquivos CSV removidos do Git (mas mantidos localmente)
- [x] Templates criados para setup inicial
- [x] Documentação criada
- [ ] Backup configurado
- [ ] Testar em nova máquina (clonar repositório e executar setup)

## 🆘 Recuperação de Dados

Se você perdeu dados antes desta implementação:

1. **Verificar histórico do Git:**
   ```powershell
   git log --all --full-history -- "all excels/*.csv"
   git show <commit-hash>:"all excels/all_applied_applications_history.csv" > recovered.csv
   ```

2. **Verificar backups locais:**
   - Verificar Recycle Bin / Lixeira
   - Verificar histórico de versões do OneDrive (se aplicável)
   - Verificar backups do sistema

## 📞 Suporte

Para dúvidas ou problemas relacionados ao gerenciamento de dados, verifique:
- Este documento
- `all excels/README.md`
- Issues do repositório
