# LinkedIn Bot - White Label MVP

## 📋 Visão Geral

Este documento descreve a arquitetura white label implementada para o LinkedIn Job Bot, permitindo suporte multi-tenant e comercialização como SaaS.

## 🏗️ Estrutura Implementada

```
Auto_job_applier_linkedIn/
├── core/                          # Camada de serviços
│   ├── __init__.py               # Exports principais
│   ├── encryption_service.py     # Criptografia de credenciais
│   ├── config_service.py         # Gerenciador de configurações
│   ├── config_compat.py          # Compatibilidade com config antigo
│   ├── database.py               # SQLAlchemy setup
│   └── models.py                 # Modelos do banco de dados
├── api/                          # API REST FastAPI
│   ├── __init__.py
│   ├── main.py                   # Aplicação FastAPI
│   └── routes/                   # Rotas organizadas
├── scripts/                      # Scripts de utilitários
│   ├── migrate_config_to_json.py # Migra config/*.py → JSON
│   └── seed_database.py          # Popular banco de dados
├── tests/                        # Testes unitários
│   └── test_encryption_service.py
├── config/
│   └── tenants/                  # Configurações por tenant
│       └── default/
├── .env.example                  # Template de variáveis
└── requirements_whitelabel.txt   # Dependências adicionais
```

## 🚀 Quick Start

### 1. Instalar Dependências

```bash
pip install -r requirements_whitelabel.txt
```

### 2. Configurar Ambiente

```bash
# Copiar template de variáveis
cp .env.example .env

# Editar .env com suas configurações
# IMPORTANTE: Definir ENCRYPTION_KEY
```

### 3. Migrar Configurações Existentes

```bash
# Converte config/*.py para JSON
python scripts/migrate_config_to_json.py
```

### 4. Inicializar Banco de Dados

```bash
# Cria tabelas e popula com dados existentes
python scripts/seed_database.py
```

### 5. Iniciar API

```bash
uvicorn api.main:app --reload
# Acesse: http://localhost:8000/docs
```

## 🔐 Segurança

### Criptografia de Credenciais

Todas as credenciais sensíveis são criptografadas usando Fernet (AES-128-CBC):

```python
from core.encryption_service import EncryptionService

encryption = EncryptionService()
encrypted = encryption.encrypt("minha-senha")
decrypted = encryption.decrypt(encrypted)
```

### Variáveis de Ambiente Obrigatórias

| Variável | Descrição |
|----------|-----------|
| `ENCRYPTION_KEY` | Chave Fernet para criptografia |
| `SECRET_KEY` | Chave para JWT/sessões |
| `DATABASE_URL` | URL de conexão do banco |

## 📦 Modelos de Dados

### Tenant (Multi-tenant)
- `id`, `slug`, `name`
- `branding` (JSON): logo, cores, tema
- `features` (JSON): limites, funcionalidades
- `settings` (JSON): timezone, idioma

### User
- `id`, `tenant_id`, `email`
- `personal_info` (JSON): dados pessoais
- `linkedin_credentials` (JSON): credenciais criptografadas
- `search_preferences` (JSON): filtros de busca

### JobApplication
- `id`, `user_id`, `tenant_id`
- `linkedin_job_id`, `title`, `company`
- `status`: applied, failed, skipped
- `questions_answered` (JSON)

### QuestionBank
- `question_hash` (único)
- `label`, `question_type`
- `default_answer`, `options`
- `times_seen`, `verified`

## 🔄 Migração Gradual

O sistema mantém compatibilidade total com o código existente:

### Usando ConfigService (Novo)

```python
from core.config_service import ConfigService

config = ConfigService(tenant_id="default", user_id="user-001")
personal = config.get_personal_info()
email, password = config.get_linkedin_credentials()
```

### Usando Compatibilidade (Transição)

```python
# Substitui imports de config/*.py
from core.config_compat import first_name, last_name, username, password
```

### Código Original (Ainda Funciona)

```python
# Continua funcionando durante transição
from config.personals import first_name, last_name
```

## 📡 API Endpoints

### Health
- `GET /health` - Status da API e banco

### Tenants
- `GET /api/v1/tenants` - Listar tenants
- `GET /api/v1/tenants/{id}` - Obter tenant
- `POST /api/v1/tenants` - Criar tenant

### Users
- `GET /api/v1/tenants/{id}/users` - Listar usuários
- `GET /api/v1/users/{id}` - Obter usuário
- `GET /api/v1/users/{id}/config` - Configurações do usuário
- `POST /api/v1/tenants/{id}/users` - Criar usuário

### Applications
- `GET /api/v1/users/{id}/applications` - Listar candidaturas
- `GET /api/v1/users/{id}/stats` - Estatísticas

### Questions
- `GET /api/v1/questions` - Banco de perguntas
- `GET /api/v1/questions/stats` - Estatísticas

## 🧪 Testes

```bash
# Rodar todos os testes
pytest tests/ -v

# Testar apenas EncryptionService
pytest tests/test_encryption_service.py -v

# Testar ConfigService
python -m core.config_service

# Testar compatibilidade
python -m core.config_compat
```

## 📊 Comandos Úteis

```bash
# Inicializar banco de dados
python -c "from core.database import init_db; init_db()"

# Verificar conexão do banco
python -c "from core.database import DatabaseManager; print(DatabaseManager.health_check())"

# Gerar chave de criptografia
python -c "from core.encryption_service import EncryptionService; print(EncryptionService.generate_key())"

# Rodar migração de config
python scripts/migrate_config_to_json.py --tenant-id=default --user-id=default-user

# Popular banco com dados existentes
python scripts/seed_database.py

# Iniciar API em modo debug
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 🗺️ Próximos Passos

### Fase 2 - Melhorias
- [ ] Dashboard administrativo (React/Next.js)
- [ ] Sistema de autenticação JWT
- [ ] Gestão de planos e billing (Stripe)
- [ ] Notificações por email
- [ ] Webhooks para integrações

### Fase 3 - Escala
- [ ] Cache Redis
- [ ] Queue para jobs assíncronos
- [ ] Métricas e analytics avançados
- [ ] API rate limiting
- [ ] Multi-region deployment

## ⚠️ Notas Importantes

1. **Backup**: Faça backup dos arquivos `config/*.py` antes de qualquer migração
2. **Credenciais**: Nunca commit `.env` ou credenciais no Git
3. **Licença**: O projeto base usa AGPL - consulte advogado para uso comercial
4. **LinkedIn**: Automação pode violar ToS - use com responsabilidade

## 📞 Suporte

- Documentação da API: http://localhost:8000/docs
- Logs: `logs/app.log`
- Issues: GitHub Issues
