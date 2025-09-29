#!/usr/bin/env python3
"""
Backend Ultra Simplificado do FleetZone
Versão mínima para demonstração
"""

import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
import json

# Configuração
DB_PATH = 'fleetzone.db'
app = Flask(__name__, static_folder='static')

def get_db_connection():
    """Conecta ao banco de dados"""
    try:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        return connection
    except Exception as e:
        print(f"Erro ao conectar banco: {e}")
        return None

def init_db():
    """Inicializa o banco de dados"""
    try:
        connection = get_db_connection()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Tabela de detecções
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                frame INTEGER,
                class INTEGER,
                class_name TEXT,
                confidence REAL,
                x1 INTEGER,
                y1 INTEGER,
                x2 INTEGER,
                y2 INTEGER,
                area INTEGER,
                fps REAL,
                total_detections INTEGER,
                unique_motos INTEGER,
                detection_rate REAL
            )
        ''')
        
        connection.commit()
        connection.close()
        print("✅ Banco de dados inicializado!")
        return True
    except Exception as e:
        print(f"Erro ao inicializar banco: {e}")
        return False

@app.route('/')
def index():
    """Página principal"""
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        return f"Erro ao carregar página: {e}", 500

@app.route('/detections', methods=['POST'])
def detections():
    """Recebe dados de detecção"""
    try:
        payload = request.get_json(silent=True) or {}
        
        # Dados básicos
        frame = int(payload.get('frame', 0))
        class_id = int(payload.get('class', -1))
        class_name = payload.get('class_name', 'unknown')
        confidence = float(payload.get('confidence', 0.0))
        bbox = payload.get('bbox', [0, 0, 0, 0])
        area = int(payload.get('area', 0))
        
        # Métricas
        metrics = payload.get('metrics', {})
        fps = float(metrics.get('avg_fps', 0.0))
        total_detections = int(metrics.get('total_detections', 0))
        unique_motos = int(metrics.get('unique_motos', 0))
        detection_rate = float(metrics.get('detection_rate', 0.0))
        
        created_at = datetime.utcnow().isoformat()
        
        # Salva no banco
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            cursor.execute('''
                INSERT INTO detections 
                (created_at, frame, class, class_name, confidence, x1, y1, x2, y2, area, 
                 fps, total_detections, unique_motos, detection_rate) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (created_at, frame, class_id, class_name, confidence, 
                  bbox[0], bbox[1], bbox[2], bbox[3], area,
                  fps, total_detections, unique_motos, detection_rate))
            
            connection.commit()
            connection.close()
        
        return jsonify({'status': 'ok'}), 201
        
    except Exception as e:
        print(f"Erro ao processar detecção: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    """Retorna métricas do sistema"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = connection.cursor()
        
        # Métricas básicas
        cursor.execute('SELECT COUNT(*) FROM detections')
        total_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT class) FROM detections WHERE class >= 0')
        unique_classes = cursor.fetchone()[0]
        
        cursor.execute('SELECT fps FROM detections ORDER BY id DESC LIMIT 60')
        last_fps = [row[0] for row in cursor.fetchall()]
        avg_fps = sum(last_fps) / len(last_fps) if last_fps else 0.0
        
        cursor.execute('SELECT AVG(detection_rate) FROM detections WHERE detection_rate > 0')
        avg_detection_rate = cursor.fetchone()[0] or 0.0
        
        connection.close()
        
        return jsonify({
            'total_events': total_events,
            'unique_classes': unique_classes,
            'avg_fps_last_60': avg_fps,
            'avg_detection_rate': avg_detection_rate,
            'active_alerts': 0
        })
        
    except Exception as e:
        print(f"Erro ao buscar métricas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Retorna histórico de detecções"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = connection.cursor()
        
        cursor.execute('''
            SELECT * FROM detections 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        history = [dict(row) for row in cursor.fetchall()]
        connection.close()
        
        return jsonify(history)
        
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Retorna alertas (vazio por enquanto)"""
    return jsonify([])

@app.route('/static/<path:path>')
def send_static(path):
    """Serve arquivos estáticos"""
    try:
        return send_from_directory(app.static_folder, path)
    except Exception as e:
        return f"Erro ao servir arquivo: {e}", 500

if __name__ == '__main__':
    print("🚀 Iniciando FleetZone Backend...")
    
    if init_db():
        print("🌐 Servidor rodando em http://localhost:5000")
        print("📊 Dashboard disponível em http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        print("❌ Erro ao inicializar banco de dados")
