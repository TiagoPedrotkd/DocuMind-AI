# DocuMind AI

Plataforma de análise de documentos com IA que transforma PDFs em resumos estruturados e acionáveis.

**Versão 1.1** — Carrega um PDF (incluindo digitalizados), obtém um resumo em português e consulta o histórico de análises anteriores.

---

## Funcionalidades

- **Upload de PDF** — Arrastar e largar ou navegar (até 25 MB)
- **Extração de texto** — PyMuPDF para PDFs com texto nativo
- **OCR para PDFs digitalizados** — Tesseract (local) ou Gemini Vision (fallback)
- **Resumos com IA** — Google Gemini (gratuito) ou OpenAI
- **Interface em português** — UI e resumos em português de Portugal
- **Histórico** — Últimas 50 análises guardadas localmente
- **Descarregar resumo** — Exportação em `.txt`

---

## Estrutura do projeto

```
documind-ai/
│
├── app.py                 # Aplicação Streamlit (UI em português)
├── requirements.txt       # Dependências Python
├── .env.example           # Modelo de variáveis de ambiente
│
├── data/                  # Histórico local (gitignored)
├── uploads/               # PDFs carregados (gitignored)
│
├── src/
│   ├── pdf_reader.py      # Extração de texto + fallback OCR
│   ├── ocr_reader.py      # OCR com Tesseract e Gemini Vision
│   ├── summarizer.py      # Resumos com Gemini ou OpenAI
│   ├── history.py         # Histórico de análises
│   └── utils.py           # Validação, configuração e utilitários
│
└── README.md
```

---

## Pré-requisitos

- **Python 3.12+**
- **Chave API Gemini** (recomendado, gratuito) — [Google AI Studio](https://aistudio.google.com/apikey)
- **Tesseract OCR** (opcional, para OCR local) — [Instalar no Windows](https://github.com/UB-Mannheim/tesseract/wiki)

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/your-org/DocuMind-AI.git
cd DocuMind-AI
```

### 2. Criar ambiente virtual

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar a chave API

```bash
cp .env.example .env
```

Editar `.env`:

```env
GEMINI_API_KEY=a_tua_chave_aqui
GEMINI_MODEL=gemini-3.1-flash-lite
```

**Modelos recomendados no plano gratuito:**

| Modelo | Pedidos/dia (típico) |
|--------|----------------------|
| `gemini-3.1-flash-lite` | 500 |
| `gemini-2.5-flash-lite` | 20 |
| `gemini-2.5-flash` | 20 |

### 5. OCR local (opcional)

Para PDFs digitalizados sem usar quota extra do Gemini:

1. Instalar [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
2. Se necessário, definir no `.env`:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

Sem Tesseract, o DocuMind usa **OCR via Gemini Vision** automaticamente.

---

## Executar a aplicação

```bash
streamlit run app.py
```

Abre em `http://localhost:8501`.

---

## Como usar

1. Carrega um PDF
2. Revê as métricas (páginas, caracteres, método de extração)
3. Clica **Gerar Resumo** (um clique de cada vez no plano gratuito)
4. Consulta o resumo ou descarrega em `.txt`
5. Acede ao **Histórico** na barra lateral para rever análises anteriores

---

## Exemplo de resumo

```
Documento: Requisitos_Projeto.pdf

Resumo Executivo:
Este documento descreve os requisitos para uma plataforma de portal do cliente.

Tópicos Principais:
- Autenticação
- Dashboard do utilizador
- Relatórios
- Notificações

Conclusões-Chave:
- Suporte mobile é obrigatório.
- Suporte multi-idioma é necessário.

Riscos ou Preocupações:
- Dependência de APIs de terceiros.
- Prazo de projeto apertado.

Ações Recomendadas:
- Validar disponibilidade das APIs.
- Priorizar implementação da autenticação.
```

---

## Métodos de extração

| Método | Quando é usado |
|--------|----------------|
| Texto nativo | PDF com texto selecionável |
| OCR local (Tesseract) | PDF digitalizado + Tesseract instalado |
| OCR via Gemini | PDF digitalizado sem Tesseract |

---

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `GEMINI_API_KEY` | Sim* | Chave API Google Gemini |
| `GEMINI_MODEL` | Não | Modelo Gemini (predefinição: `gemini-3.1-flash-lite`) |
| `TESSERACT_CMD` | Não | Caminho para o executável Tesseract |
| `OPENAI_API_KEY` | Não | Alternativa à Gemini |

\* Ou `OPENAI_API_KEY` se preferires OpenAI.

---

## Stack técnica

| Camada | Tecnologia |
|--------|------------|
| Frontend | Streamlit |
| Backend | Python 3.12+ |
| PDF | PyMuPDF |
| OCR | Tesseract + Pillow / Gemini Vision |
| IA | Google Gemini API / OpenAI |

---

## Limitações

- Apenas ficheiros PDF
- OCR limitado a 20 páginas por documento
- Histórico guardado localmente em `data/history.json` (máx. 50 entradas)
- Documentos muito grandes são truncados para caber no contexto do modelo
- Plano gratuito Gemini: respeitar limites de pedidos por minuto/dia

---

## Licença

MIT License — ver repositório para detalhes.
