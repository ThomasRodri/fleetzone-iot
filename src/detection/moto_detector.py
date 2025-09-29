#!/usr/bin/env python3
"""
MotoDetector - Detector de motos usando YOLOv8
Módulo principal de detecção
"""

import cv2
from ultralytics import YOLO
import numpy as np
from collections import deque

class MotoDetector:
    """Detector de motos usando YOLOv8"""
    
    def __init__(self, model_path='yolov8n.pt', confidence_threshold=0.5):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.fps_history = deque(maxlen=60)
        self.total_detections = 0
        self.unique_motos = set()
        
        # Classes COCO que podem ser motos ou similares
        self.moto_classes = {
            3: "motorbike",      # moto
            1: "bicycle",        # bicicleta
            2: "car",            # carro
            7: "truck",          # caminhão
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
        return {
            'total_detections': self.total_detections,
            'unique_motos': len(self.unique_motos),
            'avg_fps': np.mean(list(self.fps_history)) if self.fps_history else 0
        }
