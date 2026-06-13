# DocuMind AI

Plataforma de análise de documentos com IA que transforma PDFs em resumos estruturados e respostas conversacionais baseadas no conteúdo do documento (RAG).

**Versão 2.0** — Assistente conversacional com LangChain, FAISS e Gemini/OpenAI.

---

## Funcionalidades

### Versão 1.x (mantidas)
- Upload e validação de PDF
- Extração de texto (PyMuPDF) com OCR para digitalizados
- Resumos estruturados com IA
- Interface em português
- Histórico de resumos

### Versão 2.0 (novas)
- **RAG** — Respostas baseadas apenas no documento carregado
- **Chunking** — 1000 caracteres, overlap 200
- **Embeddings** — Gemini `gemini-embedding-001` ou OpenAI `text-embedding-3-small`
- **Vector store** — FAISS com pesquisa semântica
- **Chat conversacional** — Perguntas em linguagem natural
- **Fontes** — Trechos do documento usados em cada resposta
- **Perguntas sugeridas** — Geradas automaticamente

---

## Arquitetura RAG

```
PDF Upload
    ↓
Text Extraction (+ OCR se necessário)
    ↓
Chunking (1000 / 200 overlap)
    ↓
Gemini/OpenAI Embeddings
    ↓
FAISS Vector Store
    ↓
Pergunta do utilizador
    ↓
Similarity Search (top-K chunks)
    ↓
Gemini / GPT
    ↓
Resposta + Fontes
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
├── data/
│
├── src/
│   ├── pdf_reader.py
│   ├── ocr_reader.py
│   ├── text_chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── summarizer.py
│   ├── chatbot.py
│   ├── history.py
│   └── utils.py
│
└── README.md
```

---

## Pré-requisitos

- **Python 3.12+**
- **OpenAI API key** (opcional — só necessária se não usares Gemini)
- **Chave API Gemini** (recomendado, gratuito) — [Google AI Studio](https://aistudio.google.com/apikey)

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

Alternativa com OpenAI:

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

## Executar

```bash
streamlit run app.py
```

---

## Como usar

### Barra lateral
1. Carrega um PDF
2. Aguarda indexação (extração → chunks → embeddings → FAISS)
3. Vê páginas, chunks e método de extração
4. Clica **Gerar Resumo**

### Área principal
- **Resumo** — Resumo executivo estruturado
- **Assistente** — Chat sobre o documento com fontes
- **Texto extraído** — Conteúdo completo extraído

### Exemplo de chat

**Utilizador:** Qual é o prazo do projeto?

**Assistente:** De acordo com o documento, a fase de implementação deve estar concluída até dezembro de 2026.

**Fontes:** Trecho 3, Trecho 7

---

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `GEMINI_API_KEY` | Sim* | Chave Google Gemini (chat + embeddings + resumos) |
| `GEMINI_MODEL` | Não | Modelo de chat (predefinição: `gemini-3.1-flash-lite`) |
| `GEMINI_EMBEDDING_MODEL` | Não | Modelo de embeddings (predefinição: `gemini-embedding-001`) |
| `OPENAI_API_KEY` | Sim* | Alternativa à Gemini para RAG |
| `TESSERACT_CMD` | Não | Caminho do Tesseract no Windows |

---

## Stack técnica

| Componente | Tecnologia |
|------------|------------|
| Frontend | Streamlit |
| PDF | PyMuPDF + OCR (Tesseract/Gemini) |
| Chunking | Módulo custom `text_chunker.py` |
| Embeddings | LangChain + Gemini ou OpenAI |
| Vector DB | FAISS (LangChain Community) |
| Chat RAG | LangChain + Gemini ou OpenAI |
| Resumos | Gemini ou OpenAI |

---

## Preparado para v3.0

A arquitetura modular suporta futuras extensões:

- Múltiplos PDFs por sessão
- Comparação entre documentos
- Base de conhecimento persistente
- Autenticação de utilizadores
- Analyst Copilot

---

## Limitações

- Um PDF ativo por sessão
- RAG funciona com **Gemini (grátis)** ou OpenAI — prefere Gemini se ambas estiverem definidas
- OCR limitado a 20 páginas
- Índices FAISS guardados localmente em `vector_store/`

---

## Licença

MIT License
