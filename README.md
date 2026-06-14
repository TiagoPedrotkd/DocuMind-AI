# DocuMind AI

Plataforma de inteligência documental com IA que analisa, compara e responde a perguntas sobre múltiplos documentos de negócio simultaneamente.

**Versão 3.0** — Plataforma multi-documento com comparação, contradições, painel de insights e exportação.

---

## Funcionalidades

### Versão 3.0 (completa)
- **Upload multi-documento** — Vários PDFs na mesma sessão
- **Persistência de sessão** — Coleção, chat e análises restaurados ao reabrir a app
- **Resumos** — Por documento e da coleção completa
- **Exportação consolidada** — Relatório completo (resumos + insights + comparação + chat)
- **Comparação via chat** — Perguntas comparativas detetadas automaticamente no assistente

### Versão 2.0 (mantidas)
- RAG com LangChain + FAISS
- Embeddings Gemini ou OpenAI
- OCR para PDFs digitalizados

### Versão 1.x (mantidas)
- Extração PyMuPDF + OCR
- Resumos estruturados com IA
- Interface em português

---

## Arquitetura

```
Múltiplos PDFs
    ↓
Extração de texto (+ OCR)
    ↓
Chunking por página (1000 / 200 overlap)
    ↓
Embeddings (Gemini / OpenAI)
    ↓
Índice FAISS unificado + metadados
    ↓
Pesquisa semântica (com filtro opcional)
    ↓
GPT / Gemini
    ↓
Resposta + Fontes + Insights + Comparação
```

---

## Estrutura do projeto

```
documind-ai/
│
├── app.py
├── requirements.txt
├── .env.example
│
├── uploads/
├── vector_store/
├── documents/
├── data/
│
├── src/
│   ├── pdf_reader.py
│   ├── ocr_reader.py
│   ├── document_manager.py
│   ├── text_chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── summarizer.py
│   ├── chatbot.py
│   ├── comparison_engine.py
│   ├── insights_engine.py
│   ├── export_utils.py
│   ├── session_store.py
│   ├── question_router.py
│   ├── history.py
│   └── utils.py
│
└── README.md
```

---

## Pré-requisitos

- **Python 3.12+**
- **Chave API Gemini** (recomendado, gratuito) — [Google AI Studio](https://aistudio.google.com/apikey)
- **OpenAI API key** (opcional — alternativa à Gemini)

---

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

Configurar `.env` (Gemini — recomendado):

```env
GEMINI_API_KEY=a_tua_chave_aqui
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

---

## Executar

```bash
streamlit run app.py
```

---

## Como usar

### Barra lateral
1. Carrega um ou mais PDFs
2. Aguarda indexação (extração → chunks por página → embeddings → FAISS)
3. Gere a lista de documentos e escolhe o **âmbito de pesquisa**
4. Usa a **ferramenta de comparação** para analisar dois documentos

### Área principal
- **Resumos** — Resumo estruturado por documento ou da coleção
- **Painel de Insights** — Dashboard automático do analista
- **Comparação** — Resultados de comparação, contradições e lacunas
- **Assistente** — Chat multi-documento com comparação automática por pergunta
- **Exportar** — Relatório completo em Markdown, Word ou PDF

A sessão (documentos, chat, análises) é guardada em `documents/` e restaurada ao reiniciar a app.

### Exemplos de perguntas

- *Quais são os principais requisitos em todos os documentos?*
- *Que requisitos aparecem no BRD mas não na especificação técnica?*
- *Que integrações são mencionadas em todos os documentos?*
- *Quais são os riscos do projeto?*

---

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `GEMINI_API_KEY` | Sim* | Chave Google Gemini (chat + embeddings) |
| `GEMINI_MODEL` | Não | Modelo de chat (predefinição: `gemini-3.1-flash-lite`) |
| `GEMINI_EMBEDDING_MODEL` | Não | Embeddings (predefinição: `gemini-embedding-001`) |
| `OPENAI_API_KEY` | Sim* | Alternativa à Gemini |
| `TESSERACT_CMD` | Não | Caminho do Tesseract no Windows |

\* Pelo menos uma chave (Gemini ou OpenAI) é necessária.

---

## Stack técnica

| Componente | Tecnologia |
|------------|------------|
| Frontend | Streamlit |
| PDF | PyMuPDF + OCR (Tesseract/Gemini) |
| RAG | LangChain + FAISS |
| Embeddings | Gemini `gemini-embedding-001` ou OpenAI |
| Chat | Gemini `gemini-3.1-flash-lite` ou GPT-4.1-mini |
| Exportação | python-docx, fpdf2 |

---

## Preparado para v4.0

- Extração de requisitos
- Geração de user stories e tickets Jira
- Registos de risco
- Business Analysis Copilot
- Integração Confluence

---

## Limitações

- Índices FAISS e sessão guardados localmente em `vector_store/` e `documents/`
- OCR limitado a 20 páginas por documento
- Exportação PDF usa codificação Latin-1 (caracteres especiais podem ser substituídos)
- Comparação via chat usa heurísticas de linguagem natural (não substitui análise manual)

---

## Licença

MIT License
