# DocuMind AI

Plataforma de inteligência documental com IA que analisa, compara e gera entregáveis de analista a partir de múltiplos documentos de negócio.

**Versão 4.0** — Analyst Copilot para Business Analysts, Technical Analysts e Product Owners.

---

## Versão 4.0 — Analyst Copilot

### Módulos implementados

| Módulo | Funcionalidade |
|--------|----------------|
| **M1** | Extração e classificação de requisitos (funcional, não-funcional, regra de negócio, dependência, restrição) |
| **M2** | Geração de User Stories com critérios de aceitação |
| **M3** | Motor de análise de riscos (técnico, integração, segurança, compliance, cronograma, operacional) |
| **M4** | Deteção de ambiguidades com perguntas sugeridas |
| **M5** | Gap analysis — informação em falta |
| **M6** | Gerador de perguntas para stakeholders |
| **M7** | Resumo executivo (1 página) |
| **M8** | Dashboard do analista com métricas |
| **M9** | Matriz de rastreabilidade (requisito → documento → página → trecho) |
| **M10** | Export Center — Excel, Word, PDF, Markdown |

### Entregáveis gerados

- Catálogo de Requisitos
- User Stories + Critérios de Aceitação
- Registo de Riscos
- Relatório de Ambiguidades
- Gap Analysis Report
- Resumo Executivo
- Matriz de Rastreabilidade
- Perguntas para Entrevistas com Stakeholders

### Melhorias v4 (completas)

- Execução **módulo a módulo** ou pipeline completo com barra de progresso
- **Rastreabilidade FAISS** — documento, página e chunk reais do índice vetorial
- **Validação JSON** — normalização de categorias, prioridades e níveis de risco
- **Dashboard corrigido** — contagens funcionais vs não-funcionais separadas
- **Export Center** — Excel individual por relatório (incl. Ambiguidades)
- **Testes automatizados** — `pytest tests/`

---

## Arquitetura v4.0

```
Documentos (multi-PDF)
    ↓
Multi-Document RAG (FAISS)
    ↓
Analysis Orchestrator
    ↓
Requirements → Stories → Risks → Ambiguities → Gaps
    ↓
Stakeholder Questions → Executive Summary → Traceability
    ↓
Analyst Dashboard + Export Center
```

---

## Estrutura do projeto

```
documind-ai/
├── app.py
├── requirements.txt
├── uploads/
├── vector_store/
├── documents/
├── src/
│   ├── analyst_models.py
│   ├── analysis_base.py
│   ├── analysis_orchestrator.py
│   ├── requirements_engine.py
│   ├── story_generator.py
│   ├── risk_engine.py
│   ├── ambiguity_detector.py
│   ├── gap_engine.py
│   ├── stakeholder_questions.py
│   ├── executive_summary_engine.py
│   ├── traceability_matrix.py
│   ├── analyst_dashboard.py
│   ├── copilot_export.py
│   ├── copilot_ui.py
│   ├── document_manager.py
│   ├── comparison_engine.py
│   ├── insights_engine.py
│   ├── chatbot.py
│   └── ...
└── README.md
```

---

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configurar `.env`:

```env
GEMINI_API_KEY=a_tua_chave_aqui
GEMINI_MODEL=gemini-3.1-flash-lite
```

---

## Executar

```bash
streamlit run app.py
```

---

## Como usar o Analyst Copilot

1. Carrega PDFs (BRD, specs, contratos, etc.)
2. Vai ao separador **Analyst Copilot**
3. Clica **Executar Analyst Copilot**
4. Consulta métricas no dashboard
5. Revê entregáveis no separador **Entregáveis**
6. Exporta no **Export Center** (Excel com múltiplas folhas, Word, PDF, Markdown)

### Separadores adicionais (v3 mantidos)

- **Resumos** — resumo por documento/coleção
- **Insights** — painel de insights
- **Comparação** — análise cruzada
- **Assistente** — chat RAG com comparação automática
- **Exportar** — relatório de sessão + export copilot

---

## Stack técnica

| Componente | Tecnologia |
|------------|------------|
| Frontend | Streamlit |
| RAG | LangChain + FAISS + Gemini |
| Análise | Motores modulares + LLM estruturado (JSON) |
| Exportação | openpyxl, python-docx, fpdf2 |

---

## Preparado para v5.0

- Integração Jira / Confluence / Azure DevOps
- Estimativa de projeto
- Recomendações de arquitetura
- Solution Design Assistant

---

## Licença

MIT License
