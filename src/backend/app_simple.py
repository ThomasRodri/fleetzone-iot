#!/usr/bin/env python3
"""
Backend Simplificado do FleetZone
Versão otimizada para demonstração
"""

import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import json

# Configuração
DB_PATH = 'fleetzone.db'
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'fleetzone-secret'
socketio = SocketIO(app, cors_allowed_origins='*')

def get_db_connection():
    """Conecta ao banco de dados"""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    """Inicializa o banco de dados"""
    connection = get_db_connection()
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
    
    # Tabela de alertas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'info',
            resolved BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Tabela de métricas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            total_detections INTEGER,
            unique_motos INTEGER,
            avg_fps REAL,
            detection_rate REAL,
            session_duration REAL
        )
    ''')
    
    connection.commit()
    connection.close()
    print("✅ Banco de dados inicializado!")

@app.route('/')
def index():
    """Página principal"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/detections', methods=['POST'])
def detections():
    """Recebe dados de detecção"""
    try:
        payload = request.get_json(silent=True) or {}
        
        # Extrai dados
        frame = int(payload.get('frame', 0))
        class_id = int(payload.get('class', -1))
        class_name = payload.get('class_name', 'unknown')
        confidence = float(payload.get('confidence', 0.0))
        bbox = payload.get('bbox', [0, 0, 0, 0])
        area = int(payload.get('area', 0))
        
        # Extrai métricas
        metrics = payload.get('metrics', {})
        fps = float(metrics.get('avg_fps', 0.0))
        total_detections = int(metrics.get('total_detections', 0))
        unique_motos = int(metrics.get('unique_motos', 0))
        detection_rate = float(metrics.get('detection_rate', 0.0))
        
        created_at = datetime.utcnow().isoformat()
        
        # Salva no banco
        connection = get_db_connection()
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
        
        # Prepara evento para Socket.IO
        event = {
            'created_at': created_at,
            'frame': frame,
            'class': class_id,
            'class_name': class_name,
            'confidence': confidence,
            'bbox': bbox,
            'area': area,
            'fps': fps,
            'total_detections': total_detections,
            'unique_motos': unique_motos,
            'detection_rate': detection_rate
        }
        
        # Emite evento em tempo real
        socketio.emit('detection', event, broadcast=True)
        
        return jsonify({'status': 'ok'}), 201
        
    except Exception as e:
        print(f"❌ Erro ao processar detecção: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    """Retorna métricas do sistema"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Métricas gerais
        cursor.execute('SELECT COUNT(*) FROM detections')
        total_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT class) FROM detections WHERE class >= 0')
        unique_classes = cursor.fetchone()[0]
        
        cursor.execute('SELECT fps FROM detections ORDER BY id DESC LIMIT 60')
        last_fps = [row[0] for row in cursor.fetchall()]
        avg_fps = sum(last_fps) / len(last_fps) if last_fps else 0.0
        
        cursor.execute('SELECT AVG(detection_rate) FROM detections WHERE detection_rate > 0')
        avg_detection_rate = cursor.fetchone()[0] or 0.0
        
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE resolved = FALSE')
        active_alerts = cursor.fetchone()[0]
        
        connection.close()
        
        return jsonify({
            'total_events': total_events,
            'unique_classes': unique_classes,
            'avg_fps_last_60': avg_fps,
            'avg_detection_rate': avg_detection_rate,
            'active_alerts': active_alerts
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar métricas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Retorna alertas ativos"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute('''
            SELECT * FROM alerts 
            WHERE resolved = FALSE 
            ORDER BY created_at DESC 
            LIMIT 20
        ''')
        
        alerts = [dict(row) for row in cursor.fetchall()]
        connection.close()
        
        return jsonify(alerts)
        
    except Exception as e:
        print(f"❌ Erro ao buscar alertas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    """Retorna histórico de detecções"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        connection = get_db_connection()
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
        print(f"❌ Erro ao buscar histórico: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:path>')
def send_static(path):
    """Serve arquivos estáticos"""
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    print("🚀 Iniciando FleetZone Backend...")
    init_db()
    print("🌐 Servidor rodando em http://localhost:5000")
    print("📊 Dashboard disponível em http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
