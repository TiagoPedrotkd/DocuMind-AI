# DocuMind AI

**Personal Tech Analyst Assistant** — lê documentação de projeto e gera artefactos prontos para o teu trabalho diário.

Transforma PDFs (BRD, specs, contratos, atas) em requisitos, user stories, riscos, perguntas para workshops e drafts Jira — sem login, sem configuração complexa.

---

## O que faz por ti

| Funcionalidade | Descrição |
|----------------|-----------|
| **Ler documentos** | Upload de PDFs com RAG (busca semântica nos documentos) |
| **Responder perguntas** | Chat sobre o conteúdo carregado |
| **Extrair requisitos** | Catálogo classificado (funcional, não-funcional, regras, dependências) |
| **Gerar User Stories** | Stories com critérios de aceitação, ligadas aos requisitos |
| **Identificar riscos** | Registo de riscos com impacto e recomendações |
| **Perguntas para workshops** | Perguntas para clarificar com stakeholders |
| **Conteúdo para Jira** | Drafts de Epics, Stories e issues de risco |

---

## Início rápido

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
# Edita .env e define GEMINI_API_KEY
streamlit run app.py
```

Abre http://localhost:8501 — **sem login**, abre direto.

### Configuração mínima

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Chave gratuita em [Google AI Studio](https://aistudio.google.com/apikey).

---

## Fluxo de trabalho (15–20 min por projeto)

1. **Carregar PDFs** na barra lateral (BRD, specs, contratos, atas…)
2. Tab **Início** → *Executar análise* (pipeline completo)
3. Clicar **Gerar drafts Jira**
4. Tab **Entregáveis** → rever requisitos, stories, riscos e Jira
5. Tab **Assistente** → Chat para perguntas pontuais (*"o que diz sobre autenticação?"*)
6. Tab **Mais → Exportar** → Excel, Markdown, Word ou PDF

```
PDFs → Analyst Copilot → Entregáveis → Jira / Export
                ↓
         Chat (perguntas ad-hoc)
```

---

## Interface

| Tab | Conteúdo |
|-----|----------|
| **Início** | Guia de 3 passos + Analyst Copilot + gerar Jira |
| **Entregáveis** | Requisitos, stories, riscos, perguntas workshop, drafts Jira |
| **Assistente** | Chat RAG + análise de notas de reunião |
| **Mais** | Exportar, resumos, comparação de documentos, funcionalidades avançadas |

A barra lateral mostra o **progresso** do projeto (documentos → requisitos → stories → riscos → Jira).

---

## Analyst Copilot

Pipeline de análise que corre na tab **Início**:

| Módulo | Output |
|--------|--------|
| Requisitos | REQ-001, REQ-002… classificados por categoria e prioridade |
| User Stories | US-001 com critérios de aceitação |
| Riscos | Impacto, probabilidade, mitigação |
| Ambiguidades | Pontos pouco claros + pergunta sugerida |
| Lacunas | O que falta na documentação |
| Stakeholders | 10–15 perguntas para workshop |
| Resumo executivo | Síntese de 1 página |
| Rastreabilidade | Requisito → documento → página |

Podes executar o **pipeline completo** ou um módulo individual.

---

## Jira & Export

Depois da análise, o botão **Gerar drafts Jira** cria:

- **Epics** a partir dos requisitos
- **Stories** a partir das user stories
- **Issues de risco** com labels

Exporta em **Mais → Exportar**: Excel, Markdown, Word, PDF.

### Integrações reais (opcional)

Sem credenciais, a app funciona em **modo preview**. Para sincronizar com Jira/Confluence/Azure:

```env
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=...
JIRA_PROJECT_KEY=PROJ
```

Configuração em **Mais → Avançado → Integrações**.

---

## Funcionalidades avançadas (opcional)

Disponíveis em **Mais → Avançado** — não são necessárias para o fluxo diário:

- Delivery Intelligence (health score, estimations, test scenarios, executive reports)
- Integrações Jira / Confluence / Azure DevOps
- Knowledge Base e vista por role (BA, PM, Executive…)
- Comparação entre documentos e deteção de contradições
- Resumos estruturados por documento

---

## Stack técnica

| Camada | Tecnologia |
|--------|------------|
| UI | Streamlit |
| LLM | Google Gemini (`GEMINI_API_KEY`) |
| RAG | FAISS + embeddings Gemini |
| Persistência local | SQLite (sessão, histórico, knowledge base) |
| Export | Excel, Markdown, Word, PDF |

OpenAI é suportada como fallback se `GEMINI_API_KEY` não estiver definida.

---

## Testes

```bash
pytest tests/
```

---

## Enterprise (opcional)

Para equipas que queiram Docker, PostgreSQL, Redis, Neo4j, LangGraph e API FastAPI — o código existe no repositório mas **não aparece na UI principal**.

```bash
docker compose up --build
```

| Serviço | URL |
|---------|-----|
| Streamlit | http://localhost:8501 |
| FastAPI | http://localhost:8000 |
| Neo4j | http://localhost:7474 |

Variáveis em `.env.example` (`ORCHESTRATOR_MODE`, `POSTGRES_URL`, `NEO4J_URI`, etc.).

---

## Histórico de versões

| Versão | Foco |
|--------|------|
| **Atual** | Personal Tech Analyst Assistant — UI simplificada |
| v6 | Multi-agent platform (código mantido, UI removida) |
| v5 | Delivery Intelligence — Jira, health, estimations |
| v4 | Analyst Copilot — 10 módulos de análise |
| v3 | Multi-documento, comparação, persistência |
| v2 | RAG conversacional |
| v1 | Resumos e OCR |

---

## Licença

MIT License
