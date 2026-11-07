# 🚀 Flask Hosting Project - Nuvemhost

Um sistema de hospedagem de projetos web usando **Flask + MySQL**.
Permite gerenciar uploads de projetos (ZIP), extrair arquivos e servir conteúdos de forma organizada.

---

## 📌 Tecnologias utilizadas

* **Flask** - Framework web em Python
* **MySQL Connector** - Conexão com banco de dados MySQL
* **bcrypt** - Criptografia de senhas
* **python-dotenv** - Carregar variáveis de ambiente
* **Werkzeug** - Utilitários para upload seguro
* **Logging** - Logs rotativos do servidor
* **Bootstrap 5** - Interface responsiva
* **Bootstrap Icons** - Ícones

---

## ✨ Funcionalidades

- **Autenticação**: Registro e login seguro com bcrypt
- **Dashboard**: Visualização de todos os projetos do usuário
- **Upload de projetos**: Aceita arquivos ZIP (máx. 10MB)
- **Limite de projetos**: Máximo 3 projetos por usuário
- **Editor de código**: Edição de arquivos HTML/CSS/JS no navegador
- **Visualização pública**: Projetos acessíveis via URL única
- **Pausar/Reativar projetos**: Controle de status com indicador visual
- **Tema Dark/Light**: Suporte a tema escuro/claro
- **PWA**: Service Worker para funcionamento offline

---

## 📋 Requisitos

- Python 3.10+
- MySQL/MariaDB
- pip

---

## Configuração do projeto

### 1️ Clonar repositório

```
git clone https://github.com/MrDiogoMilhomem/Nuvemhost.git
cd Nuvemhost
```

### 2️ Criar ambiente virtual

```
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3️ Instalar dependências

```
pip install -r requirements.txt
```

### 4️ Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```
DEBUG=True
SECRET_KEY=uma_chave_muito_secreta

# Banco de dados
DB_USER=*Coloque*
DB_PASS=*Coloque*
DB_HOST=localhost
DB_NAME=project_hosting

# Uploads e Logs
UPLOAD_FOLDER="/root/flaskhostingg/uploads"
ALLOWED_EXTENSIONS=["zip"]
ALLOWED_PROJECT_FILES=["html", "css", "js", "png", "jpg", "jpeg", "gif", "svg", "ico", "txt", "md", "json"]
LOG_FILE="flask.log"
```

### 5️ Inicializar banco de dados

```sql
-- Execute o arquivo database.sql no MySQL
mysql -u root -p < database.sql
```

Para bancos existentes, execute a migração:
```sql
mysql -u root -p project_hosting < migration_add_status.sql
```

---

## ▶️ Executar a aplicação

```
python app.py
```

Por padrão, a aplicação roda em:

```
http://127.0.0.1:5000
```

---

## 📂 Estrutura do projeto

```
Nuvemhost/
│── app.py                      # Arquivo principal da aplicação Flask
│── requirements.txt            # Dependências do Python
│── database.sql                # Schema do banco de dados
│── migration_add_status.sql    # Migração para coluna status
│── .env                        # Variáveis de ambiente (não versionar)
│── .gitignore                  # Arquivos ignorados pelo Git
│── uploads/                    # Pasta de uploads (ignorada no Git)
│── templates/                  # Templates HTML
│   ├── base.html               # Template base
│   ├── index.html              # Página inicial
│   ├── login.html              # Login
│   ├── register.html           # Registro
│   ├── dashboard.html          # Dashboard do usuário
│   ├── upload.html             # Upload de projeto
│   ├── edit_project.html       # Editor de código
│   ├── paused.html             # Página de projeto pausado
│   ├── 404.html                # Erro 404
│   └── 500.html                # Erro 500
│── static/
│   ├── css/
│   │   └── styles.css          # Estilos customizados
│   ├── js/
│   │   ├── base.js             # JS comum (tema, alerts)
│   │   ├── dashboard.js        # JS do dashboard
│   │   ├── upload.js           # JS de upload
│   │   ├── register.js         # JS de registro
│   │   └── service-worker.js   # Service Worker (PWA)
│   └── images/
│       └── favicon.png
```

---

## 🔧 Como usar

1. **Registre-se** em `/register`
2. **Faça login** em `/login`
3. No **Dashboard**, clique em "New Project"
4. Faça upload de um arquivo `.zip` contendo seu projeto (deve ter `index.html`)
5. Acesse seu projeto em `/project/<project_id>/`
6. Use o menu **⋮** (três pontos) no card do projeto para:
   - **View Project** - Abrir projeto
   - **Edit Code** - Editar arquivos
   - **Copy URL** - Copiar link público
   - **Pause/Reactivate** - Pausar ou reativar o projeto
   - **Delete** - Excluir projeto

---

## 🎨 Interface

- **Tema**: Suporte a Dark/Light mode (persistido no localStorage)
- **Cards de projeto**: Mostram nome, data, botões de ação
- **Indicador de status**: Bolinha colorida no canto superior direito
  - 🟢 **Verde** = Ativo
  - 🔴 **Vermelho** = Pausado
- **Dropdown de ações**: Menu acessível via três pontos
- **Responsivo**: Funciona em mobile, tablet e desktop

---

## Segurança

* Nunca faça commit do arquivo `.env`
* Senhas são criptografadas com `bcrypt`
* Uploads permitidos são validados pela extensão
* Validação de path traversal em extração de ZIP
* Arquivos servidos validados por extensão permitida
* Sessões protegidas com `SECRET_KEY`
* Proteção CSRF via SameSite cookies

Consulte [SECURITY.md](SECURITY.md) para detalhes completos.

---

## Logs

Logs são gravados em arquivo rotativo (configurado via `LOG_FILE`):
- Acessos HTTP
- Erros de aplicação
- Operações de banco de dados
- Uploads e exclusões

---

## Licença

Este projeto é open-source e distribuído sob os termos da [GPL-2.0](LICENSE).