import re
import json
import cv2
import easyocr
import oracledb

# ==============================
# CONFIGURAÇÕES
# ==============================
IMAGEM_PATH = "images/image.png"  
PATIO_NUMERO = 3
ENDERECO = "Pátio da Paulista"

# ==============================
# PADRÕES DE PLACAS BRASILEIRAS
# ==============================
PLATE_PATTERNS = [
    re.compile(r"^[A-Z]{3}\d{4}$"),        
    re.compile(r"^[A-Z]{3}\d[A-Z]\d{2}$"), 
]

def normalizar(texto: str) -> str:
    t = texto.upper()
    t = re.sub(r"[^A-Z0-9]", "", t)
    return t

def eh_placa_valida(c: str) -> bool:
    if not (6 <= len(c) <= 8):
        return False
    for pat in PLATE_PATTERNS:
        if pat.match(c):
            return True
    return False

# ==============================
# 1️⃣ LEITURA DA PLACA VIA OCR
# ==============================
print("🔍 Lendo placa da imagem...")
reader = easyocr.Reader(['pt', 'en'])
resultado = reader.readtext(IMAGEM_PATH, detail=1)

candidatos = []
for bbox, texto, conf in resultado:
    norm = normalizar(texto)
    candidatos.append((norm, conf))

validos = [(t, c) for (t, c) in candidatos if eh_placa_valida(t)]
validos.sort(key=lambda x: x[1], reverse=True)

print("\nResultados OCR (normalizados):")
for t, c in candidatos:
    print(f" - {t:>10} | conf={c:.3f} | placa_valida={eh_placa_valida(t)}")

if not validos:
    print("\n❌ Nenhuma placa válida foi detectada.")
    raise SystemExit(1)

placa_detectada = validos[0][0]
print(f"\n✅ Placa escolhida: {placa_detectada}")

# ==============================
# 2️⃣ CONEXÃO COM ORACLE
# ==============================
with open('login.json', 'r') as f:
    info = json.load(f)
    login = info["login"]
    senha = info["senha"]

dsn = oracledb.makedsn(
    host='oracle.fiap.com.br',
    port=1521,
    sid='ORCL'
)

conn = oracledb.connect(user=login, password=senha, dsn=dsn)
cursor = conn.cursor()

# ==============================
# 3️⃣ VERIFICA SE A PLACA EXISTE E DEFINE ENTRADA/SAÍDA
# ==============================
cursor.execute("""
    SELECT TIPO_REGISTRO
    FROM MOTOS_PATIO
    WHERE PLACA = :1
    ORDER BY ID DESC
""", (placa_detectada,))

ultimo_registro = cursor.fetchone()

if ultimo_registro is None:
    tipo_registro = "ENTRADA"
    print(f"ℹ️ Placa {placa_detectada} ainda não registrada. Definindo como ENTRADA.")
elif ultimo_registro[0] == "ENTRADA":
    tipo_registro = "SAIDA"
    print(f"ℹ️ Último registro da placa {placa_detectada} foi ENTRADA. Definindo agora como SAÍDA.")
else:
    tipo_registro = "ENTRADA"
    print(f"ℹ️ Último registro da placa {placa_detectada} foi SAÍDA. Definindo agora como ENTRADA.")

# ==============================
# 4️⃣ INSERE NOVO REGISTRO NO BANCO
# ==============================
cursor.execute("""
    INSERT INTO MOTOS_PATIO (PLACA, PATIO_NUMERO, ENDERECO, TIPO_REGISTRO)
    VALUES (:1, :2, :3, :4)
""", (placa_detectada, PATIO_NUMERO, ENDERECO, tipo_registro))
conn.commit()

print(f"🚀 Registro inserido: {placa_detectada} | {tipo_registro} | Pátio {PATIO_NUMERO} | {ENDERECO}")

# ==============================
# 5️⃣ LISTA TODOS OS REGISTROS
# ==============================
cursor.execute("""
    SELECT ID, PLACA, PATIO_NUMERO, ENDERECO, TIPO_REGISTRO, DATA_REGISTRO
    FROM MOTOS_PATIO
    ORDER BY ID DESC
""")
rows = cursor.fetchall()

print("\n=== MOTOS CADASTRADAS ===")
for r in rows:
    print(f"ID: {r[0]} | Placa: {r[1]} | Tipo: {r[4]} | Pátio: {r[2]} | Endereço: {r[3]} | Data: {r[5]}")

cursor.close()
conn.close()
