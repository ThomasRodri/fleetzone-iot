#!/usr/bin/env python3
"""
MetricsCollector - Coletor de métricas
Módulo para coleta e análise de métricas
"""

import time
from collections import deque
from datetime import datetime

class MetricsCollector:
    """Coletor de métricas de performance"""
    
    def __init__(self):
        self.fps_history = deque(maxlen=60)
        self.detection_history = deque(maxlen=100)
        self.start_time = time.time()
        
    def update_fps(self, fps):
        """Atualiza histórico de FPS"""
        self.fps_history.append(fps)
    
    def add_detection(self, detection):
        """Adiciona detecção ao histórico"""
        self.detection_history.append({
            'timestamp': datetime.now().isoformat(),
            'detection': detection
        })
    
    def get_current_metrics(self):
        """Retorna métricas atuais"""
        elapsed = time.time() - self.start_time
        
        return {
            'session_duration': elapsed,
            'avg_fps': sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0,
            'total_detections': len(self.detection_history),
            'fps_trend': list(self.fps_history)[-10:] if len(self.fps_history) >= 10 else list(self.fps_history)
        }
    
    def reset(self):
        """Reseta métricas"""
        self.fps_history.clear()
        self.detection_history.clear()
        self.start_time = time.time()
