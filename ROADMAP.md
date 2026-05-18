## Estratégia ideal
Uma abordagem em camadas:
```
1. Infraestrutura
2. Modelagem
3. Backend core
4. Frontend core
5. Integração
6. Conceitos de SO
7. Relatórios
8. Refinamento
9. Documentação
```

## Arquitetura

### Frontend (vanilla)
- `HTML`, `CSS`, `JS`
- `Bootstrap`, `Axio`

### Backend (python)
- `threading`, `asyncio`, `queue`
- `os`, `pathlib`, `platform`, `shutil`
- `logging`, `RotatingFileHandler`
- `SQLAlchemy`, `SQLite`
- `FastAPI`, `Uvicorn`

## 1. Setup

- organizar estrutura backend
- configurar FastAPI
- configurar CORS
---
- organizar estrutura frontend
- criar layout base
- roteamento funcionando

## 2. Modelagem de Dados

- entidades
    - patient
    - doctor
    - appointment
- criar models SQLAlchemy
- configurar SQLite
---
- tabela de pacientes
- tabela de médicos
- garantir navegação básica

## 3. CRUD Completo

- patient (POST, GET, PUT, DELETE)
- doctor (POST, GET, PUT, DELETE)
- appointment (POST, GET, PUT, DELETE)
---
- patient (list, form, edit)
- doctor (list, form)
- appointment (agendamento)
> IA deve trabalhar aqui endpoint por endpoint ⚠️

## 4. Regras de Negócio

- impedir médico com dois horários iguais
- impedir paciente duplicado no mesmo horário
- horários válidos
---
- mensagens de erro
- loading

## 5. Conceitos de S.O. ⚠️💥💀

- lock de agendamento
- explicação no relatório
- threads para gerar relatórios, backup etc
- sistema de arquivos logs, backups, reports, cache etc
- detectar S.O. paths
- logging
- cache

## 6. Relatórios

- pdf (consulta por médico)
- csv (export geral)
---
- tela de relatórios


## O que documentar continuamente

- concorrência
    - locks, threads, async
- sistema de arquivos
    - backups, logs, diretórios
- syscalls
    - paths, permissões, platform API
- memória
    - cache, limpeza
