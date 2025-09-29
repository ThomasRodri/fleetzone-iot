import cv2
from ultralytics import YOLO
from sort import Sort
import numpy as np
import argparse
import csv
import time
import requests


def main():
    parser = argparse.ArgumentParser(description="Rastreamento de motos com YOLOv8 + SORT")
    parser.add_argument("--video", default="assets/sample_video.mp4", help="Caminho para o arquivo de vídeo")
    parser.add_argument("--output", help="Arquivo CSV para salvar os dados de rastreamento")
    parser.add_argument("--no-display", action="store_true", help="Desabilita a exibição do vídeo")
    parser.add_argument("--max-frames", type=int, default=None, help="Número máximo de frames a serem processados")
    parser.add_argument("--backend-url", default="http://localhost:5000/detections", help="URL do backend para envio dos eventos")
    args = parser.parse_args()

    model = YOLO('yolov8n.pt')
    cap = cv2.VideoCapture(args.video)
    tracker = Sort()

    frame_num = 0
    track_ids = set()
    start_time = time.time()

    csv_file = None
    writer = None
    if args.output:
        csv_file = open(args.output, 'w', newline='')
        writer = csv.writer(csv_file)
        writer.writerow(['frame', 'track_id', 'x1', 'y1', 'x2', 'y2'])

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_num += 1

        results = model(frame)
        detections = results[0].boxes

        dets = []
        for box in detections:
            cls = int(box.cls.item())
            if cls == 3:  # classe 3 = "motorbike" em COCO
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf.item()
                dets.append([x1, y1, x2, y2, conf])

        dets_np = np.array(dets)
        if len(dets_np) == 0:
            tracks = np.empty((0, 5))
        else:
            tracks = tracker.update(dets_np)

        for track in tracks:
            if len(track) == 5:
                x1, y1, x2, y2, track_id = track.astype(int)
                track_ids.add(int(track_id))
                if writer:
                    writer.writerow([frame_num, int(track_id), x1, y1, x2, y2])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, f'ID {int(track_id)}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                # Enviar evento ao backend (não bloqueante com timeout curto)
                try:
                    elapsed = time.time() - start_time
                    fps = frame_num / elapsed if elapsed > 0 else 0
                    payload = {
                        'frame': frame_num,
                        'track_id': int(track_id),
                        'x1': int(x1),
                        'y1': int(y1),
                        'x2': int(x2),
                        'y2': int(y2),
                        'fps': float(fps),
                        'count': len(track_ids),
                    }
                    requests.post(args.backend_url, json=payload, timeout=0.2)
                except Exception:
                    pass

        if not args.no_display:
            cv2.imshow("FleetZone - Rastreamento YOLOv8 + SORT", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        if args.max_frames and frame_num >= args.max_frames:
            break

    cap.release()
    if not args.no_display:
        cv2.destroyAllWindows()
    if csv_file:
        csv_file.close()
    elapsed = time.time() - start_time
    fps = frame_num / elapsed if elapsed > 0 else 0
    print(f"Processadas {frame_num} frames em {elapsed:.2f}s ({fps:.2f} FPS)")
    print(f"IDs únicos rastreados: {len(track_ids)}")


if __name__ == "__main__":
    main()
