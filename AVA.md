# Sistema de Agendamento de Consultas Médicas - CRUD

## Descrição do Projeto

Desenvolva um sistema completo de agendamento de consultas médicas que
implemente e demonstre os principais conceitos de Sistemas Operacionais. O sistema deve permitir o cadastro de pacientes, agendamento de consultas, geração de relatórios e operar com dependência direta do sistema operacional subjacente.

Duração: 2 semanas `(27/05)` \
Modalidade: Individual ou em duplas \
Entrega: Código fonte + relatório técnico + apresentação

## Objetivos de Aprendizado

- Aplicar conceitos teóricos de Sistemas Operacionais em um projeto real
- Compreender a interação entre software e sistema operacional
- Desenvolver habilidades de programação concorrente e manipulação de arquivos
- Vivenciar desafios de desenvolvimento dependente de plataforma

## Funcionalidades Requisitadas

### 1. Sistema de Agendamento Básico
🔹 Conceitos de SO: Processos e Threads
- Interface para agendamento de consultas (web, desktop)
- Controle de pacientes e médicos -CRUD
- Controle de horários disponíveis - CRUD
- Verificação de conflitos de agendamento

### 2. Persistência de Dados em Arquivos Locais ou Banco de Dados
🔹 Conceitos de SO: Sistema de Arquivos
- Armazenamento de consultas em arquivos JSON/XML/CSV
- Criação de estrutura de diretórios específica por SO
- Backup automático dos dados
- Leitura/Escrita assíncrona de arquivos

### 3. Geração de Relatórios
🔹 Conceitos de SO: Operações de I/O
- Geração de relatórios em PDF/CSV
- Salvamento em diretórios específicos do usuário
- Download de relatórios gerados
- Formatação dependente do sistema de arquivos

### 4. Processamento Concorrente
🔹 Conceitos de SO: Escalonamento e Concorrência
- Processamento assíncrono de agendamentos
- Múltiplas threads para operações de I/O
- Controle de concorrência no acesso aos arquivos
- Sincronização entre processos

### 5. Sistema de Logging
🔹 Conceitos de SO: Gerência de Dispositivos
- Registro de todas as operações em arquivo de log
- Timestamp com fuso horário do sistema
- Rotação de logs (opcional)
- Níveis de log (INFO, ERROR, DEBUG)

### 6. Gerenciamento de Memória
🔹 Conceitos de SO: Gerência de Memória
- Cache de consultas frequentes
- Limpeza automática de dados temporários
- Alocação dinâmica de estruturas de dados
- Controle de vazamento de memória


### 7. Configuração Dependente de SO
🔹 Conceitos de SO: Chamadas de Sistema
    - Paths diferentes para Windows, Linux e macOS
    - Permissões de arquivo adequadas por SO
    - Encoding de arquivos específico
    - Tratamento de diferenças de filesystem

## Estrutura Esperada do Projeto
```
sistema_agendamento/
├── src/
│ ├── core/                 # Lógica principal
│ ├── storage/              # Operações de arquivo  🔹 SO: Sistema de Arquivos
│ ├── concurrent/           # Processos e threads   🔹 SO: Concorrência
│ ├── reports/              # Geração de relatórios 🔹 SO: I/O
│ └── config/               # Configuração por SO   🔹 SO: Chamadas de Sistema
├── data/
│ ├── consultas/            # Dados das consultas
│ ├── relatorios/           # Relatórios gerados
│ └── logs/                 # Arquivos de log
├── docs/
│ └── relatorio_tecnico.pdf # Documentação
└── README.md
```

## Critérios de Avaliação

### Funcionalidade (40%)
- Sistema de agendamento funciona corretamente
- Persistência em arquivos locais ou banco de dados
- Geração de relatórios
- Interface utilizável

### Conceitos de SO (40%)
- Implementação correta de processos/threads 🔹 SO: Concorrência
- Manipulação adequada de arquivos 🔹 SO: Sistema de Arquivos
- Gerenciamento de memória eficiente 🔹 SO: Memória
- Configuração específica por SO🔹 SO: Chamadas de Sistema

### Qualidade do Código (10%)
- Organização e documentação
- Tratamento de erros
- Boas práticas de programação

### Relatório Técnico (10%)
- Explicação das implementações de SO
- Análise de decisões técnicas
- Demonstração de funcionamento

## Conceitos de SO a Serem Demonstrados

## Entrega
Cada grupo deve explicar no relatório como implementou:
1. 🔹 Processos e Threads: Como o sistema lida com múltiplas operações
simultâneas?
2. 🔹 Sistema de Arquivos: Como os dados são organizados e acessados?
3. 🔹 Gerência de Memória: Como a memória é alocada e liberada?
4. 🔹 Concorrência: Como são evitados conflitos no acesso aos recursos?
5. 🔹 Chamadas de Sistema: Quais APIs do SO são utilizadas?
6. 🔹 Entrada/Saída: Como são realizadas as operações de leitura/escrita?

### Prazo: 2 semanas a partir da data de publicação

### Itens para Entrega:
1. Relatório Técnico (PDF) contendo:
    - Explicação das funcionalidades
    - Detalhamento das implementações de SO
    - Capturas de tela do sistema funcionando
    - Dificuldades encontradas e soluções
2. Manual de Instalação e Uso
3. Apresentação (5-10 minutos) demonstrando:
    - Funcionalidades principais
    - Implementações específicas de SO
    - Diferenciais do projeto

