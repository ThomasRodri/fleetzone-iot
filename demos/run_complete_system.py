#!/usr/bin/env python3
"""
FleetZone - Sistema Completo
Script principal que integra detecção de visão computacional com IoT
"""

import sys
import os
import time
import threading
import subprocess
from datetime import datetime

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.detection.moto_detector import MotoDetector
from src.utils.database import DatabaseManager
from src.iot.sensor_simulator import IoTDeviceSimulator
import requests

class FleetZoneComplete:
    """Sistema completo FleetZone com IoT e Visão Computacional"""
    
    def __init__(self):
        self.detector = MotoDetector()
        self.db = DatabaseManager()
        self.iot_simulator = IoTDeviceSimulator()
        self.backend_process = None
        self.running = False
        
    def start_backend(self):
        """Inicia o backend Flask"""
        print("🚀 Iniciando backend Flask...")
        try:
            # Inicia o backend em processo separado
            self.backend_process = subprocess.Popen([
                sys.executable, '-m', 'src.backend.app'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Aguarda o backend inicializar
            time.sleep(3)
            
            # Verifica se está rodando
            try:
                response = requests.get("http://localhost:5000/metrics", timeout=2)
                if response.status_code == 200:
                    print("✅ Backend Flask iniciado com sucesso!")
                    return True
            except requests.exceptions.RequestException:
                pass
                
            print("❌ Falha ao iniciar backend Flask")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao iniciar backend: {e}")
            return False
    
    def stop_backend(self):
        """Para o backend Flask"""
        if self.backend_process:
            print("🛑 Parando backend Flask...")
            self.backend_process.terminate()
            self.backend_process.wait()
            print("✅ Backend Flask parado!")
    
    def run_detection_demo(self, max_frames=100):
        """Executa demonstração de detecção"""
        print("🔍 Iniciando demonstração de detecção...")
        
        video_path = "assets/sample_video.mp4"
        if not os.path.exists(video_path):
            print(f"❌ Vídeo não encontrado: {video_path}")
            return False
        
        import cv2
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("❌ Erro ao abrir vídeo")
            return False
        
        frame_count = 0
        start_time = time.time()
        
        print("📹 Processando vídeo (pressione 'q' para sair)...")
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Detecção
            detections = self.detector.detect_motos(frame)
            moto_detections = self.detector.filter_motos(detections)
            
            # Calcula métricas
            elapsed = time.time() - start_time
            current_fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Desenha detecções
            self._draw_detections(frame, moto_detections)
            
            # Salva dados
            if moto_detections:
                self.db.save_detections(frame_count, moto_detections, current_fps)
                
                # Envia para API
                for det in moto_detections:
                    detection_data = {
                        'frame': frame_count,
                        'class': det['class'],
                        'class_name': det['class_name'],
                        'confidence': det['confidence'],
                        'bbox': det['bbox'],
                        'area': det['area'],
                        'metrics': {
                            'avg_fps': current_fps,
                            'total_detections': len(moto_detections),
                            'unique_motos': len(set(f"{d['class']}_{d['bbox']}" for d in moto_detections)),
                            'detection_rate': len(moto_detections) / elapsed if elapsed > 0 else 0
                        }
                    }
                    
                    try:
                        requests.post("http://localhost:5000/detections", 
                                    json=detection_data, timeout=1)
                    except requests.exceptions.RequestException:
                        pass
            
            # Adiciona informações na tela
            self._draw_info(frame, frame_count, current_fps, len(moto_detections))
            
            # Exibe frame
            cv2.imshow("FleetZone - Sistema Completo", frame)
            
            # Controles
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        
        # Limpeza
        cap.release()
        cv2.destroyAllWindows()
        
        # Relatório
        self._show_report(frame_count, time.time() - start_time)
        return True
    
    def _draw_detections(self, frame, detections):
        """Desenha detecções no frame"""
        import cv2
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            class_name = det['class_name']
            
            # Cor baseada na classe
            color = (0, 255, 0) if det['class'] == 3 else (255, 0, 0)
            
            # Desenha bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Desenha label
            label = f"{class_name}: {conf:.2f}"
            cv2.putText(frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    def _draw_info(self, frame, frame_count, fps, detections_count):
        """Desenha informações na tela"""
        import cv2
        info_text = [
            f"Frame: {frame_count}",
            f"FPS: {fps:.1f}",
            f"Detecções: {detections_count}",
            f"Sistema: FleetZone + IoT"
        ]
        
        for i, text in enumerate(info_text):
            cv2.putText(frame, text, (10, 30 + i*25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def _show_report(self, frame_count, elapsed_time):
        """Mostra relatório final"""
        stats = self.db.get_statistics()
        
        print("\n📊 RELATÓRIO FINAL:")
        print("=" * 40)
        print(f"Frames processados: {frame_count}")
        print(f"Tempo total: {elapsed_time:.2f}s")
        print(f"FPS médio: {frame_count/elapsed_time:.2f}")
        print(f"Total de detecções: {stats['total_detections']}")
        print(f"Classes detectadas: {stats['unique_classes']}")
        
        print("\n📋 ÚLTIMAS DETECÇÕES:")
        print("=" * 30)
        
        recent = self.db.get_recent_detections(5)
        for i, det in enumerate(recent, 1):
            print(f"{i}. Frame {det['frame']} - {det['class_name']} "
                  f"(conf: {det['confidence']:.2f})")
    
    def run_complete_demo(self):
        """Executa demonstração completa do sistema"""
        print("🎯 FleetZone - Sistema Completo")
        print("=" * 50)
        print("Integrando Visão Computacional + IoT")
        print("=" * 50)
        try:
            # Inicializa banco de dados
            print("🗄️ Inicializando banco de dados...")
            self.db.initialize()
            print("✅ Banco de dados inicializado")
            # Inicia backend
            if not self.start_backend():
                print("⚠️ Continuando sem backend...")
            # Inicia simulação IoT
            print("📡 Iniciando simulação IoT...")
            self.iot_simulator.start_simulation()
            # Executa detecção
            print("🔍 Iniciando detecção de visão computacional...")
            self.run_detection_demo()
            print("\n✅ Demonstração completa finalizada!")
            print("🌐 Dashboard disponível em: http://localhost:5000")
            print("📊 Sistema integrado funcionando!")
        except KeyboardInterrupt:
            print("\n⏹️ Sistema interrompido pelo usuário")
        except Exception as e:
            print(f"❌ Erro: {e}")
        finally:
            # Limpeza
            print("\n🧹 Limpando recursos...")
            self.iot_simulator.stop_simulation()
            self.stop_backend()
            print("✅ Limpeza concluída!")

def main():
    """Função principal"""
    system = FleetZoneComplete()
    system.run_complete_demo()

if __name__ == "__main__":
    main()
