from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Usuario, Porto, CategoriaVeiculo, Empresa, ConfigTarifacao, Venda
from datetime import datetime, timedelta
import os
import cv2
import numpy as np
import pytesseract
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def ler_placa_imagem(image_path):
    """Realiza OCR na imagem para extrair a placa"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Aplicar threshold para melhorar contraste
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Configurar tesseract para placas brasileiras
        config_tesseract = r'--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        # Realizar OCR
        texto = pytesseract.image_to_string(thresh, config=config_tesseract, lang='por')
        
        # Limpar resultado e buscar padrão de placa
        texto = texto.upper().replace(' ', '').replace('\n', '')
        
        # Padrão Mercosul: LLLNLNN ou antigo LLLNNN
        import re
        padrao = re.compile(r'[A-Z]{3}[0-9][A-Z0-9][0-9]{2}')
        match = padrao.search(texto)
        
        if match:
            return match.group()
        
        # Tentar padrão antigo
        padrao_antigo = re.compile(r'[A-Z]{3}[0-9]{4}')
        match_antigo = padrao_antigo.search(texto)
        
        if match_antigo:
            return match_antigo.group()
        
        return texto[:8] if len(texto) >= 7 else None
    except Exception as e:
        print(f"Erro ao ler placa: {e}")
        return None

def calcular_valor_com_acrescimo(categoria_id, data_hora=None):
    """Calcula o valor com acréscimo noturno se aplicável"""
    if data_hora is None:
        data_hora = datetime.now()
    
    categoria = CategoriaVeiculo.query.get(categoria_id)
    if not categoria:
        return None, None
    
    valor_base = categoria.valor_base
    hora_atual = data_hora.hour
    minuto_atual = data_hora.minute
    
    # Verificar se está no horário noturno (22:01 às 04:59)
    percentual_acrescimo = 0.0
    
    # Horário noturno: das 22:01 até 04:59
    if hora_atual >= 22 or hora_atual < 5:
        percentual_acrescimo = Config.ACRESCIMO_NOTURNO
    elif hora_atual == 5 and minuto_atual > 0:
        # Das 05:01 em diante já é diurno
        pass
    elif hora_atual == 22 and minuto_atual == 0:
        # Exatamente 22:00 ainda é diurno
        pass
    
    # Verificar configurações específicas de tarifação
    configs = ConfigTarifacao.query.filter_by(
        categoria_id=categoria_id, 
        ativo=True
    ).all()
    
    for config in configs:
        if config.hora_inicio <= hora_atual < config.hora_fim:
            percentual_acrescimo = config.percentual_acrescimo
            break
        # Caso especial para horários que cruzam a meia-noite
        elif config.hora_inicio > config.hora_fim:
            if hora_atual >= config.hora_inicio or hora_atual < config.hora_fim:
                percentual_acrescimo = config.percentual_acrescimo
                break
    
    valor_final = valor_base * (1 + percentual_acrescimo)
    return valor_base, valor_final, percentual_acrescimo

# Rotas de Autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        lembrar = request.form.get('lembrar') == 'on'
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.verificar_senha(senha) and usuario.ativo:
            login_user(usuario, remember=lembrar)
            proxima_pagina = request.args.get('next')
            return redirect(proxima_pagina) if proxima_pagina else redirect(url_for('index'))
        
        flash('E-mail ou senha inválidos.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard Principal
@app.route('/')
@login_required
def index():
    # Dados do dashboard em tempo real
    hoje = datetime.now().date()
    
    # Vendas do dia
    vendas_hoje = Venda.query.filter(
        db.func.date(Venda.data_venda) == hoje
    ).all()
    
    total_vendas_hoje = sum(v.valor_final for v in vendas_hoje)
    quantidade_vendas_hoje = len(vendas_hoje)
    
    # Vendas por porto
    portos = Porto.query.filter_by(ativo=True).all()
    vendas_por_porto = []
    for porto in portos:
        vendas_porto = Venda.query.filter_by(porto_id=porto.id).filter(
            db.func.date(Venda.data_venda) == hoje
        ).all()
        total_porto = sum(v.valor_final for v in vendas_porto)
        vendas_por_porto.append({
            'nome': porto.nome,
            'total': total_porto,
            'quantidade': len(vendas_porto)
        })
    
    # Top operadores
    usuarios = Usuario.query.filter_by(ativo=True).all()
    top_operadores = []
    for usuario in usuarios:
        vendas_usuario = Venda.query.filter_by(usuario_id=usuario.id).filter(
            db.func.date(Venda.data_venda) == hoje
        ).all()
        total_usuario = sum(v.valor_final for v in vendas_usuario)
        if total_usuario > 0:
            top_operadores.append({
                'nome': usuario.nome,
                'total': total_usuario,
                'quantidade': len(vendas_usuario)
            })
    
    top_operadores.sort(key=lambda x: x['total'], reverse=True)
    top_operadores = top_operadores[:5]
    
    # Vendas por categoria
    categorias = CategoriaVeiculo.query.filter_by(ativo=True).all()
    vendas_por_categoria = []
    for categoria in categorias:
        vendas_cat = Venda.query.filter_by(categoria_id=categoria.id).filter(
            db.func.date(Venda.data_venda) == hoje
        ).all()
        total_cat = sum(v.valor_final for v in vendas_cat)
        vendas_por_categoria.append({
            'nome': categoria.nome,
            'total': total_cat,
            'quantidade': len(vendas_cat)
        })
    
    return render_template('index.html',
                         total_vendas_hoje=total_vendas_hoje,
                         quantidade_vendas_hoje=quantidade_vendas_hoje,
                         vendas_por_porto=vendas_por_porto,
                         top_operadores=top_operadores,
                         vendas_por_categoria=vendas_por_categoria)

# Tela de Atendimento
@app.route('/atendimento', methods=['GET', 'POST'])
@login_required
def atendimento():
    if request.method == 'POST':
        placa = request.form.get('placa', '').upper().strip()
        cor_veiculo = request.form.get('cor_veiculo', '').strip()
        categoria_id = request.form.get('categoria_id', type=int)
        porto_id = request.form.get('porto_id', type=int)
        empresa_id = request.form.get('empresa_id', type=int)
        pago = request.form.get('pago') == 'on'
        observacoes = request.form.get('observacoes', '')
        
        if not categoria_id or not porto_id:
            flash('Categoria e porto são obrigatórios.', 'error')
            return redirect(url_for('atendimento'))
        
        valor_base, valor_final, percentual_acrescimo = calcular_valor_com_acrescimo(categoria_id)
        
        if valor_final is None:
            flash('Erro ao calcular valor.', 'error')
            return redirect(url_for('atendimento'))
        
        venda = Venda(
            placa=placa if placa else None,
            cor_veiculo=cor_veiculo if cor_veiculo else None,
            categoria_id=categoria_id,
            porto_id=porto_id,
            usuario_id=current_user.id,
            empresa_id=empresa_id if empresa_id else None,
            valor_base=valor_base,
            percentual_acrescimo=percentual_acrescimo,
            valor_final=valor_final,
            pago=pago,
            observacoes=observacoes
        )
        
        db.session.add(venda)
        db.session.commit()
        
        flash(f'Vendida registrada com sucesso! Valor: R$ {valor_final:.2f}', 'success')
        return redirect(url_for('atendimento'))
    
    categorias = CategoriaVeiculo.query.filter_by(ativo=True).order_by(CategoriaVeiculo.codigo).all()
    portos = Porto.query.filter_by(ativo=True).order_by(Porto.nome).all()
    empresas = Empresa.query.filter_by(ativo=True).order_by(Empresa.nome_fantasia).all()
    cores = Config.CORES_VEICULOS
    
    return render_template('atendimento.html', categorias=categorias, portos=portos, empresas=empresas, cores=cores)

# Upload e leitura de placa
@app.route('/upload_placa', methods=['POST'])
@login_required
def upload_placa():
    if 'imagem' not in request.files:
        return jsonify({'erro': 'Nenhuma imagem enviada'}), 400
    
    arquivo = request.files['imagem']
    
    if arquivo.filename == '':
        return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400
    
    if arquivo and allowed_file(arquivo.filename):
        filename = secure_filename(arquivo.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        arquivo.save(filepath)
        
        placa = ler_placa_imagem(filepath)
        
        # Remover arquivo após processamento
        try:
            os.remove(filepath)
        except:
            pass
        
        if placa:
            return jsonify({'placa': placa, 'sucesso': True})
        else:
            return jsonify({'erro': 'Não foi possível ler a placa', 'sucesso': False}), 400
    
    return jsonify({'erro': 'Formato de arquivo não permitido'}), 400

# Cadastros
@app.route('/cadastro/<tipo>', methods=['GET', 'POST'])
@login_required
def cadastro(tipo):
    if request.method == 'POST':
        if tipo == 'categoria':
            nome = request.form.get('nome')
            valor_base = request.form.get('valor_base', type=float)
            descricao = request.form.get('descricao', '')
            
            if not nome or not valor_base:
                flash('Nome e valor base são obrigatórios.', 'error')
                return redirect(url_for('cadastro', tipo='categoria'))
            
            categoria = CategoriaVeiculo(
                nome=nome,
                valor_base=valor_base,
                descricao=descricao
            )
            db.session.add(categoria)
            db.session.commit()
            flash('Categoria cadastrada com sucesso!', 'success')
        
        elif tipo == 'porto':
            nome = request.form.get('nome')
            
            if not nome:
                flash('Nome é obrigatório.', 'error')
                return redirect(url_for('cadastro', tipo='porto'))
            
            porto = Porto(nome=nome)
            db.session.add(porto)
            db.session.commit()
            flash('Porto cadastrado com sucesso!', 'success')
        
        elif tipo == 'empresa':
            razao_social = request.form.get('razao_social')
            nome_fantasia = request.form.get('nome_fantasia')
            cnpj = request.form.get('cnpj')
            tipo_faturamento = request.form.get('tipo_faturamento')
            
            if not razao_social:
                flash('Razão social é obrigatória.', 'error')
                return redirect(url_for('cadastro', tipo='empresa'))
            
            empresa = Empresa(
                razao_social=razao_social,
                nome_fantasia=nome_fantasia,
                cnpj=cnpj,
                tipo_faturamento=tipo_faturamento
            )
            db.session.add(empresa)
            db.session.commit()
            flash('Empresa cadastrada com sucesso!', 'success')
        
        elif tipo == 'usuario':
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')
            
            if not nome or not email or not senha:
                flash('Todos os campos são obrigatórios.', 'error')
                return redirect(url_for('cadastro', tipo='usuario'))
            
            if Usuario.query.filter_by(email=email).first():
                flash('E-mail já cadastrado.', 'error')
                return redirect(url_for('cadastro', tipo='usuario'))
            
            usuario = Usuario(nome=nome, email=email)
            usuario.set_senha(senha)
            db.session.add(usuario)
            db.session.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
        
        return redirect(url_for('cadastro', tipo=tipo))
    
    # GET - mostrar formulário
    if tipo == 'categoria':
        itens = CategoriaVeiculo.query.order_by(CategoriaVeiculo.nome).all()
    elif tipo == 'porto':
        itens = Porto.query.order_by(Porto.nome).all()
    elif tipo == 'empresa':
        itens = Empresa.query.order_by(Empresa.nome_fantasia).all()
    elif tipo == 'usuario':
        itens = Usuario.query.order_by(Usuario.nome).all()
    else:
        flash('Tipo de cadastro inválido.', 'error')
        return redirect(url_for('index'))
    
    return render_template('cadastro.html', tipo=tipo, itens=itens)

# Relatórios
@app.route('/relatorios', methods=['GET', 'POST'])
@login_required
def relatorios():
    if request.method == 'POST':
        data_inicio = request.form.get('data_inicio')
        data_fim = request.form.get('data_fim')
        porto_id = request.form.get('porto_id', type=int)
        usuario_id = request.form.get('usuario_id', type=int)
        categoria_id = request.form.get('categoria_id', type=int)
        
        query = Venda.query
        
        if data_inicio:
            query = query.filter(db.func.date(Venda.data_venda) >= data_inicio)
        if data_fim:
            query = query.filter(db.func.date(Venda.data_venda) <= data_fim)
        if porto_id:
            query = query.filter_by(porto_id=porto_id)
        if usuario_id:
            query = query.filter_by(usuario_id=usuario_id)
        if categoria_id:
            query = query.filter_by(categoria_id=categoria_id)
        
        vendas = query.order_by(Venda.data_venda.desc()).all()
        
        # Totais
        total_vendas = sum(v.valor_final for v in vendas)
        total_quantidade = len(vendas)
        
        # Agrupar por operador
        por_operador = {}
        for venda in vendas:
            operador_nome = venda.operador.nome
            if operador_nome not in por_operador:
                por_operador[operador_nome] = {'total': 0, 'quantidade': 0}
            por_operador[operador_nome]['total'] += venda.valor_final
            por_operador[operador_nome]['quantidade'] += 1
        
        return render_template('relatorios.html',
                             vendas=vendas,
                             total_vendas=total_vendas,
                             total_quantidade=total_quantidade,
                             por_operador=por_operador,
                             filtros=request.form)
    
    portos = Porto.query.filter_by(ativo=True).order_by(Porto.nome).all()
    usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
    categorias = CategoriaVeiculo.query.filter_by(ativo=True).order_by(CategoriaVeiculo.nome).all()
    
    return render_template('relatorios.html', portos=portos, usuarios=usuarios, categorias=categorias, vendas=None)

# API para dados em tempo real
@app.route('/api/dashboard')
@login_required
def api_dashboard():
    hoje = datetime.now().date()
    
    vendas_hoje = Venda.query.filter(
        db.func.date(Venda.data_venda) == hoje
    ).all()
    
    total = sum(v.valor_final for v in vendas_hoje)
    quantidade = len(vendas_hoje)
    
    return jsonify({
        'total_vendas': total,
        'quantidade_vendas': quantidade,
        'timestamp': datetime.now().isoformat()
    })

# API para buscar categoria por código ou nome
@app.route('/api/buscar_categoria')
@login_required
def api_buscar_categoria():
    termo = request.args.get('termo', '').strip().upper()
    
    if not termo:
        return jsonify([])
    
    # Buscar por código exato primeiro
    categoria = CategoriaVeiculo.query.filter_by(codigo=termo, ativo=True).first()
    if categoria:
        return jsonify([{
            'id': categoria.id,
            'codigo': categoria.codigo,
            'nome': categoria.nome,
            'valor_base': categoria.valor_base
        }])
    
    # Buscar por nome parcial
    categorias = CategoriaVeiculo.query.filter(
        CategoriaVeiculo.nome.ilike(f'%{termo}%'),
        CategoriaVeiculo.ativo == True
    ).limit(10).all()
    
    resultado = [{
        'id': cat.id,
        'codigo': cat.codigo,
        'nome': cat.nome,
        'valor_base': cat.valor_base
    } for cat in categorias]
    
    return jsonify(resultado)

# API para listar todas as categorias
@app.route('/api/listar_categorias')
@login_required
def api_listar_categorias():
    categorias = CategoriaVeiculo.query.filter_by(ativo=True).order_by(CategoriaVeiculo.codigo).all()
    return jsonify([{
        'id': cat.id,
        'codigo': cat.codigo,
        'nome': cat.nome,
        'valor_base': cat.valor_base
    } for cat in categorias])

# Inicialização do banco
def criar_banco():
    with app.app_context():
        db.create_all()
        
        # Criar usuário admin padrão se não existir
        if not Usuario.query.filter_by(email='admin@fluvial.com').first():
            admin = Usuario(
                nome='Administrador',
                email='admin@fluvial.com'
            )
            admin.set_senha('admin123')
            db.session.add(admin)
            
            # Criar portos padrão
            for nome_porto in Config.PORTOS_PADRAO:
                porto = Porto(nome=nome_porto)
                db.session.add(porto)
            
            # Criar categorias padrão com códigos
            for cat_data in Config.CATEGORIAS_PADRAO:
                categoria = CategoriaVeiculo(
                    codigo=cat_data['codigo'],
                    nome=cat_data['nome'],
                    valor_base=cat_data['valor_base'],
                    descricao=cat_data['descricao']
                )
                db.session.add(categoria)
            
            db.session.commit()
            print("Banco de dados inicializado com dados padrão!")

if __name__ == '__main__':
    # Criar pasta de uploads se não existir
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Criar banco de dados
    criar_banco()
    
    # Rodar aplicação
    app.run(host='0.0.0.0', port=5000, debug=False)
