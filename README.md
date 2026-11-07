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
* **boto3** - SDK AWS para armazenamento S3-compatível

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

## ☁️ Sistema de Armazenamento (S3 + Local Fallback)

O Nuvemhost utiliza um sistema de armazenamento unificado que suporta:

### **Produção: S3-Compatible Storage**
- **AWS S3** - `https://s3.amazonaws.com`
- **MinIO** - `http://localhost:9000` (auto-hospedado)
- **DigitalOcean Spaces** - `https://nyc3.digitaloceanspaces.com`
- **Vultr Object Storage** - `https://ewr1.vultrobjects.com`
- **Cloudflare R2** - `https://<account-id>.r2.cloudflarestorage.com`
- **Backblaze B2** - `https://s3.us-west-000.backblazeb2.com`
- Qualquer serviço compatível com API S3

### **Desenvolvimento: Local Filesystem**
- Fallback automático quando S3 não configurado
- Armazena em `UPLOAD_FOLDER` (padrão: `./uploads`)
- Mesma API, zero mudança de código

### **Recursos do Storage**
- ✅ **Stream direto** - Zero uso de disco temporário em produção
- ✅ **Bucket auto-criado** - Na primeira execução
- ✅ **Path traversal protection** - Em S3 e local
- ✅ **MIME type detection** - Para serving correto
- ✅ **Presigned URLs** - Acesso temporário seguro (S3)
- ✅ **Operações atômicas** - Upload/Delete consistentes

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

Crie um arquivo `.env` na raiz do projeto (baseie-se no `.env.example`):

```bash
# Flask
DEBUG=True
SECRET_KEY=uma_chave_muito_secreta

# Banco de dados
DB_HOST=localhost
DB_USER=seu_usuario
DB_PASS=sua_senha
DB_NAME=project_hosting

# Armazenamento Local (fallback / desenvolvimento)
UPLOAD_FOLDER=./uploads
ALLOWED_EXTENSIONS=["zip"]
ALLOWED_PROJECT_FILES=["html", "css", "js", "png", "jpg", "jpeg", "gif", "svg", "ico", "txt", "md", "json"]

# ☁️ S3 Storage (OBRIGATÓRIO para produção)
# Suporta: AWS S3, MinIO, DigitalOcean Spaces, Vultr, Cloudflare R2, Backblaze B2, etc.
S3_ENDPOINT=https://s3.amazonaws.com          # Ex: http://localhost:9000 (MinIO)
S3_ACCESS_KEY=seu_access_key
S3_SECRET_KEY=sua_secret_key
S3_BUCKET=seu-bucket-name
S3_REGION=us-east-1
S3_USE_SSL=true

# Email (Zoho SMTP)
SMTP_SERVER=smtp.zoho.com
SMTP_PORT=587
SMTP_USER=seu_email@dominio.com
SMTP_PASS=sua_senha_email

# Logs
LOG_FILE=flask.log
```

> ⚠️ **Nunca commite o arquivo `.env`** - Adicione ao `.gitignore`

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
│── s3.py                       # Módulo de armazenamento (S3 + Local)
│── requirements.txt            # Dependências do Python
│── database.sql                # Schema do banco de dados
│── migration_add_status.sql    # Migração para coluna status
│── .env                        # Variáveis de ambiente (não versionar)
│── .env.example                # Exemplo de configuração
│── .gitignore                  # Arquivos ignorados pelo Git
│── uploads/                    # Pasta de uploads local (fallback)
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
  - **Verde** = Ativo
  - **Vermelho** = Pausado
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