#!/usr/bin/env python3
"""
Script para gerar dados de teste para o dashboard
"""

import requests
import json
import time
import random
from datetime import datetime

def send_detection_data():
    """Envia dados de detecção para o backend"""
    data = {
        'frame': random.randint(1, 1000),
        'class': 3,  # motorbike
        'class_name': 'motorbike',
        'confidence': round(random.uniform(0.7, 0.95), 2),
        'bbox': [
            random.randint(50, 200),
            random.randint(50, 200), 
            random.randint(250, 400),
            random.randint(250, 400)
        ],
        'area': random.randint(8000, 15000),
        'metrics': {
            'avg_fps': round(random.uniform(20, 30), 1),
            'total_detections': random.randint(1, 10),
            'unique_motos': random.randint(1, 5),
            'detection_rate': round(random.uniform(0.3, 0.8), 2)
        }
    }
    
    try:
        response = requests.post('http://localhost:5000/detections', json=data, timeout=2)
        print(f"✅ Detecção enviada: {response.status_code} - Frame {data['frame']}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar detecção: {e}")
        return False

def send_iot_sensor_data():
    """Envia dados de sensor IoT"""
    sensor_data = {
        'sensor_id': f'SENSOR_{random.randint(1, 6):02d}',
        'moto_id': f'MOTO_{random.randint(100, 999)}',
        'location': random.choice(['Vaga A1', 'Vaga B2', 'Vaga C3', 'Área Externa']),
        'is_active': random.choice([True, False]),
        'battery_level': round(random.uniform(70, 100), 1),
        'signal_strength': round(random.uniform(60, 100), 1),
        'temperature': round(random.uniform(20, 35), 1),
        'humidity': round(random.uniform(40, 80), 1),
        'vibration': round(random.uniform(0, 5), 1)
    }
    
    try:
        response = requests.post('http://localhost:5000/iot/sensor', json=sensor_data, timeout=2)
        print(f"📡 Sensor enviado: {response.status_code} - {sensor_data['sensor_id']}")
        return response.status_code == 201
    except Exception as e:
        print(f"❌ Erro ao enviar sensor: {e}")
        return False

def main():
    """Função principal"""
    print("🎯 Gerando dados de teste para o FleetZone Dashboard")
    print("=" * 50)
    
    # Gera dados por 30 segundos
    start_time = time.time()
    detection_count = 0
    sensor_count = 0
    
    while time.time() - start_time < 30:
        # Envia detecção a cada 2 segundos
        if send_detection_data():
            detection_count += 1
        
        time.sleep(1)
        
        # Envia dados IoT a cada 3 segundos
        if int(time.time()) % 3 == 0:
            if send_iot_sensor_data():
                sensor_count += 1
        
        time.sleep(1)
    
    print("\n📊 Resumo:")
    print(f"✅ Detecções enviadas: {detection_count}")
    print(f"📡 Dados IoT enviados: {sensor_count}")
    print("🌐 Verifique o dashboard em: http://localhost:5000")

if __name__ == "__main__":
    main()
