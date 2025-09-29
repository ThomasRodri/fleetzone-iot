#!/usr/bin/env python3
"""
SensorSimulator - Simulador de sensores IoT
Simula sensores de motos para o sistema VisionMoto
"""

import random
import time
import json
import threading
import requests
from datetime import datetime
from typing import Dict, List

class MotoSensor:
    """Sensor individual de moto"""
    
    def __init__(self, sensor_id: str, location: str, moto_id: str = None):
        self.sensor_id = sensor_id
        self.location = location
        self.moto_id = moto_id or f"MOTO_{sensor_id}"
        self.is_active = False
        self.last_seen = None
        self.battery_level = random.randint(80, 100)
        self.signal_strength = random.randint(70, 100)
        
    def generate_data(self) -> Dict:
        """Gera dados simulados do sensor"""
        now = datetime.now()
        
        # Simula detecção de moto (70% de chance)
        detected = random.random() < 0.7
        
        if detected:
            self.is_active = True
            self.last_seen = now.isoformat()
            self.battery_level = max(0, self.battery_level - random.uniform(0.1, 0.5))
            self.signal_strength = max(0, self.signal_strength - random.uniform(0.5, 2.0))
        else:
            self.is_active = False
        
        return {
            'sensor_id': self.sensor_id,
            'moto_id': self.moto_id,
            'location': self.location,
            'timestamp': now.isoformat(),
            'is_active': self.is_active,
            'last_seen': self.last_seen,
            'battery_level': round(self.battery_level, 1),
            'signal_strength': round(self.signal_strength, 1),
            'temperature': round(random.uniform(20, 35), 1),
            'humidity': round(random.uniform(40, 80), 1),
            'vibration': round(random.uniform(0, 10), 2) if self.is_active else 0.0
        }

class IoTActuator:
    """Atuador IoT para controle de motos"""
    
    def __init__(self, actuator_id: str, location: str):
        self.actuator_id = actuator_id
        self.location = location
        self.status = "idle"  # idle, locking, unlocking, alarm
        self.last_action = None
        
    def generate_data(self) -> Dict:
        """Gera dados do atuador"""
        now = datetime.now()
        
        # Simula ações do atuador
        if random.random() < 0.1:  # 10% chance de ação
            actions = ["locking", "unlocking", "alarm"]
            self.status = random.choice(actions)
            self.last_action = now.isoformat()
        elif random.random() < 0.05:  # 5% chance de voltar ao idle
            self.status = "idle"
        
        return {
            'actuator_id': self.actuator_id,
            'location': self.location,
            'timestamp': now.isoformat(),
            'status': self.status,
            'last_action': self.last_action,
            'power_level': round(random.uniform(85, 100), 1),
            'temperature': round(random.uniform(25, 40), 1)
        }

class IoTDeviceSimulator:
    """Simulador principal de dispositivos IoT"""
    
    def __init__(self, api_url: str = "http://localhost:5000"):
        self.api_url = api_url
        self.sensors: List[MotoSensor] = []
        self.actuators: List[IoTActuator] = []
        self.running = False
        self.threads = []
        
        # Cria dispositivos simulados
        self._create_devices()
        
    def _create_devices(self):
        """Cria dispositivos IoT simulados"""
        locations = [
            "Estacionamento A - Vaga 1",
            "Estacionamento A - Vaga 2", 
            "Estacionamento B - Vaga 1",
            "Estacionamento B - Vaga 2",
            "Entrada Principal",
            "Saída de Emergência"
        ]
        
        # Cria 6 sensores
        for i in range(6):
            sensor = MotoSensor(
                sensor_id=f"SENSOR_{i+1:02d}",
                location=locations[i],
                moto_id=f"MOTO_{i+1:03d}"
            )
            self.sensors.append(sensor)
        
        # Cria 3 atuadores
        for i in range(3):
            actuator = IoTActuator(
                actuator_id=f"ACTUATOR_{i+1:02d}",
                location=locations[i*2]  # Um atuador para cada 2 sensores
            )
            self.actuators.append(actuator)
    
    def _send_sensor_data(self, sensor: MotoSensor):
        """Envia dados do sensor para a API"""
        try:
            data = sensor.generate_data()
            response = requests.post(f"{self.api_url}/iot/sensor", 
                                  json=data, timeout=2)
            if response.status_code == 201:
                print(f"📡 Sensor {sensor.sensor_id}: Moto {'detectada' if data['is_active'] else 'não detectada'}")
        except requests.exceptions.RequestException:
            pass  # Falha silenciosa
    
    def _send_actuator_data(self, actuator: IoTActuator):
        """Envia dados do atuador para a API"""
        try:
            data = actuator.generate_data()
            response = requests.post(f"{self.api_url}/iot/actuator", 
                                  json=data, timeout=2)
            if response.status_code == 201:
                print(f"🔧 Atuador {actuator.actuator_id}: {data['status']}")
        except requests.exceptions.RequestException:
            pass  # Falha silenciosa
    
    def _simulate_sensor(self, sensor: MotoSensor):
        """Simula um sensor individual"""
        while self.running:
            self._send_sensor_data(sensor)
            time.sleep(random.uniform(2, 5))  # Intervalo aleatório entre 2-5s
    
    def _simulate_actuator(self, actuator: IoTActuator):
        """Simula um atuador individual"""
        while self.running:
            self._send_actuator_data(actuator)
            time.sleep(random.uniform(5, 10))  # Intervalo aleatório entre 5-10s
    
    def start_simulation(self):
        """Inicia a simulação IoT"""
        print("🚀 Iniciando simulação IoT...")
        print(f"📊 {len(self.sensors)} sensores e {len(self.actuators)} atuadores")
        
        self.running = True
        
        # Inicia threads para sensores
        for sensor in self.sensors:
            thread = threading.Thread(target=self._simulate_sensor, args=(sensor,), daemon=True)
            thread.start()
            self.threads.append(thread)
        
        # Inicia threads para atuadores
        for actuator in self.actuators:
            thread = threading.Thread(target=self._simulate_actuator, args=(actuator,), daemon=True)
            thread.start()
            self.threads.append(thread)
        
        print("✅ Simulação IoT iniciada!")
    
    def stop_simulation(self):
        """Para a simulação IoT"""
        print("🛑 Parando simulação IoT...")
        self.running = False
        
        # Aguarda threads terminarem
        for thread in self.threads:
            thread.join(timeout=1)
        
        print("✅ Simulação IoT parada!")
    
    def get_device_status(self) -> Dict:
        """Retorna status de todos os dispositivos"""
        return {
            'sensors': [{
                'id': s.sensor_id,
                'location': s.location,
                'moto_id': s.moto_id,
                'is_active': s.is_active,
                'battery_level': s.battery_level,
                'signal_strength': s.signal_strength
            } for s in self.sensors],
            'actuators': [{
                'id': a.actuator_id,
                'location': a.location,
                'status': a.status,
                'last_action': a.last_action
            } for a in self.actuators]
        }

def main():
    """Função principal para teste"""
    simulator = IoTDeviceSimulator()
    
    try:
        simulator.start_simulation()
        
        # Executa por 60 segundos
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\n⏹️ Interrompido pelo usuário")
    finally:
        simulator.stop_simulation()

if __name__ == "__main__":
    main()
