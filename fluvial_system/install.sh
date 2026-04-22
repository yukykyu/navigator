#!/bin/bash
# Script de Instalação Automatizada - Fluvial System
# Sistema de Gestão de Travessia Fluvial

set -e

echo "=============================================="
echo "  FLUVIAL SYSTEM - Instalação Automatizada"
echo "=============================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
    log_error "Por favor, execute como root (use sudo)"
    exit 1
fi

# Diretório de instalação
INSTALL_DIR="/opt/fluvial_system"
SERVICE_NAME="fluvial"

log_info "Iniciando instalação do Fluvial System..."

# 1. Atualizar sistema
log_info "Atualizando pacotes do sistema..."
apt-get update -qq

# 2. Instalar dependências do sistema
log_info "Instalando dependências do sistema..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    nginx \
    curl \
    wget \
    git > /dev/null 2>&1

# Instalar Tesseract OCR (para leitura de placas)
log_info "Instalando Tesseract OCR..."
apt-get install -y -qq \
    tesseract-ocr \
    libtesseract-dev \
    libopencv-dev \
    python3-opencv > /dev/null 2>&1

# 3. Criar diretório de instalação
log_info "Criando diretório de instalação..."
mkdir -p $INSTALL_DIR

# 4. Copiar arquivos da aplicação
log_info "Copiando arquivos da aplicação..."
cp -r /workspace/fluvial_system/* $INSTALL_DIR/

# 5. Criar ambiente virtual Python
log_info "Criando ambiente virtual Python..."
cd $INSTALL_DIR
python3 -m venv venv

# 6. Ativar ambiente virtual e instalar dependências
log_info "Instalando dependências Python..."
source $INSTALL_DIR/venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 7. Configurar permissões
log_info "Configurando permissões..."
chown -R www-data:www-data $INSTALL_DIR
chmod +x $INSTALL_DIR/app.py

# 8. Criar arquivo de ambiente
log_info "Criando arquivo de configuração..."
cat > $INSTALL_DIR/.env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///$INSTALL_DIR/instance/fluvial.db
FLASK_ENV=production
EOF

# 9. Criar serviço systemd
log_info "Configurando serviço systemd..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Fluvial Ferry System
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 10. Configurar Nginx
log_info "Configurando Nginx..."
cat > /etc/nginx/sites-available/fluvial << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/fluvial_system/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

ln -sf /etc/nginx/sites-available/fluvial /etc/nginx/sites-enabled/fluvial
rm -f /etc/nginx/sites-enabled/default

# Testar configuração do Nginx
nginx -t > /dev/null 2>&1

# 11. Iniciar serviços
log_info "Iniciando serviços..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
systemctl enable nginx
systemctl restart nginx

# 12. Aguardar inicialização
sleep 5

# 13. Verificar status
log_info "Verificando status dos serviços..."

if systemctl is-active --quiet $SERVICE_NAME; then
    log_info "Serviço Fluvial: ${GREEN}ATIVO${NC}"
else
    log_error "Serviço Fluvial: ${RED}INATIVO${NC}"
fi

if systemctl is-active --quiet nginx; then
    log_info "Nginx: ${GREEN}ATIVO${NC}"
else
    log_warn "Nginx: ${YELLOW}INATIVO${NC}"
fi

# 14. Mostrar informações de acesso
echo ""
echo "=============================================="
echo -e "${GREEN}  INSTALAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
echo "=============================================="
echo ""
echo "Acesso ao sistema:"
echo "  URL: http://$(hostname -I | awk '{print $1}' || echo 'SEU_IP')/"
echo ""
echo "Credenciais padrão:"
echo "  E-mail: admin@fluvial.com"
echo "  Senha: admin123"
echo ""
echo "Comandos úteis:"
echo "  Ver status:    sudo systemctl status $SERVICE_NAME"
echo "  Reiniciar:     sudo systemctl restart $SERVICE_NAME"
echo "  Parar:         sudo systemctl stop $SERVICE_NAME"
echo "  Logs:          sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "=============================================="

# Desativar modo debug na aplicação de produção
sed -i "s/debug=False/debug=True/" $INSTALL_DIR/app.py

log_info "Instalação finalizada!"
