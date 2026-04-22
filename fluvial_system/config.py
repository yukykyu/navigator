import os
from datetime import datetime, timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fluvial-secret-key-2024-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///fluvial.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # Configurações de tarifação
    HORARIO_DIURNO_INICIO = 5  # 05:00
    HORARIO_DIURNO_FIM = 22    # 22:00
    ACRESCIMO_NOTURNO = 0.30   # 30%
    
    # Portos padrão
    PORTOS_PADRAO = [
        'Porto Principal',
        'Porto Norte',
        'Porto Sul',
        'Porto Leste'
    ]
    
    # Categorias padrão com códigos
    CATEGORIAS_PADRAO = [
        {'codigo': '01', 'nome': 'Pedestre', 'valor_base': 5.00, 'descricao': 'Travessia de pedestre'},
        {'codigo': '02', 'nome': 'Motocicleta', 'valor_base': 12.00, 'descricao': 'Moto até 500cc'},
        {'codigo': '03', 'nome': 'Bicicleta', 'valor_base': 3.00, 'descricao': 'Travessia de bicicleta'},
        {'codigo': '10', 'nome': 'Carro de Passeio', 'valor_base': 22.00, 'descricao': 'Veículo de passeio até 5 lugares'},
        {'codigo': '11', 'nome': 'Caminhonete', 'valor_base': 28.00, 'descricao': 'Caminhonete pequena/média'},
        {'codigo': '12', 'nome': 'Van/Kombi', 'valor_base': 35.00, 'descricao': 'Van ou veículo similar'},
        {'codigo': '20', 'nome': 'Caminhão Leve', 'valor_base': 45.00, 'descricao': 'Caminhão até 3 toneladas'},
        {'codigo': '21', 'nome': 'Caminhão Pesado', 'valor_base': 65.00, 'descricao': 'Caminhão acima de 3 toneladas'},
        {'codigo': '30', 'nome': 'Ônibus', 'valor_base': 80.00, 'descricao': 'Ônibus de passageiros'},
        {'codigo': '40', 'nome': 'Carroça', 'valor_base': 10.00, 'descricao': 'Veículo de tração animal'}
    ]
    
    # Cores de veículos com códigos
    CORES_VEICULOS = [
        {'codigo': 'B', 'nome': 'Branco'},
        {'codigo': 'P', 'nome': 'Preto'},
        {'codigo': 'G', 'nome': 'Prata/Gris'},
        {'codigo': 'Z', 'nome': 'Cinza Chumbo'},
        {'codigo': 'V', 'nome': 'Vermelho'},
        {'codigo': 'A', 'nome': 'Azul'},
        {'codigo': 'M', 'nome': 'Marrom'},
        {'codigo': 'E', 'nome': 'Bege'},
        {'codigo': 'D', 'nome': 'Dourado'},
        {'codigo': 'O', 'nome': 'Laranja'},
        {'codigo': 'X', 'nome': 'Roxo/Violeta'},
        {'codigo': 'R', 'nome': 'Rosa'},
        {'codigo': 'J', 'nome': 'Amarelo'},
        {'codigo': 'K', 'nome': 'Verde'},
        {'codigo': 'I', 'nome': 'Indigo'},
        {'codigo': 'C', 'nome': 'Creme'},
        {'codigo': 'F', 'nome': 'Fosco/Preto Fosco'},
        {'codigo': 'N', 'nome': 'Azul Marinho'},
        {'codigo': 'Q', 'nome': 'Bronze'},
        {'codigo': 'T', 'nome': 'Turquesa'},
        {'codigo': 'U', 'nome': 'Outros'}
    ]
