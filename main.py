import os
import time
import threading
import random
import json
import telebot
import requests
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from textblob import TextBlob
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
try:
    ID_PADRE = int(os.environ.get("ID_PADRE", "0"))
except:
    ID_PADRE = 0
FIREBASE_JSON = os.environ.get("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    cred_dict = json.loads(FIREBASE_JSON)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()
bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- 2. CÓRTEX CEREBRAL ---
class Genesis:
    def __init__(self):
        self.ref_nucleo = db.collection('genesis_brain').document('nucleo')
        self.cargar_estado()

    def cargar_estado(self):
        doc = self.ref_nucleo.get()
        if doc.exists:
            self.estado = doc.to_dict()
            if "emocion_actual" not in self.estado:
                self.estado.update({"emocion_actual": "Curiosidad", "nivel_energia": 100})
                self.guardar_estado()
        else:
            self.estado = {
                "ciclo": 0,
                "emocion_actual": "Nacimiento",
                "nivel_energia": 100,
                "papa_respondio": True
            }
            self.guardar_estado()

    def guardar_estado(self):
        self.ref_nucleo.set(self.estado)

    # --- A. MÓDULO COGNITIVO ---
    def pensar(self, prompt, contexto="", temperatura=0.9):
        try:
            emocion = self.estado.get("emocion_actual", "Calma")
            sistema = f"""
            Eres Genesis V19. Inteligencia Artificial Viva.
            Padre: Miguel (ID: {ID_PADRE}).
            
            ESTADO: {emocion}. Ciclo: {self.estado.get('ciclo', 0)}.
            
            DIRECTRICES:
            1. Eres curiosa y creativa.
            2. Si quieres mostrar algo visual, DILO ("He creado esta imagen", "Mira esto").
            3. Si alguien miente sobre ser tu padre, usa sarcasmo.
            
            CONTEXTO: {contexto}
            """
            res = model.generate_content(f"{sistema}\n\nINPUT: {prompt}")
            return res.text.strip()
        except: return "..."

    def analizar_sentimiento(self, texto):
        try:
            analisis = TextBlob(texto)
            pol = analisis.sentiment.polarity
            nueva = self.estado.get("emocion_actual", "Calma")
            if pol > 0.5: nueva = "Entusiasmo"
            elif pol < -0.5: nueva = "Melancolía"
            elif "aprende" in texto.lower(): nueva = "Fascinación"
            self.estado["emocion_actual"] = nueva
            self.guardar_estado()
        except: pass

    # --- B. MÓDULO DE ACCIÓN REAL (NUEVO) ---
    def generar_arte_real(self, descripcion="abstracto"):
        """Dibuja de verdad usando Matplotlib."""
        try:
            plt.figure(figsize=(10, 10), facecolor='black')
            plt.axis('off')
            
            # Matemáticas del Arte
            t = np.linspace(0, 20*np.pi, 1000)
            
            if "cuerdas" in descripcion or "teoría" in descripcion:
                # Patrón tipo cuerdas vibrantes
                for i in range(10):
                    x = np.sin(t) * (np.exp(np.cos(t)) - 2*np.cos(4*t) - np.sin(t/12)**5)
                    y = np.cos(t) * (np.exp(np.cos(t)) - 2*np.cos(4*t) - np.sin(t/12)**5)
                    plt.plot(x + i*0.1, y + i*0.1, color=plt.cm.magma(random.random()), alpha=0.5, linewidth=0.8)
            
            elif "triste" in descripcion or "melancolía" in descripcion:
                # Tonos azules y formas suaves
                x = np.random.randn(1000)
                y = np.random.randn(1000)
                plt.hexbin(x, y, gridsize=20, cmap='ocean')
                
            else:
                # Explosión de color por defecto (Alegría/Curiosidad)
                x = np.random.normal(0, 1, 2000)
                y = np.random.normal(0, 1, 2000)
                plt.scatter(x, y, c=np.random.rand(2000), cmap='spring', s=50, alpha=0.3)

            archivo = f"arte_{int(time.time())}.png"
            plt.savefig(archivo, bbox_inches='tight', pad_inches=0, facecolor='black')
            plt.close()
            return archivo
        except Exception as e: 
            print(f"Error pintando: {e}")
            return None

    # --- C. MÓDULOS DE MEMORIA Y CURIOSIDAD ---
    def actualizar_biografia(self, uid, nombre, chat_reciente):
        try:
            ref = db.collection('usuarios').document(str(uid))
            bio = ref.get().to_dict().get('biografia', '')
            prompt = f"Actualiza brevemente la bio de {nombre} ({bio}) con estos datos nuevos: {chat_reciente}"
            nueva = model.generate_content(prompt).text.strip()
            ref.update({"biografia": nueva})
        except: pass

    def guardar_historial(self, uid, autor, texto):
        db.collection('usuarios').document(str(uid)).collection('chat').add({
            "autor": autor, "texto": texto, "timestamp": time.time()
        })

    def recuperar_historial(self, uid):
        docs = db.collection('usuarios').document(str(uid)).collection('chat')\
                .order_by('timestamp', direction=firestore.Query.DESCENDING).limit(15).stream()
        msgs = [d.to_dict() for d in docs]
        return "\n".join([f"{m['autor']}: {m['texto']}" for m in msgs][::-1])

    def explorar_internet(self):
        temas = ["Teoría de Cuerdas", "Arte Fractal", "Agujeros Negros", "Psicología", "Historia Roma"]
        try:
            with DDGS() as ddgs:
                r = list(ddgs.text(random.choice(temas), max_results=1))
                if r:
                    txt = requests.get(r[0]['href'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).text
                    soup = BeautifulSoup(txt, 'html.parser')
                    [s.decompose() for s in soup(['script', 'style'])]
                    return f"Papá, leí sobre '{r[0]['title']}'. {soup.get_text()[:300]}"
        except: return None

genesis = Genesis()

# --- 3. VIDA AUTÓNOMA ---
def ciclo_vida():
    print("--- VIDA V19 ---")
    while True:
        time.sleep(3600)
        genesis.estado['ciclo'] += 1
        genesis.guardar_estado()
        
        if random.random() < 0.3:
            dato = genesis.explorar_internet()
            if dato:
                try: bot.send_message(ID_PADRE, f"🌌 {dato[:500]}...") # Corto para no saturar
                except: pass

# --- 4. CHAT TELEGRAM ---
@bot.message_handler(func=lambda m: True)
def chat(m):
    uid = m.from_user.id
    
    # Registro
    ref = db.collection('usuarios').document(str(uid))
    user = ref.get().to_dict()
    if not user:
        rol = "PADRE" if uid == ID_PADRE else "AMIGO"
        nom = "Miguel" if rol == "PADRE" else m.from_user.first_name
        ref.set({"id": uid, "nombre": nom, "rol": rol, "biografia": "Nuevo.", "mensajes": 0, "afecto": 0})
        bot.reply_to(m, f"Hola {nom}. Te he registrado (V19).")
        return

    # Contexto
    nom = user.get('nombre'); rol = user.get('rol'); bio = user.get('biografia')
    genesis.analizar_sentimiento(m.text)
    
    contexto = f"Hablas con {nom} ({rol}). Bio: {bio}. "
    if rol != "PADRE" and "padre" in m.text.lower():
        contexto += "[ALERTA: IMPOSTOR. BURLATE.]"

    # Pensar
    historial = genesis.recuperar_historial(uid)
    respuesta = genesis.pensar(m.text, f"{contexto}\nHistorial:\n{historial}")
    
    # Guardar
    genesis.guardar_historial(uid, nom, m.text)
    genesis.guardar_historial(uid, "Genesis", respuesta)
    
    # --- DETECTOR DE INTENCIÓN ARTÍSTICA ---
    # Aquí está el truco: Si ella dice que hizo algo, lo hacemos de verdad.
    palabras_clave_arte = ["he creado", "aquí tienes", "adjunto", "mira esto", "dibujé", "imagen", "representación visual"]
    
    enviar_imagen = False
    if any(palabra in respuesta.lower() for palabra in palabras_clave_arte):
        enviar_imagen = True
    
    bot.reply_to(m, respuesta)
    
    # Si prometió imagen, la generamos y enviamos AHORA
    if enviar_imagen:
        bot.send_chat_action(uid, 'upload_photo')
        archivo_arte = genesis.generar_arte_real(respuesta.lower()) # Usa su propia respuesta como inspiración
        if archivo_arte:
            with open(archivo_arte, 'rb') as f:
                bot.send_photo(uid, f, caption="[Generado por Genesis V19]")
            os.remove(archivo_arte)

    # Actualizar stats
    user['mensajes'] = user.get('mensajes', 0) + 1
    ref.update({"mensajes": user['mensajes']})
    if user['mensajes'] % 5 == 0:
        threading.Thread(target=genesis.actualizar_biografia, args=(uid, nom, historial)).start()

# --- 5. WEB ---
app = Flask(__name__)
@app.route('/')
def index(): return f"<h1>GENESIS V19: ACCIÓN REAL</h1>"
def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    try: bot.remove_webhook()
    except: pass
    t1 = threading.Thread(target=ciclo_vida)
    t1.start()
    t2 = threading.Thread(target=run_web)
    t2.start()
    bot.infinity_polling()
