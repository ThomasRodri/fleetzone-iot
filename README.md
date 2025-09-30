FleetZone IoT — Visão Computacional + Dashboard + IoT

Monitoramento de pátios com detecção de motos em tempo real usando YOLOv8 (Ultralytics), backend Python/Flask com Flask-SocketIO para atualizações em tempo real e integração com dispositivos IoT. Inclui dashboard web, API REST, demos e pasta de relatórios.

Tecnologias: Python 3.10+, Flask, Flask-SocketIO, Ultralytics YOLOv8, OpenCV, SQLite, HTML/CSS/JS. Estrutura de pastas conforme o repositório público. 
GitHub

Sumário

Arquitetura & Pastas

Pré-requisitos

Instalação

Como rodar (Backend + Dashboard)

Como rodar a Demo

Configurações (env)

API REST

Eventos WebSocket

Banco de Dados

Relatórios

Scripts Úteis

Troubleshooting

Roadmap

Licença

Arquitetura & Pastas
fleetzone-iot/
├─ assets/           # Imagens, CSS, JS, modelos e artefatos estáticos
├─ demos/            # Exemplos e scripts de teste (ex.: runner de vídeo)
├─ reports/          # Relatórios exportados (CSV/JSON) e notebooks auxiliares
├─ scripts/          # Utilitários de manutenção/migração
├─ src/
│  └─ backend/
│     └─ app.py      # Backend Flask principal (API + SocketIO + Dashboard)
├─ fix_db.py         # Ajustes/migrações pontuais no SQLite
├─ fleetzone.py      # Módulos centrais/orquestração da solução
├─ requirements.txt  # Dependências Python
└─ README.md


As pastas e arquivos acima refletem o conteúdo público do repo, inclusive a presença de fleetzone.py, fix_db.py e requirements.txt. 
GitHub

Pré-requisitos

Python 3.10+

pip atualizado

FFmpeg instalado no sistema (recomendado para leitura de vídeo e codecs)

Git

(Windows/PowerShell) Permitir scripts locais (ver Troubleshooting
)

Instalação

Clone o repositório:

git clone https://github.com/ThomasRodri/fleetzone-iot.git
cd fleetzone-iot


Crie e ative um ambiente virtual:

Windows (PowerShell):

python -m venv .venv
.\.venv\Scripts\Activate.ps1


Windows (CMD):

python -m venv .venv
.venv\Scripts\activate.bat


macOS / Linux:

python3 -m venv .venv
source .venv/bin/activate


Instale as dependências:

pip install --upgrade pip
pip install -r requirements.txt


O arquivo requirements.txt está no repositório público. 
GitHub

Como rodar (Backend + Dashboard)

Ative o venv (se ainda não estiver ativo).

Suba o backend Flask (dashboard incluso):

cd src/backend
python app.py


Acesse no navegador:

http://127.0.0.1:5000


O dashboard exibe contadores (detecções totais, motos únicas, FPS médio, taxa de detecção), classes detectadas, últimos eventos e dispositivos IoT conectados, com atualização em tempo real via SocketIO.

A presença do dashboard web + API + SocketIO consta do README do repo. 
GitHub

Como rodar a Demo

A demo executa a detecção sobre um vídeo local e envia/expõe resultados para o backend/dashboard.

cd demos
python main.py


Parâmetros típicos:

--source caminho para o vídeo (padrão: assets/sample_video.mp4)

--cam índice/URL de câmera, se quiser rodar em tempo real

A pasta demos/ está referenciada no README do repo e existe no projeto. 
GitHub

Configurações (env)

Crie um arquivo .env na raiz (opcional, caso queira customizar):

# Porta do Flask
FLASK_PORT=5000

# Caminho padrão da fonte de vídeo/câmera
VIDEO_SOURCE=assets/sample_video.mp4

# Banco de dados SQLite
DATABASE_URL=sqlite:///fleetzone.db

# Thresholds de detecção (ex.: 0.25 = 25%)
YOLO_CONFIDENCE=0.25
YOLO_IOU=0.45

# Flags para relatórios
EXPORT_REPORTS=true
REPORTS_DIR=reports


Se não definir .env, o app deve usar valores padrão hardcoded (ex.: porta 5000, fonte de vídeo de assets/).

API REST

Rotas principais expostas pelo backend:

Método	Rota	Descrição	Exemplo de resposta
GET	/	Página inicial (dashboard web)	HTML
GET	/detections	Retorna as detecções recentes em JSON	{"detections":[...]}
GET	/alerts	Lista alertas do sistema	{"alerts":[...]}
POST	/upload	Envia imagem/vídeo para análise (multipart/form-data)	{"detections":[...]}

Exemplo (upload de imagem):

curl -X POST -F "file=@moto.jpg" http://127.0.0.1:5000/upload


Resposta:

{
  "detections": [
    {"class":"moto","confidence":0.92,"bbox":[34,45,120,200]}
  ]
}


Essas rotas constam no README público (com upload via curl e resposta esperada). 
GitHub

Eventos WebSocket

O Flask-SocketIO envia atualizações em tempo real para o dashboard:

detections:update — nova leva de detecções

stats:update — métricas agregadas (FPS, taxa de detecção etc.)

alerts:update — alertas disparados pelo motor de regras

Payload típico:

{
  "timestamp": "2025-09-30T12:00:00Z",
  "fps": 24.3,
  "count": 12,
  "unique": 9,
  "classes": {"moto": 12},
  "lastDetections": [
    {"class":"moto","confidence":0.91,"bbox":[...]}
  ]
}


Os nomes dos eventos podem variar conforme sua implementação em app.py; este bloco documenta o comportamento esperado do dashboard citado no README do repo. 
GitHub

Banco de Dados

SQLite local (arquivo fleetzone.db por padrão).

Script auxiliar: fix_db.py para pequenos ajustes/migrações.

Tabelas sugeridas:

detections(id, ts, class, confidence, bbox, source_id)

devices(id, name, type, status, last_seen)

alerts(id, ts, level, message, meta)

O uso de SQLite está mencionado no README público; o arquivo fix_db.py está na raiz do repo. 
GitHub

Relatórios

A pasta reports/ armazena saídas exportadas (CSV/JSON) geradas pelo backend ou pelos scripts de suporte (ex.: consolidação diária de contagens, heatmaps por horário, etc.).

Scripts Úteis

scripts/ — utilitários de automação (ex.: limpeza, exportações, conversão de anotações).

fix_db.py — normalizações pontuais no banco (renomear colunas, índices, VACUUM).

Execute um script:

python scripts/<nome-do-script>.py

Troubleshooting
Windows/PowerShell — “execução de scripts desabilitada”

Se ao ativar o venv você vir erro de política de execução, rode:

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser


Depois ative novamente:

.\.venv\Scripts\Activate.ps1

OpenCV/FFmpeg

Se o vídeo não abrir ou o codec falhar:

Garanta FFmpeg instalado e no PATH.

Teste outro arquivo/URL em --source.

Porta ocupada (5000)

Ajuste FLASK_PORT no .env, ou

Rode python app.py --port 5050 (se suportado).

Roadmap

 Conectar câmera IP/RTSP e múltiplas fontes simultâneas

 Exportar relatórios (CSV/JSON) a cada N minutos

 Regras de alerta configuráveis (zona proibida, detecção fora de horário)

 Painel de dispositivos IoT com telemetria (MQTT/HTTP)

 Deploy em nuvem (Render/Heroku/Azure)

 Autenticação básica (login para o dashboard)

 Testes automatizados (unitários e de contrato da API)

O README público cita próximos passos como conectar câmera em tempo real, exportar relatórios e deploy. 
GitHub

Licença

Este projeto é disponibilizado para fins educacionais. Defina uma licença explícita (ex.: MIT/Apache-2.0) caso pretenda uso/redistribuição ampla.

Créditos

Projeto desenvolvido pela equipe FleetZone.
Stack e organização conforme materiais presentes no repositório público