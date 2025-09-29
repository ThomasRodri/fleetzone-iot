#!/usr/bin/env python3
"""
Backend API - API REST para o FleetZone
Módulo de backend simplificado
"""

import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
import json

class FleetZoneAPI:
    """API REST para o FleetZone"""
    
    def __init__(self, db_path='fleetzone.db'):
        self.app = Flask(__name__, static_folder='static')
        self.db_path = db_path
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura rotas da API"""
        
        @self.app.route('/')
        def index():
            return send_from_directory(self.app.static_folder, 'index.html')
        
        @self.app.route('/api/detections', methods=['POST'])
        def detections():
            try:
                payload = request.get_json(silent=True) or {}
                
                # Dados básicos
                frame = int(payload.get('frame', 0))
                class_name = payload.get('class_name', 'unknown')
                confidence = float(payload.get('confidence', 0.0))
                bbox = payload.get('bbox', [0, 0, 0, 0])
                fps = float(payload.get('fps', 0.0))
                
                # Salva no banco
                self._save_detection(frame, class_name, confidence, bbox, fps)
                
                return jsonify({'status': 'ok'}), 201
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/metrics', methods=['GET'])
        def metrics():
            try:
                stats = self._get_statistics()
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/history', methods=['GET'])
        def history():
            try:
                limit = request.args.get('limit', 100, type=int)
                history = self._get_history(limit)
                return jsonify(history)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/static/<path:path>')
        def send_static(path):
            return send_from_directory(self.app.static_folder, path)
    
    def _save_detection(self, frame, class_name, confidence, bbox, fps):
        """Salva detecção no banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO detections (timestamp, frame, class_name, confidence, bbox, fps)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), frame, class_name, confidence, str(bbox), fps))
        
        conn.commit()
        conn.close()
    
    def _get_statistics(self):
        """Retorna estatísticas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM detections')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT class_name) FROM detections')
        classes = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(fps) FROM detections')
        avg_fps = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_events': total,
            'unique_classes': classes,
            'avg_fps_last_60': avg_fps,
            'avg_detection_rate': 0,
            'active_alerts': 0
        }
    
    def _get_history(self, limit):
        """Retorna histórico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM detections 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return history
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Executa a API"""
        print(f"🚀 Iniciando FleetZone API em http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Função principal para executar a API"""
    api = FleetZoneAPI()
    api.run()

if __name__ == "__main__":
    main()
