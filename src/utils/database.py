#!/usr/bin/env python3
"""
DatabaseManager - Gerenciador de banco de dados
Módulo para persistência de dados do FleetZone
"""

import sqlite3
from datetime import datetime
import os


def _default_db_path():
    """
    Resolve o caminho absoluto para fleetzone.db na RAIZ do projeto,
    mesmo que o script seja executado a partir de 'demos/'.
    Estrutura esperada:
      raiz/
        fleetzone.db
        src/utils/database.py (este arquivo)
    """
    # .../src/utils/database.py -> .../src/utils
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    # .../src
    src_dir = os.path.dirname(utils_dir)
    # .../ (raiz do projeto)
    project_root = os.path.dirname(src_dir)
    return os.path.join(project_root, "fleetzone.db")


class DatabaseManager:
    """Gerenciador de banco de dados SQLite"""

    def __init__(self, db_path: str | None = None):
        # Usa sempre o DB da raiz do projeto, a menos que seja explicitamente passado
        self.db_path = db_path or _default_db_path()

    # ---------- utilidades internas ----------

    def _connect(self):
        return sqlite3.connect(self.db_path)

    # ---------- schema / init ----------

    def initialize(self):
        """Inicializa o banco de dados e cria tabelas se não existirem"""
        conn = self._connect()
        cursor = conn.cursor()

        # Tabela de detecções (created_at é o carimbo de tempo)
        cursor.execute("""
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
        """)

        # Tabela de métricas da sessão
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_frames INTEGER,
                total_detections INTEGER,
                avg_fps REAL,
                session_duration REAL
            )
        """)

        # Índices simples para consultas comuns
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_created_at ON detections(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_frame ON detections(frame)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_classname ON detections(class_name)")

        conn.commit()
        conn.close()

    # ---------- gravação ----------

    def save_detection(
        self,
        frame_num: int,
        detections: list[dict],
        fps: float,
        total_detections: int = 0,
        unique_motos: int = 0,
        detection_rate: float = 0.0,
    ):
        """Salva UMA OU MAIS detecções no banco (lista de dicts do detector)"""
        if not detections:
            return

        now_iso = datetime.now().isoformat(timespec="seconds")
        rows = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            rows.append(
                (
                    now_iso,
                    frame_num,
                    det.get("class"),
                    det.get("class_name"),
                    float(det.get("confidence", 0.0)),
                    int(x1),
                    int(y1),
                    int(x2),
                    int(y2),
                    int(det.get("area", (x2 - x1) * (y2 - y1))),
                    float(fps),
                    int(total_detections),
                    int(unique_motos),
                    float(detection_rate),
                )
            )

        conn = self._connect()
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO detections (
                created_at, frame, class, class_name, confidence,
                x1, y1, x2, y2, area, fps, total_detections, unique_motos, detection_rate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        conn.close()

    # compat antigo
    def save_detections(self, *args, **kwargs):
        """Alias para save_detection para manter compatibilidade"""
        return self.save_detection(*args, **kwargs)

    # ---------- leitura ----------

    def get_statistics(self) -> dict:
        """Retorna estatísticas agregadas do banco"""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM detections")
        total = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(DISTINCT class_name) FROM detections")
        classes = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(fps) FROM detections")
        avg_fps = cursor.fetchone()[0] or 0.0

        conn.close()

        return {
            "total_detections": int(total),
            "unique_classes": int(classes),
            "avg_fps": float(avg_fps),
        }

    def get_recent_detections(self, limit: int = 10) -> list[dict]:
        """
        Retorna detecções recentes.
        Importante: a coluna de data é 'created_at'. Para a aplicação,
        retornamos com a chave 'timestamp' por conveniência.
        """
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT frame, class_name, confidence, created_at
            FROM detections
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "frame": row[0],
                "class_name": row[1],
                "confidence": float(row[2]),
                "timestamp": row[3],  # vem de created_at
            }
            for row in rows
        ]

    # ---------- métricas de sessão (opcional) ----------

    def save_session_metrics(
        self,
        total_frames: int,
        total_detections: int,
        avg_fps: float,
        session_duration: float,
    ):
        """Registra um resumo da sessão de processamento (opcional)"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO metrics (timestamp, total_frames, total_detections, avg_fps, session_duration)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                int(total_frames),
                int(total_detections),
                float(avg_fps),
                float(session_duration),
            ),
        )
        conn.commit()
        conn.close()
