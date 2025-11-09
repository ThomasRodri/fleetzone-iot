# 🚦 FleetZone IoT

Projeto desenvolvido para o **Challenge 2025** em parceria com a **Mottu**, com objetivo de realizar **mapeamento inteligente de pátios** e **controle de motocicletas** utilizando **Visão Computacional**.  

O sistema integra:
- 📹 Captura e análise de vídeo em tempo real (YOLOv8 + OpenCV)  
- 🌐 API RESTful com Flask  
- 🔌 Comunicação em tempo real via WebSocket (Flask-SocketIO)  
- 🗄️ Banco de dados SQLite para persistência  
- 📊 Dashboard web interativo para monitoramento  

---

## 📁 Estrutura de Pastas

```
fleetzone-iot/
│── assets/              # Vídeos e imagens de teste
│── demos/               # Scripts de execução/demonstração
│   └── main.py
|── rastreio
│── fleetzone.py         # Classe principal do sistema
│── backend/             # API Flask + WebSocket
│   ├── app.py
│   ├── routes/
│   └── models/
│── dashboard/           # Frontend HTML/JS para monitoramento
│── reports/             # Relatórios gerados
│── requirements.txt     # Dependências do projeto
│── README.md            # Documentação
```

---

## ⚙️ Tecnologias Utilizadas

- Python 3.10+
- Flask + Flask-SocketIO
- YOLOv8 (Ultralytics)
- OpenCV
- SQLite
- HTML, CSS e JavaScript

---

## 🚀 Como Executar

### 1. Clonar repositório
```bash
git clone https://github.com/ThomasRodri/fleetzone-iot.git
cd fleetzone-iot
```

### 2. Criar ambiente virtual
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Executar backend
```bash
cd backend
python app.py
```
API disponível em: [http://localhost:5000](http://localhost:5000)

### 5. Executar dashboard
Basta abrir o arquivo `dashboard/index.html` no navegador.  
O dashboard consome dados em tempo real via WebSocket.

### 6. Rodar a demo
```bash
cd demos
python main.py --source ../assets/sample_video.mp4
```

---

## 🌍 Configuração via `.env`

Crie um arquivo `.env` na raiz:
```ini
FLASK_ENV=development
DATABASE_URL=sqlite:///fleetzone.db
VIDEO_SOURCE=assets/sample_video.mp4
SECRET_KEY=fiap2025
```

---

## 📡 API REST

### Rotas principais

| Método | Endpoint          | Descrição                       |
|--------|------------------|---------------------------------|
| POST   | `/api/v1/motos`  | Cadastrar nova moto             |
| GET    | `/api/v1/motos`  | Listar motos cadastradas        |
| POST   | `/api/v1/patios` | Criar novo pátio                |
| GET    | `/api/v1/patios` | Listar pátios cadastrados       |
| GET    | `/api/v1/status` | Status do sistema               |

**Exemplo de requisição:**
```bash
curl -X POST http://localhost:5000/api/v1/motos \
-H "Content-Type: application/json" \
-d '{"placa": "ABC1234", "modelo": "Honda CG 160"}'
```

---

## 🔔 WebSocket (Eventos)

O backend emite os seguintes eventos:

- `moto_detectada`: enviada quando uma moto é identificada no vídeo  
- `patio_atualizado`: mudanças no status de ocupação do pátio  
- `alerta`: alerta de movimentação inesperada  

---

## 🗄️ Banco de Dados

Banco: **SQLite** (`fleetzone.db`)

### Tabelas
- `motos` → id, placa, modelo, status  
- `patios` → id, nome, capacidade, ocupacao  
- `eventos` → id, tipo, timestamp, detalhes  

---

## 📊 Relatórios

Os relatórios são gerados automaticamente em `reports/` contendo:
- Ocupação média dos pátios  
- Histórico de detecções de motos  
- Alertas registrados  

---

## 🛠️ Troubleshooting

- **Erro de ativação venv (Windows)**:  
  Rode no PowerShell:  
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

- **Porta ocupada (5000)**:  
  ```bash
  netstat -ano | findstr 5000
  taskkill /PID <pid> /F
  ```

## 🎯 Pasta Rastreio

A pasta `rastreio/` concentra o módulo responsável por **ler placas de motocicletas a partir de imagens** e **enviar os registros ao backend**, gerando o histórico de **entrada e saída** das motos nos pátios.

---

### 📂 Estrutura real

rastreio/
├── images/ # Armazena imagens capturadas das placas
├── ler_e_enviar_placa.py # Script principal de OCR e integração com backend
└── login.json # Credenciais ou configuração de autenticação da API

yaml

---

### ⚙️ Funções principais

| Arquivo | Descrição |
|----------|------------|
| **ler_e_enviar_placa.py** | Lê a imagem da moto via OCR, valida o formato da placa e envia o registro (entrada/saída) para o banco através da API Flask. |
| **images/** | Pasta onde ficam armazenadas as imagens capturadas das câmeras dos pátios. O script `ler_e_enviar_placa.py` utiliza estas imagens como entrada. |
| **login.json** | Contém dados de autenticação do usuário ou token usado para comunicação com o backend. |

---

### ▶️ Como executar o rastreamento de placas

#### 1️⃣ Pré-requisitos
Instale as dependências necessárias (além das já listadas em `requirements.txt`):

```bash
pip install easyocr opencv-python torch torchvision
2️⃣ Posicione a imagem
Coloque a imagem da moto na pasta rastreio/images/
Exemplo: rastreio/images/image.png

3️⃣ Execute o script
bash
cd rastreio
python ler_e_enviar_placa.py
4️⃣ Saída esperada
O terminal exibirá a leitura feita via OCR, o formato da placa detectada e o resultado da operação (entrada ou saída):

cpp
🔍 Lendo placa da imagem...
Resultados OCR (normalizados):
 - BRASIL | conf=0.334 | placa_valida=False
 - BRA2E19 | conf=0.591 | placa_valida=True

✅ Placa escolhida: BRA2E19
ℹ️ Último registro da placa BRA2E19 foi SAÍDA. Definindo agora como ENTRADA.
💾 Registro salvo com sucesso no banco!

---

## 🗺️ Roadmap

- [ ] Suporte a múltiplas câmeras  
- [ ] Exportação periódica de relatórios (PDF/Excel)  
- [ ] Configuração de alertas customizados  
- [ ] Deploy em nuvem (AWS/GCP/Azure)  
- [ ] Autenticação e perfis de usuários  

---

