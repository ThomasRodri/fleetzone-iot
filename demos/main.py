#!/usr/bin/env python3
# demos/main.py

import os
import sys
import argparse

# Garante que a RAIZ do projeto está no sys.path (…/fleetzone)
_DEMOS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_DEMOS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# >>> Se a classe estiver em outro lugar, troque a importação abaixo:
# from demos.demo_final import FleetZoneSystem
from fleetzone import FleetZoneSystem   # raiz/fleetzone.py

def parse_args():
    p = argparse.ArgumentParser("FleetZone - runner")
    p.add_argument(
        "--source",
        type=str,
        default=os.path.join("assets", "sample_video.mp4"),
        help="Caminho do vídeo (mp4, avi, etc.)",
    )
    p.add_argument(
        "--frames",
        type=int,
        default=200,
        help="Máximo de frames para processar (0 = sem limite)",
    )
    return p.parse_args()

def main():
    args = parse_args()

    print("🎯 FleetZone - Sistema de Detecção de Motos")
    print("=" * 50)

    system = FleetZoneSystem()
    try:
        system.initialize()
        ok = system.run_detection(
            video_path=args.source,
            max_frames=(args.frames if args.frames > 0 else 10_000_000),
        )
        if ok:
            print("\n✅ Sistema executado com sucesso!")
            print("🎉 FleetZone funcionando perfeitamente!")
    except KeyboardInterrupt:
        print("\n⏹️ Sistema interrompido pelo usuário")
        system.stop()
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        print("\n🧹 Limpeza concluída")

if __name__ == "__main__":
    main()
