# DocuMind AI

Plataforma de inteligência documental e delivery que transforma documentação de projeto em artefactos acionáveis para equipas enterprise.

**Versão 6.0** — Multi-Agent Project Intelligence Platform

---

## Versão 6.0 — Multi-Agent Platform

### Agentes Especializados

| Agente | Responsabilidades |
|--------|-------------------|
| **Analyst Agent** | Requisitos, user stories, ambiguidades, acceptance criteria |
| **Solution Architect Agent** | Arquitetura, componentes, integrações |
| **Security Agent** | GDPR, autenticação, conformidade, proteção de dados |
| **QA Agent** | Casos de teste, cenários, cobertura |
| **Project Manager Agent** | Estimativas, roadmap, plano de implementação |
| **Risk Agent** | Risk register, impacto, mitigação |
| **Orchestrator Agent** | Roteamento inteligente + resposta consolidada |

### Funcionalidades Avançadas

- **Project Digital Twin** — modelo vivo: Requisitos → Stories → Sistemas → Riscos → Testes
- **Sprint Planning AI** — sugestão de sprints com story points
- **Architecture Review** — deteção de SPOF, monitorização, dependências
- **Stakeholder Simulation** — Cliente, PO, Architect, QA Lead
- **Project Health Engine v6** — Requirements, Architecture, Testing, Risk
- **Knowledge Graph** — Neo4j (enterprise) ou SQLite (fallback local)

### Enterprise Stack

| Componente | Tecnologia | Modo |
|------------|------------|------|
| **Orchestrator** | LangGraph / native / CrewAI / AutoGen | `ORCHESTRATOR_MODE` |
| **Knowledge Graph** | Neo4j | `NEO4J_URI` |
| **Persistence** | PostgreSQL | `POSTGRES_URL` |
| **Cache** | Redis | `REDIS_URL` |
| **API** | FastAPI (sem login) | `DOCUMIND_API_URL` |
| **Deploy** | Docker Compose | `docker-compose up` |

### Docker Compose (stack completa)

```bash
# .env com GEMINI_API_KEY
docker compose up --build
```

| Serviço | URL |
|---------|-----|
| Streamlit | http://localhost:8501 |
| FastAPI | http://localhost:8000 |
| Neo4j Browser | http://localhost:7474 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

Depois: http://localhost:8501 (sem login — abre direto)

---

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Opcional — ativar LangGraph:

```env
ORCHESTRATOR_MODE=langgraph
```

### Fluxo v6

> "Analisa este projeto e diz-me os riscos, requisitos em falta, arquitetura recomendada e plano de implementação."

O Orchestrator chama os agentes relevantes e consolida numa resposta única.

1. Carrega PDFs
2. Tab **Início** → pergunta ao Orchestrator
3. Explora **Digital Twin**, **Sprint Planning**, **Knowledge Graph**
4. v4/v5 continuam disponíveis para pipelines detalhados

### Exemplo de pergunta

## Versão 5.0 — Delivery Copilot

### Módulos

| Módulo | Funcionalidade |
|--------|----------------|
| **M1** | Integração **Jira** — Epics, Stories, Tasks, Bugs (preview ou API real) |
| **M2** | Integração **Confluence** — BRD, specs, risk register, solution overview |
| **M3** | Integração **Azure DevOps** — User Stories, Features, Tasks |
| **M4** | Ciclo de vida — Requisito → Story → Task → Implementação → Testes |
| **M5** | Meeting Intelligence — action items, decisões, riscos, dependências |
| **M6** | Project Health Analyzer — score 0-100 + warnings |
| **M7** | Estimation Assistant — story points, complexidade, esforço |
| **M8** | Architecture Awareness — sistemas, APIs, integrações |
| **M9** | Test Scenario Generator — casos positivos, negativos, edge cases |
| **M10** | Project Knowledge Base — SQLite + Q&A persistente |
| **M11** | Executive Reporting — weekly status, risks, readiness |
| **M12** | Role-Based Views — BA, TA, PM, Executive, Scrum Master, Architect |

### Integrações Enterprise

Configura no `.env` (opcional — sem credenciais usa **modo preview**):

```env
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=...
JIRA_PROJECT_KEY=PROJ

CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_SPACE_KEY=DOCS

AZURE_DEVOPS_ORG=your-org
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_PAT=...
```

### Fluxo recomendado

1. Carrega PDFs de projeto
2. **Analyst Copilot** (v4) → requisitos, stories, riscos
3. **Delivery Intelligence** (v5) → Jira drafts, health, estimations, testes
4. **Integrações** → sincronizar (ou preview) com Jira/Confluence/Azure
5. **Knowledge Base** → perguntas sobre riscos, lacunas, decisões
6. **Role View** → dashboard adaptado ao teu perfil

---

## Versões anteriores (mantidas)

- **v4** — Analyst Copilot (10 módulos de análise)
- **v3** — Multi-documento, comparação, persistência
- **v2** — RAG conversacional
- **v1** — Resumos e OCR

---

## Arquitetura v5

```
Documentos + Reuniões
    ↓
Knowledge Layer (SQLite)
    ↓
RAG + Analysis Engine (v4)
    ↓
Delivery Engine (v5)
    ↓
Jira / Confluence / Azure DevOps
    ↓
Project Intelligence Dashboard
```

---

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Testes

```bash
pytest tests/
```

---

## API FastAPI

```bash
pip install -r requirements-api.txt
uvicorn api.main:app --reload --port 8000
```

Endpoints: `/health`, `/agents/analyze`, `/knowledge-graph/stats`, `/audit` (sem autenticação)

---

## Licença

MIT License
