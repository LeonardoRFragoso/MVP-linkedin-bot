# 📋 Sistema de Banco de Perguntas - LinkedIn Bot

## 🎯 O que é?

Sistema inteligente que **captura automaticamente TODAS as perguntas** respondidas durante suas candidaturas no LinkedIn e permite que você revise, edite e reutilize essas respostas em futuras candidaturas.

## ✨ Funcionalidades

### 🤖 Automático
- **Captura automática**: Toda pergunta respondida é salva automaticamente
- **Deduplicação inteligente**: Perguntas similares são agrupadas
- **Rastreamento**: Sabe em quais vagas cada pergunta apareceu
- **Reutilização**: Consulta o banco antes de responder novas perguntas

### 🎨 Interface Visual
- **Formulário HTML moderno**: Interface bonita e intuitiva
- **Filtros**: Busque por tipo, status de verificação ou texto
- **Edição em tempo real**: Altere respostas diretamente no navegador
- **Estatísticas**: Veja quantas perguntas foram capturadas

### 📊 Tipos de Perguntas Suportadas
- **SELECT** (dropdowns): Múltipla escolha com opções
- **RADIO** (botões de opção): Escolha única entre opções
- **TEXT** (campos de texto): Respostas curtas
- **TEXTAREA** (áreas de texto): Respostas longas

## 🚀 Como Usar

### 1️⃣ Execute o Bot Normalmente

```bash
python runAiBot.py
```

O bot agora **automaticamente**:
- ✅ Salva todas as perguntas respondidas
- ✅ Consulta o banco antes de responder perguntas já vistas
- ✅ Armazena em `data/questions_bank.json`

### 2️⃣ Revise as Perguntas Capturadas

Em outro terminal/prompt, inicie o servidor de revisão:

```bash
python review_questions_server.py
```

Acesse no navegador:
```
http://localhost:5000
```

### 3️⃣ Revise e Edite

Na interface web você pode:

1. **Ver todas as perguntas** capturadas
2. **Filtrar** por tipo ou status
3. **Buscar** por texto específico
4. **Editar respostas** diretamente
5. **Marcar como verificada** após revisar
6. **Salvar tudo** de uma vez

### 4️⃣ Aproveite a Automação

Nas próximas candidaturas, o bot:
- 🔍 Consulta o banco antes de responder
- 💾 Usa suas respostas verificadas automaticamente
- ✨ Só responde com lógica padrão se não encontrar no banco
- 📝 Continua salvando novas perguntas

## 📁 Estrutura de Arquivos

```
Auto_job_applier_linkedIn/
├── modules/
│   └── questions_bank.py          # Módulo principal do banco
├── data/
│   └── questions_bank.json        # Banco de dados (criado automaticamente)
├── review_questions.html          # Interface web
├── review_questions_server.py     # Servidor Flask
└── BANCO_DE_PERGUNTAS_README.md  # Esta documentação
```

## 🔧 Configurações

### Prioridade de Respostas

O bot usa a seguinte ordem de prioridade ao responder:

1. **Banco de perguntas verificadas** (suas respostas revisadas)
2. **Banco de perguntas vistas 2x+** (respostas consistentes)
3. **Lógica de resposta inteligente** (regras do bot)
4. **Smart answers** (respostas configuradas)
5. **AI** (se habilitada)

### Desabilitar Consulta ao Banco

Se quiser que o bot **não consulte** o banco (mas continue salvando):

Em `config/questions.py`, adicione:
```python
use_questions_bank_lookup = False  # Default: True
```

## 📊 Formato do Banco de Dados

O arquivo `data/questions_bank.json` tem o seguinte formato:

```json
{
  "abc123def456": {
    "label": "How many years of Python experience do you have?",
    "normalized_label": "how many years of python experience do you have",
    "type": "text",
    "answer": "5",
    "options": [],
    "first_seen": "2026-01-17T17:30:00",
    "last_seen": "2026-01-17T18:45:00",
    "times_seen": 3,
    "jobs": [
      {
        "job_id": "12345678",
        "job_title": "Senior Python Developer",
        "date": "2026-01-17T17:30:00"
      }
    ],
    "verified": true,
    "notes": ""
  }
}
```

## 🎓 Dicas de Uso

### ✅ Boas Práticas

1. **Revise periodicamente**: Acesse o formulário a cada 10-20 candidaturas
2. **Marque como verificada**: Após revisar, marque para o bot usar com confiança
3. **Seja consistente**: Use respostas consistentes para perguntas similares
4. **Teste respostas**: Veja quais respostas funcionam melhor

### ⚠️ Cuidados

1. **Respostas específicas**: Algumas perguntas podem ser específicas da vaga
2. **Backup**: Faça backup do `questions_bank.json` periodicamente
3. **Sensibilidade**: Não compartilhe o arquivo (contém suas informações)

## 🐛 Solução de Problemas

### Erro: "Módulo questions_bank não encontrado"
```bash
# Verifique se o arquivo existe:
dir modules\questions_bank.py
```

### Erro: "Porta 5000 já em uso"
```bash
# Altere a porta no review_questions_server.py:
app.run(debug=False, host='0.0.0.0', port=5001)  # Use 5001 ou outra porta
```

### Banco não está salvando perguntas
1. Verifique permissões da pasta `data/`
2. Veja os logs do bot para erros
3. Confirme que o arquivo `data/questions_bank.json` foi criado

### Interface não carrega perguntas
1. Verifique se o servidor está rodando
2. Abra o console do navegador (F12) para ver erros
3. Confirme que o arquivo JSON existe e não está corrompido

## 📈 Estatísticas e Insights

O formulário mostra:
- **Total de perguntas**: Quantas únicas foram capturadas
- **Verificadas**: Quantas você já revisou
- **Pendentes**: Quantas ainda precisam de revisão
- **Por tipo**: Distribuição por SELECT, RADIO, TEXT, TEXTAREA

## 🔄 Fluxo Completo

```
[Candidatura] → [Pergunta Aparece]
                      ↓
         [Bot consulta banco] ← [Resposta encontrada?]
                ↓                        ↓
            [Não]                     [Sim]
                ↓                        ↓
    [Responde com lógica]      [Usa resposta salva]
                ↓                        ↓
        [Salva no banco] ←──────────────┘
                ↓
    [Você revisa depois no formulário]
                ↓
    [Marca como verificada]
                ↓
    [Bot usa nas próximas candidaturas]
```

## 🎉 Benefícios

1. **Consistência**: Mesmas respostas para mesmas perguntas
2. **Velocidade**: Bot responde mais rápido (não precisa processar)
3. **Controle**: Você revisa e aprova as respostas
4. **Aprendizado**: Veja quais perguntas são mais comuns
5. **Otimização**: Melhore respostas baseado em resultados

## 🆘 Suporte

Problemas ou dúvidas?
1. Verifique os logs do bot em `logs/log.txt`
2. Revise esta documentação
3. Abra uma issue no GitHub

---

**Desenvolvido com ❤️ para otimizar suas candidaturas no LinkedIn**
