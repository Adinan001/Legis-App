# Legis — Sistema de Gestão Jurídica
## Guia de Instalação e Uso (Windows)

---

### PRÉ-REQUISITO
- Python 3.10 ou superior instalado
  → Download: https://www.python.org/downloads/
  → Durante a instalação, marque "Add Python to PATH"

---

### INSTALAÇÃO (apenas uma vez)

1. Abra o **Prompt de Comando** (cmd) ou **PowerShell**
2. Navegue até a pasta do projeto:
   ```
   cd C:\Caminho\Para\Legis
   ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

---

### EXECUTAR O SISTEMA

```
python main.py
```

Ou clique duas vezes no arquivo `main.py` (se o Python estiver associado a .py no Windows).

---

### ESTRUTURA DO PROJETO

```
Legis/
├── main.py               ← Ponto de entrada
├── config.py             ← Configurações globais e paleta de cores
├── requirements.txt      ← Dependências
├── legis.db              ← Banco de dados SQLite (criado automaticamente)
├── core/
│   └── database.py       ← Toda a lógica de acesso a dados
└── ui/
    ├── widgets.py         ← Componentes reutilizáveis
    ├── main_window.py     ← Janela principal e navegação
    ├── dashboard_page.py  ← Painel de visão geral
    ├── processos_page.py  ← Gestão de processos
    ├── clientes_page.py   ← Cadastro de clientes
    ├── financeiro_page.py ← Fluxo de caixa
    ├── agenda_page.py     ← Agenda e prazos
    ├── documentos_page.py ← Modelos e documentos
    ├── jurisprudencia_page.py ← Banco de jurisprudência
    ├── consulta_datajud_page.py ← Consulta CNJ online
    └── configuracoes_page.py   ← Dados do escritório
```

---

### MÓDULOS DISPONÍVEIS

| Módulo              | Função                                                    |
|---------------------|-----------------------------------------------------------|
| Dashboard           | Visão geral: processos, clientes, saldo e prazos          |
| Processos           | CRUD completo com filtro e status colorido                |
| Proc. Automáticos   | Consulta online ao CNJ via DataJud                        |
| Clientes            | Cadastro de PF e PJ com e-mail e endereço                 |
| Financeiro          | Lançamentos de receitas e despesas com saldo              |
| Agenda & Prazos     | Compromissos com tipo, vínculo ao processo e status       |
| Documentos          | Modelos e petições com pré-visualização                   |
| Jurisprudência      | Banco organizado por área → tema → acórdão com ementa     |
| Configurações       | Dados do escritório exibidos no sistema                   |

---

### BACKUP DO BANCO DE DADOS

O banco `legis.db` fica na pasta do projeto. Para fazer backup,
basta copiar esse arquivo para outro local.

---

Desenvolvido como ferramenta de apoio à prática jurídica.
