📖 README – FleetZone Dashboard
👥 Grupo

FleetZone

📌 Sobre o Projeto

O FleetZone Dashboard é um sistema que integra visão computacional (YOLOv8) e backend em Python/Flask para monitorar e identificar motos em tempo real.
O sistema também permite conexão com dispositivos IoT para enriquecer as análises e gerar alertas automáticos.

🚀 Funcionalidades

🔍 Detecção em Tempo Real de motos usando modelo YOLOv8.

📊 Dashboard Web exibindo:

Total de detecções

Motos únicas

FPS médio

Taxa de detecção

Classes detectadas

Dispositivos IoT conectados

⚡ Atualização dinâmica das últimas detecções.

🔔 Alertas do sistema configuráveis.

🌐 API Flask para integração com outros sistemas.

🏗️ Arquitetura do Projeto
FleetZone-main/
│
├── demos/               # Exemplos e scripts de teste
│   └── main.py
│
├── src/
│   └── backend/
│       └── app.py       # Backend Flask principal
│
├── assets/              # Imagens, CSS, JS, modelos
│
├── requirements.txt     # Dependências Python
├── index.html           # Página inicial (verde/preto)
└── README.md            # Este documento

⚙️ Tecnologias Utilizadas

Python 3.10+

Flask

Flask-SocketIO

YOLOv8 (Ultralytics)

SQLite (armazenamento local)

HTML5 / CSS3 (tema verde & preto)

▶️ Como Rodar
1. Clonar o repositório
git clone <url-do-repo>
cd FleetZone-main

2. Criar ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1   # (no PowerShell do Windows)

3. Instalar dependências
pip install -r requirements.txt

4. Rodar backend Flask
cd src/backend
python app.py


Acesse no navegador:
👉 http://127.0.0.1:5000

5. Rodar demo (opcional)
cd demos
python main.py

📡 Rotas Principais da API
Método	Rota	Descrição
GET	/	Página inicial (dashboard)
GET	/detections	Retorna as detecções em JSON
GET	/alerts	Lista os alertas do sistema
POST	/upload	Envia vídeo/imagem para análise
WS	/socket.io	Atualizações em tempo real via Socket
📊 Exemplo de Uso

Enviar uma imagem para detecção:

curl -X POST -F "file=@moto.jpg" http://127.0.0.1:5000/upload


Resposta esperada:

{
  "detections": [
    {"class": "moto", "confidence": 0.92, "bbox": [34, 45, 120, 200]}
  ]
}

✅ Status Atual

Backend Flask funcional

Dashboard com tema verde/preto

Integração com YOLOv8 configurada

API em funcionamento básico

📌 Próximos Passos

 Conectar câmera em tempo real

 Adicionar exportação de relatórios (CSV/JSON)

 Melhorar sistema de alertas

 Deploy em nuvem (Heroku/Azure)