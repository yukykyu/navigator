from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com vendas
    vendas = db.relationship('Venda', backref='operador', lazy='dynamic')
    
    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)
    
    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Porto(db.Model):
    __tablename__ = 'portos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com vendas
    vendas = db.relationship('Venda', backref='porto', lazy='dynamic')


class CategoriaVeiculo(db.Model):
    __tablename__ = 'categorias_veiculos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)  # Código numérico rápido (ex: 10, 01, 09)
    nome = db.Column(db.String(100), nullable=False)
    valor_base = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com vendas
    vendas = db.relationship('Venda', backref='categoria', lazy='dynamic')


class Empresa(db.Model):
    __tablename__ = 'empresas'
    
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(200), nullable=False)
    nome_fantasia = db.Column(db.String(100))
    cnpj = db.Column(db.String(20), unique=True)
    tipo_faturamento = db.Column(db.String(20))  # 'quinzenal' ou 'mensal'
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com vendas
    vendas = db.relationship('Venda', backref='empresa', lazy='dynamic')


class ConfigTarifacao(db.Model):
    __tablename__ = 'config_tarifacao'
    
    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_veiculos.id'), nullable=False)
    hora_inicio = db.Column(db.Integer, nullable=False)  # 0-23
    minuto_inicio = db.Column(db.Integer, default=0)  # 0-59
    hora_fim = db.Column(db.Integer, nullable=False)  # 0-23
    minuto_fim = db.Column(db.Integer, default=0)  # 0-59
    percentual_acrescimo = db.Column(db.Float, default=0.0)
    ativo = db.Column(db.Boolean, default=True)
    descricao = db.Column(db.String(200))
    
    categoria = db.relationship('CategoriaVeiculo', backref='configs_tarifacao')


class Venda(db.Model):
    __tablename__ = 'vendas'
    
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(20))
    cor_veiculo = db.Column(db.String(50))  # Cor do veículo
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_veiculos.id'), nullable=False)
    porto_id = db.Column(db.Integer, db.ForeignKey('portos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'))
    
    valor_base = db.Column(db.Float, nullable=False)
    percentual_acrescimo = db.Column(db.Float, default=0.0)
    valor_final = db.Column(db.Float, nullable=False)
    
    pago = db.Column(db.Boolean, default=True)  # False para faturamento
    data_venda = db.Column(db.DateTime, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    
    @property
    def valor_total_formatado(self):
        return f"R$ {self.valor_final:.2f}".replace('.', ',')
