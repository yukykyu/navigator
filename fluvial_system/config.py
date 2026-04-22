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
