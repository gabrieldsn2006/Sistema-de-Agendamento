# Sistema de Agendamento de Consultas Médicas

API REST para agendamento de consultas médicas com foco em conceitos de Sistemas Operacionais.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Banco de dados | SQLAlchemy + SQLite |
| Concorrência | threading, asyncio, queue |
| Logging | logging + RotatingFileHandler |
| SO | os, pathlib, platform, shutil |

## Estrutura

```
sistema_agendamento/
├── src/
│   ├── main.py               # App FastAPI + CORS
│   ├── config/
│   │   ├── settings.py       # Configurações + detecção de SO
│   │   └── logger.py         # Logging com rotação de arquivos
│   ├── core/                 # Lógica de negócio (próxima etapa)
│   ├── storage/              # Operações de arquivo (próxima etapa)
│   ├── concurrent/           # Threads e locks (etapa SO)
│   └── reports/              # Geração de PDF/CSV (etapa relatórios)
├── data/
│   ├── consultas/            # Dados JSON de backup
│   ├── relatorios/           # PDFs e CSVs gerados
│   ├── logs/                 # agendamento.log (rotacionado)
│   ├── backups/              # Backups automáticos
│   └── cache/                # Cache em memória/disco
├── docs/
├── run.py                    # Ponto de entrada
└── requirements.txt
```

## Instalação

```bash
# 1. Criar ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Iniciar servidor
python run.py
```

## Endpoints disponíveis

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Status da API |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI (automático) |

## Conceitos de SO implementados

- **Chamadas de Sistema**: `platform.system()` detecta o SO; paths e permissões ajustados por plataforma (`os.chmod`)
- **Sistema de Arquivos**: criação automática de diretórios `data/` com `pathlib.Path.mkdir`
- **Gerência de Dispositivos**: logging com `RotatingFileHandler` — rotação automática ao atingir 5 MB, mantendo 3 backups
