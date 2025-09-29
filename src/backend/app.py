import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fleetzone.db')

def create_app() -> Flask:
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = 'fleetzone-secret'
    return app

def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db() -> None:
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Tabela principal de detecções
    cursor.execute(
        """
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
        );
        """
    )
    
    # Tabela de alertas
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'info',
            resolved BOOLEAN DEFAULT FALSE
        );
        """
    )
    
    # Tabela de dispositivos IoT
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS iot_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            device_type TEXT NOT NULL,
            location TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_seen TEXT,
            status TEXT DEFAULT 'active',
            battery_level REAL,
            signal_strength REAL,
            temperature REAL,
            humidity REAL,
            vibration REAL,
            power_level REAL,
            last_action TEXT
        );
        """
    )
    
    # Tabela de eventos IoT
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS iot_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            processed BOOLEAN DEFAULT FALSE
        );
        """
    )
    
    connection.commit()
    connection.close()

app = create_app()
socketio = SocketIO(app, cors_allowed_origins='*')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/detections', methods=['POST'])
def detections():
    payload = request.get_json(silent=True) or {}
    
    # Extrai dados básicos
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
    
    cursor.execute(
        '''INSERT INTO detections 
           (created_at, frame, class, class_name, confidence, x1, y1, x2, y2, area, 
            fps, total_detections, unique_motos, detection_rate) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (created_at, frame, class_id, class_name, confidence, 
         bbox[0], bbox[1], bbox[2], bbox[3], area,
         fps, total_detections, unique_motos, detection_rate)
    )
    
    # Métricas são calculadas dinamicamente, não precisam ser salvas separadamente
    
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
    socketio.emit('detection', event)
    
    # Verifica alertas
    check_alerts(class_id, confidence, total_detections, unique_motos)
    
    return jsonify({'status': 'ok'}), 201

def check_alerts(class_id, confidence, total_detections, unique_motos):
    """Verifica e cria alertas baseados nos dados"""
    alerts = []
    
    # Alerta para baixa confiança
    if confidence < 0.4:
        alerts.append({
            'type': 'low_confidence',
            'message': f'Detecção com baixa confiança: {confidence:.2f}',
            'severity': 'warning'
        })
    
    # Alerta para alta confiança (moto confirmada)
    if confidence > 0.9:
        alerts.append({
            'type': 'high_confidence',
            'message': f'Moto detectada com alta confiança: {confidence:.2f}',
            'severity': 'info'
        })
    
    # Alerta para muitas detecções
    if total_detections > 20 and total_detections % 10 == 0:
        alerts.append({
            'type': 'milestone',
            'message': f'Marco atingido: {total_detections} detecções processadas',
            'severity': 'info'
        })
    
    # Alerta para sistema ativo
    if total_detections == 1:
        alerts.append({
            'type': 'system_start',
            'message': 'Sistema FleetZone iniciado - Primeira detecção registrada',
            'severity': 'info'
        })
    
    # Salva alertas
    if alerts:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        for alert in alerts:
            cursor.execute(
                '''INSERT INTO alerts (created_at, alert_type, message, severity) 
                   VALUES (?, ?, ?, ?)''',
                (datetime.utcnow().isoformat(), alert['type'], alert['message'], alert['severity'])
            )
        
        connection.commit()
        connection.close()
        
        # Emite alertas via Socket.IO
        for alert in alerts:
            socketio.emit('alert', alert)

@app.route('/metrics', methods=['GET'])
def metrics():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Métricas gerais
    cursor.execute('SELECT COUNT(*) FROM detections')
    total_events = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT class_name) FROM detections WHERE class_name IS NOT NULL')
    unique_classes = cursor.fetchone()[0]
    
    # Calcula motos únicas baseado em posição aproximada (bbox)
    cursor.execute('''
        SELECT COUNT(DISTINCT CAST(x1/50 AS INTEGER) || '_' || CAST(y1/50 AS INTEGER)) 
        FROM detections 
        WHERE class_name = 'motorbike'
    ''')
    unique_motos_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT fps FROM detections WHERE fps IS NOT NULL ORDER BY id DESC LIMIT 60')
    last_fps = [row[0] for row in cursor.fetchall()]
    avg_fps = sum(last_fps) / len(last_fps) if last_fps else 0.0
    
    # Métricas de performance
    cursor.execute('SELECT AVG(detection_rate) FROM detections WHERE detection_rate > 0')
    avg_detection_rate = cursor.fetchone()[0] or 0.0
    
    # Últimas métricas agregadas
    try:
        cursor.execute('SELECT * FROM metrics ORDER BY id DESC LIMIT 1')
        last_metrics = cursor.fetchone()
    except sqlite3.OperationalError:
        last_metrics = None
    
    # Alertas ativos
    try:
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE resolved = FALSE')
        active_alerts = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        active_alerts = 0
    
    connection.close()
    
    return jsonify({
        'total_events': total_events,
        'unique_classes': unique_classes,
        'unique_motos': unique_motos_count,
        'avg_fps_last_60': avg_fps,
        'avg_detection_rate': avg_detection_rate,
        'active_alerts': active_alerts,
        'last_metrics': dict(last_metrics) if last_metrics else None
    })

@app.route('/alerts', methods=['GET'])
def get_alerts():
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

@app.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute('UPDATE alerts SET resolved = TRUE WHERE id = ?', (alert_id,))
    connection.commit()
    connection.close()
    
    return jsonify({'status': 'ok'})

@app.route('/history', methods=['GET'])
def get_history():
    """Retorna histórico de detecções"""
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

@app.route('/iot/sensor', methods=['POST'])
def iot_sensor():
    """Endpoint para dados de sensores IoT"""
    payload = request.get_json(silent=True) or {}
    
    device_id = payload.get('sensor_id', 'unknown')
    moto_id = payload.get('moto_id', 'unknown')
    location = payload.get('location', 'unknown')
    timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
    is_active = payload.get('is_active', False)
    battery_level = payload.get('battery_level', 0.0)
    signal_strength = payload.get('signal_strength', 0.0)
    temperature = payload.get('temperature', 0.0)
    humidity = payload.get('humidity', 0.0)
    vibration = payload.get('vibration', 0.0)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Atualiza ou insere dispositivo
    cursor.execute('''
        INSERT OR REPLACE INTO iot_devices 
        (device_id, device_type, location, created_at, last_seen, status, 
         battery_level, signal_strength, temperature, humidity, vibration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (device_id, 'sensor', location, timestamp, timestamp, 
          'active' if is_active else 'idle', battery_level, signal_strength,
          temperature, humidity, vibration))
    
    # Registra evento
    event_data = {
        'moto_id': moto_id,
        'is_active': is_active,
        'battery_level': battery_level,
        'signal_strength': signal_strength,
        'temperature': temperature,
        'humidity': humidity,
        'vibration': vibration
    }
    
    cursor.execute('''
        INSERT INTO iot_events (device_id, event_type, event_data, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (device_id, 'sensor_data', json.dumps(event_data), timestamp))
    
    connection.commit()
    connection.close()
    
    # Emite evento via Socket.IO
    socketio.emit('iot_sensor', {
        'device_id': device_id,
        'moto_id': moto_id,
        'location': location,
        'is_active': is_active,
        'timestamp': timestamp,
        'battery_level': battery_level,
        'signal_strength': signal_strength
    })
    
    return jsonify({'status': 'ok'}), 201

@app.route('/iot/actuator', methods=['POST'])
def iot_actuator():
    """Endpoint para dados de atuadores IoT"""
    payload = request.get_json(silent=True) or {}
    
    device_id = payload.get('actuator_id', 'unknown')
    location = payload.get('location', 'unknown')
    timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
    status = payload.get('status', 'idle')
    last_action = payload.get('last_action')
    power_level = payload.get('power_level', 0.0)
    temperature = payload.get('temperature', 0.0)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Atualiza ou insere dispositivo
    cursor.execute('''
        INSERT OR REPLACE INTO iot_devices 
        (device_id, device_type, location, created_at, last_seen, status, 
         power_level, temperature, last_action)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (device_id, 'actuator', location, timestamp, timestamp, status,
          power_level, temperature, last_action))
    
    # Registra evento
    event_data = {
        'status': status,
        'last_action': last_action,
        'power_level': power_level,
        'temperature': temperature
    }
    
    cursor.execute('''
        INSERT INTO iot_events (device_id, event_type, event_data, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (device_id, 'actuator_data', json.dumps(event_data), timestamp))
    
    connection.commit()
    connection.close()
    
    # Emite evento via Socket.IO
    socketio.emit('iot_actuator', {
        'device_id': device_id,
        'location': location,
        'status': status,
        'timestamp': timestamp,
        'power_level': power_level
    })
    
    return jsonify({'status': 'ok'}), 201

@app.route('/iot/devices', methods=['GET'])
def get_iot_devices():
    """Retorna status de todos os dispositivos IoT"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT * FROM iot_devices 
        ORDER BY device_type, device_id
    ''')
    
    devices = [dict(row) for row in cursor.fetchall()]
    connection.close()
    
    return jsonify(devices)

@app.route('/iot/events', methods=['GET'])
def get_iot_events():
    """Retorna eventos IoT recentes"""
    limit = request.args.get('limit', 50, type=int)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT * FROM iot_events 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    events = [dict(row) for row in cursor.fetchall()]
    connection.close()
    
    return jsonify(events)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)


