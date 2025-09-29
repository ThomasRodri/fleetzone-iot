#!/usr/bin/env python3
# fleetzone.py
"""
FleetZone - Orquestrador do sistema (runner-friendly)
- Inicializa DB
- Checa backend (opcional)
- Roda detecção (apenas motos)
"""

import os
import sys
import time
import threading
from datetime import datetime

import cv2
import requests

# Garante import dos módulos em src/
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Imports do projeto
from src.utils.database import DatabaseManager
from src.detection.moto_detector import MotoDetector


class FleetZoneSystem:
    """Sistema principal do FleetZone (apenas motos)"""

    def __init__(self):
        self.detector = MotoDetector()
        self.db = DatabaseManager(db_path=os.path.join(_PROJECT_ROOT, "fleetzone.db"))
        self.running = False
        self.api_url = "http://localhost:5000"
        self.backend_running = False
        self.total_detections = 0
        self.unique_motos = set()

    def initialize(self):
        """Inicializa banco e verifica backend"""
        print("🚀 Inicializando FleetZone...")
        self.db.initialize()
        print("✅ Banco de dados inicializado")
        self._check_backend()
        print("✅ Sistema inicializado com sucesso!")

    def _check_backend(self):
        """Verifica se a API backend está no ar (opcional)"""
        try:
            r = requests.get(f"{self.api_url}/metrics", timeout=1.5)
            if r.status_code == 200:
                self.backend_running = True
                print("✅ Backend API conectado")
            else:
                print("⚠️ Backend API não disponível - modo offline")
        except requests.exceptions.RequestException:
            print("⚠️ Backend API não disponível - modo offline")

    def _send_to_api(self, payload: dict):
        if not self.backend_running:
            return
        try:
            requests.post(f"{self.api_url}/detections", json=payload, timeout=1.0)
        except requests.exceptions.RequestException:
            pass  # ignora se offline

    def run_detection(self, video_path: str, max_frames: int = 200) -> bool:
        """Executa detecção SOMENTE de motos no vídeo informado"""
        # Normaliza caminho relativo
        if not os.path.isabs(video_path):
            video_path = os.path.join(_PROJECT_ROOT, video_path)

        print(f"🔍 Iniciando detecção em: {os.path.relpath(video_path, _PROJECT_ROOT)}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("❌ Erro ao abrir vídeo")
            return False

        self.running = True
        frame_count = 0
        start = time.time()
        print("📹 Processando vídeo...")
        print("Controles: 'q' = sair, 's' = salvar frame")

        while self.running:
            ok, frame = cap.read()
            if not ok:
                break

            frame_count += 1

            # ======== DETECÇÃO ========
            # detect_motos + filter_motos já restringem a motos no seu projeto
            detections = self.detector.detect_motos(frame)
            moto_dets = self.detector.filter_motos(detections)

            elapsed = time.time() - start
            fps_now = (frame_count / elapsed) if elapsed > 0 else 0.0

            # Desenha caixas e labels
            self._draw_detections(frame, moto_dets)
            self._draw_info(frame, frame_count, fps_now, len(moto_dets))

            # Atualiza métricas locais + persiste no DB
            if moto_dets:
                self.total_detections += len(moto_dets)
                for det in moto_dets:
                    self.unique_motos.add(f"{det['class']}_{tuple(det['bbox'])}")

                detection_rate = (len(moto_dets) / elapsed) if elapsed > 0 else 0.0

                # Salva no banco (usa created_at; NADA de 'timestamp'!)
                self.db.save_detections(
                    frame_num=frame_count,
                    detections=moto_dets,
                    fps=fps_now,
                    total_detections=self.total_detections,
                    unique_motos=len(self.unique_motos),
                    detection_rate=detection_rate,
                )

                # Envia para API (se disponível)
                for det in moto_dets:
                    payload = {
                        "frame": frame_count,
                        "class": det["class"],
                        "class_name": det["class_name"],
                        "confidence": det["confidence"],
                        "bbox": det["bbox"],
                        "area": det["area"],
                        "metrics": {
                            "avg_fps": fps_now,
                            "total_detections": self.total_detections,
                            "unique_motos": len(self.unique_motos),
                            "detection_rate": detection_rate,
                            "elapsed_time": elapsed,
                        },
                        "created_at": datetime.now().isoformat(),
                    }
                    threading.Thread(
                        target=self._send_to_api, args=(payload,), daemon=True
                    ).start()

            # Mostra janela
            cv2.imshow("FleetZone - Detecção de Motos", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("s"):
                out = os.path.join(_PROJECT_ROOT, f"frame_{frame_count}.jpg")
                cv2.imwrite(out, frame)
                print(f"📸 Frame {frame_count} salvo em {os.path.basename(out)}")

            if frame_count >= max_frames:
                print(f"📊 Limite de frames atingido ({max_frames})")
                break

        cap.release()
        cv2.destroyAllWindows()

        self._show_report(frame_count, time.time() - start)
        return True

    def _draw_detections(self, frame, detections):
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            conf = det["confidence"]
            label = f"{det['class_name']}: {conf:.2f}"
            color = (0, 255, 0)  # verde para motos
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                label,
                (x1, max(15, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

    def _draw_info(self, frame, frame_count, fps, dets):
        lines = [
            f"Frame: {frame_count}",
            f"FPS: {fps:.1f}",
            f"Motos detectadas (frame): {dets}",
            f"Total detect.: {self.total_detections}",
        ]
        for i, t in enumerate(lines):
            cv2.putText(
                frame,
                t,
                (10, 30 + i * 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

    def _show_report(self, frames, elapsed):
        stats = self.db.get_statistics()
        print("\n📊 RELATÓRIO FINAL:")
        print("=" * 40)
        print(f"Frames processados: {frames}")
        print(f"Tempo total: {elapsed:.2f}s")
        print(f"FPS médio: {frames / elapsed:.2f}")
        print(f"Total de detecções (todas): {stats['total_detections']}")
        print(f"Classes detectadas: {stats['unique_classes']}")

        print("\n📋 ÚLTIMAS DETECÇÕES:")
        print("=" * 30)
        try:
            recent = self.db.get_recent_detections(5)
            if not recent:
                print("— sem registros ainda —")
            else:
                for i, det in enumerate(recent, 1):
                    ts = det.get("timestamp", "")
                    print(f"{i}. Frame {det['frame']} - {det['class_name']} "
                          f"(conf: {det['confidence']:.2f}) {ts}")
        except Exception as e:
            print(f"⚠️ Aviso ao listar recentes: {e}")

    def stop(self):
        self.running = False
        print("🛑 Sistema parado")
