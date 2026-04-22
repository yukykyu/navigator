# Sistema de Gestão de Travessia Fluvial

## Visão Geral
Aplicação web moderna, leve e eficiente para gestão operacional e financeira de empresas de travessia fluvial.

## Tecnologias Utilizadas

### Backend
- **Python 3.x** - Linguagem principal
- **Flask** - Framework web leve e rápido
- **SQLite** - Banco de dados (pode migrar para PostgreSQL em produção)
- **OpenCV + pytesseract** - Leitura automática de placas (OCR)

### Frontend
- **HTML5/CSS3/JavaScript** - Nativo, sem necessidade de frameworks pesados
- **Bootstrap 5** - Responsividade e design moderno
- **Chart.js** - Gráficos e dashboards
- **html5-qrcode** - Leitura de placas via câmera do navegador

## Requisitos do Sistema

### Servidor
- Ubuntu Server 20.04 ou superior
- 2GB RAM mínimo
- 20GB armazenamento
- Python 3.8+
- Nginx (opcional para produção)

### Navegadores Suportados
- Google Chrome (recomendado)
- Mozilla Firefox
- Microsoft Edge
- Safari
- Opera

## Instalação

### 1. Instalar dependências do sistema
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y tesseract-ocr libtesseract-dev
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y nginx sqlite3
```

### 2. Configurar ambiente virtual
```bash
cd /opt/fluvial_system
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências Python
```bash
pip install flask flask-sqlalchemy flask-login werkzeug opencv-python-headless pytesseract pillow pandas
```

### 4. Configurar serviço systemd
```bash
sudo nano /etc/systemd/system/fluvial.service
```

Conteúdo do arquivo:
```ini
[Unit]
Description=Fluvial Ferry System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/fluvial_system
Environment="PATH=/opt/fluvial_system/venv/bin"
ExecStart=/opt/fluvial_system/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Iniciar serviço
```bash
sudo systemctl daemon-reload
sudo systemctl enable fluvial
sudo systemctl start fluvial
sudo systemctl status fluvial
```

### 6. Configurar Nginx (opcional)
```bash
sudo nano /etc/nginx/sites-available/fluvial
```

```nginx
server {
    listen 80;
    server_name seu_dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /opt/fluvial_system/static;
        expires 30d;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/fluvial /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Funcionalidades

### 1. Leitura Automática de Placas
- Via câmera do dispositivo (webcam, smartphone, tablet)
- Via upload de imagem
- OCR com pytesseract otimizado para placas brasileiras

### 2. Cadastro de Categorias
- Carro de passeio
- Caminhonete
- Caminhão
- Moto
- Pedestre
- Cargas especiais
- Valores configuráveis por categoria

### 3. Empresas para Faturamento
- Cadastro de empresas
- Opções de pagamento: quinzenal ou mensal
- Histórico de travessias por empresa

### 4. Tarifação Dinâmica
- Configuração de horários com valores diferenciados
- Acréscimo noturno automático (ex: 30% das 22h às 05h)
- Valores específicos por data/hora

### 5. Dashboard em Tempo Real
- Vendas por porto de travessia
- Totalizadores diários, semanais, mensais
- Ranking de operadores por volume de vendas
- Gráficos interativos

### 6. Relatórios
- Por período personalizado
- Por operador
- Por categoria de veículo
- Por empresa faturada
- Exportação em CSV/PDF

## Estrutura de Arquivos

```
fluvial_system/
├── app.py                 # Aplicação principal
├── models.py              # Modelos do banco de dados
├── requirements.txt       # Dependências Python
├── config.py              # Configurações do sistema
├── static/
│   ├── css/
│   │   └── style.css      # Estilos personalizados
│   ├── js/
│   │   ├── main.js        # Scripts principais
│   │   └── ocr.js         # Leitura de placas
│   └── uploads/           # Imagens temporárias
└── templates/
    ├── base.html          # Template base
    ├── index.html         # Dashboard
    ├── atendimento.html   # Tela de atendimento
    ├── cadastro.html      # Cadastros diversos
    ├── relatorios.html    # Relatórios
    └── login.html         # Login
```

## Segurança

- Autenticação de usuários
- Senhas criptografadas (werkzeug.security)
- Proteção CSRF
- Sessions seguras
- Controle de acesso por nível de usuário

## Licenças

- **Python**: PSF License (gratuita)
- **Flask**: BSD License (gratuita)
- **SQLite**: Public Domain (gratuita)
- **Bootstrap**: MIT License (gratuita)
- **Chart.js**: MIT License (gratuita)
- **Tesseract**: Apache 2.0 (gratuita)
- **OpenCV**: Apache 2.0 (gratuita)

## Custo Estimado de Infraestrutura

- Servidor VPS Ubuntu (2GB RAM, 20GB SSD): R$ 30-50/mês
- Domínio: R$ 40/ano
- **Total mensal estimado**: R$ 35-55/mês

## Suporte e Manutenção

- Logs em `/var/log/fluvial/`
- Backup automático do banco SQLite
- Atualizações via git pull
- Monitoramento via systemctl

## Contato

Sistema desenvolvido sob licença free/open-source para máxima economia e flexibilidade.
