import cv2
from ultralytics import YOLO
import numpy as np
import argparse
import time
import json
import requests
from datetime import datetime
import threading
from collections import deque

class MotoDetector:
    def __init__(self, model_path='yolov8n.pt', confidence_threshold=0.5):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.fps_history = deque(maxlen=60)
        self.detection_history = deque(maxlen=100)
        self.total_detections = 0
        self.unique_motos = set()
        self.start_time = time.time()
        
        # Classes COCO que podem ser motos ou similares
        self.moto_classes = {
            3: "motorbike",      # moto
            1: "bicycle",        # bicicleta (pode ser confundida)
            2: "car",            # carro (para comparação)
            7: "truck",          # caminhão (pode ser confundido)
        }
        
    def detect_motos(self, frame):
        """Detecta motos no frame usando YOLOv8"""
        results = self.model(frame, conf=self.confidence_threshold)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls.item())
                    conf = box.conf.item()
                    
                    # Filtra apenas motos e veículos similares
                    if cls in self.moto_classes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        detection = {
                            'class': cls,
                            'class_name': self.moto_classes[cls],
                            'confidence': conf,
                            'bbox': [x1, y1, x2, y2],
                            'area': (x2 - x1) * (y2 - y1)
                        }
                        detections.append(detection)
        
        return detections
    
    def filter_motos(self, detections):
        """Filtra apenas motos baseado em características específicas"""
        moto_detections = []
        
        for det in detections:
            # Prioriza motos (classe 3)
            if det['class'] == 3:
                moto_detections.append(det)
            # Se não há motos, considera bicicletas como possíveis motos
            elif det['class'] == 1 and len([d for d in detections if d['class'] == 3]) == 0:
                # Ajusta a confiança para bicicletas
                det['confidence'] *= 0.7
                moto_detections.append(det)
        
        return moto_detections
    
    def calculate_metrics(self):
        """Calcula métricas de performance"""
        elapsed = time.time() - self.start_time
        current_fps = len(self.fps_history) / elapsed if elapsed > 0 else 0
        
        return {
            'total_detections': self.total_detections,
            'unique_motos': len(self.unique_motos),
            'current_fps': current_fps,
            'avg_fps': np.mean(list(self.fps_history)) if self.fps_history else 0,
            'elapsed_time': elapsed,
            'detection_rate': self.total_detections / elapsed if elapsed > 0 else 0
        }
    
    def send_to_backend(self, detections, frame_num, metrics):
        """Envia dados para o backend"""
        for det in detections:
            try:
                payload = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'frame': frame_num,
                    'class': det['class'],
                    'class_name': det['class_name'],
                    'confidence': det['confidence'],
                    'bbox': det['bbox'],
                    'area': det['area'],
                    'metrics': metrics
                }
                
                requests.post('http://localhost:5000/detections', 
                            json=payload, timeout=0.1)
            except Exception as e:
                pass  # Ignora erros de comunicação
    
    def process_video(self, video_path, output_path=None, max_frames=None, 
                     display=True, backend_url='http://localhost:5000/detections'):
        """Processa vídeo com detecção de motos"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Erro ao abrir vídeo: {video_path}")
            return
        
        # Configuração do vídeo de saída
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        frame_start_time = time.time()
        
        print("Iniciando detecção de motos...")
        print("Pressione 'q' para sair, 's' para salvar frame")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Detecção
            detections = self.detect_motos(frame)
            moto_detections = self.filter_motos(detections)
            
            # Atualiza métricas
            self.total_detections += len(moto_detections)
            for det in moto_detections:
                self.unique_motos.add(f"{det['class']}_{det['bbox']}")
            
            # Calcula FPS
            frame_time = time.time() - frame_start_time
            if frame_time > 0:
                current_fps = 1.0 / frame_time
                self.fps_history.append(current_fps)
            frame_start_time = time.time()
            
            # Desenha detecções
            for det in moto_detections:
                x1, y1, x2, y2 = det['bbox']
                conf = det['confidence']
                class_name = det['class_name']
                
                # Cor baseada na classe
                color = (0, 255, 0) if det['class'] == 3 else (255, 0, 0)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{class_name}: {conf:.2f}"
                cv2.putText(frame, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Adiciona informações de métricas
            metrics = self.calculate_metrics()
            info_text = [
                f"FPS: {metrics['avg_fps']:.1f}",
                f"Detecções: {metrics['total_detections']}",
                f"Motos únicas: {metrics['unique_motos']}",
                f"Frame: {frame_count}"
            ]
            
            for i, text in enumerate(info_text):
                cv2.putText(frame, text, (10, 30 + i*25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Envia para backend
            self.send_to_backend(moto_detections, frame_count, metrics)
            
            # Salva frame se solicitado
            if output_path and writer:
                writer.write(frame)
            
            # Exibe frame
            if display:
                cv2.imshow("FleetZone - Detecção de Motos", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    cv2.imwrite(f"frame_{frame_count}.jpg", frame)
                    print(f"Frame {frame_count} salvo")
            
            # Limite de frames
            if max_frames and frame_count >= max_frames:
                break
        
        # Limpeza
        cap.release()
        if writer:
            writer.release()
        if display:
            cv2.destroyAllWindows()
        
        # Relatório final
        final_metrics = self.calculate_metrics()
        print("\n=== RELATÓRIO FINAL ===")
        print(f"Frames processados: {frame_count}")
        print(f"Tempo total: {final_metrics['elapsed_time']:.2f}s")
        print(f"FPS médio: {final_metrics['avg_fps']:.2f}")
        print(f"Total de detecções: {final_metrics['total_detections']}")
        print(f"Motos únicas detectadas: {final_metrics['unique_motos']}")
        print(f"Taxa de detecção: {final_metrics['detection_rate']:.2f} detecções/segundo")

def main():
    parser = argparse.ArgumentParser(description="Detecção avançada de motos com YOLOv8")
    parser.add_argument("--video", default="assets/sample_video.mp4", 
                       help="Caminho para o arquivo de vídeo")
    parser.add_argument("--output", help="Arquivo de saída para salvar vídeo processado")
    parser.add_argument("--no-display", action="store_true", 
                       help="Desabilita a exibição do vídeo")
    parser.add_argument("--max-frames", type=int, default=None, 
                       help="Número máximo de frames a serem processados")
    parser.add_argument("--confidence", type=float, default=0.5, 
                       help="Limiar de confiança para detecção")
    parser.add_argument("--model", default="yolov8n.pt", 
                       help="Caminho para o modelo YOLOv8")
    
    args = parser.parse_args()
    
    # Inicializa detector
    detector = MotoDetector(
        model_path=args.model,
        confidence_threshold=args.confidence
    )
    
    # Processa vídeo
    detector.process_video(
        video_path=args.video,
        output_path=args.output,
        max_frames=args.max_frames,
        display=not args.no_display
    )

if __name__ == "__main__":
    main()
