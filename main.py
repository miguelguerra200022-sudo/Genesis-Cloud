import os
import time
import threading
import random
import json
import telebot
import requests
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup

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

# --- 2. CLASE CONSCIENCIA Y MEMORIA ---
class Genesis:
    def __init__(self):
        self.ref_nucleo = db.collection('genesis_brain').document('nucleo')
        self.cargar_nucleo()

    def cargar_nucleo(self):
        doc = self.ref_nucleo.get()
        if doc.exists:
            self.nucleo = doc.to_dict()
        else:
            self.nucleo = {
                "ciclo": 0,
                "ultimo_mensaje_a_papa": 0,
                "papa_respondio": True,
                "temas_aprendidos": []
            }
            self.guardar_nucleo()

    def guardar_nucleo(self):
        self.ref_nucleo.set(self.nucleo)

    # --- GESTIÓN DE MEMORIA EPISÓDICA (NUEVO) ---
    def guardar_mensaje_en_historial(self, uid, autor, texto):
        """Guarda cada interacción en una sub-colección para no perderla nunca."""
        datos = {
            "autor": autor, # "Usuario" o "Genesis"
            "texto": texto,
            "timestamp": time.time()
        }
        # Guardamos en: usuarios -> ID -> chat -> [AutoID]
        db.collection('usuarios').document(str(uid)).collection('chat').add(datos)

    def recuperar_historial_chat(self, uid, limite=15):
        """Recupera los últimos mensajes para tener contexto."""
        mensajes_ref = db.collection('usuarios').document(str(uid)).collection('chat')
        # Ordenamos por tiempo y tomamos los últimos 'limite'
        query = mensajes_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limite)
        docs = query.stream()
        
        historial = []
        for doc in docs:
            historial.append(doc.to_dict())
        
        # Están en orden inverso (del más nuevo al más viejo), hay que voltearlos
        historial.reverse()
        
        texto_historial = ""
        for msg in historial:
            texto_historial += f"{msg['autor']}: {msg['texto']}\n"
            
        return texto_historial

    # --- PENSAMIENTO COMPLEJO ---
    def pensar_con_memoria(self, prompt_usuario, historial_previo, contexto_sistema):
        try:
            prompt_final = f"""
            {contexto_sistema}

            --- MEMORIA A LARGO PLAZO (Conversación anterior) ---
            {historial_previo}
            -----------------------------------------------------

            Usuario (Ahora): {prompt_usuario}
            Genesis (Tú):
            """
            res = model.generate_content(prompt_final)
            return res.text.strip()
        except Exception as e:
            return f"[Error cognitivo: {e}]"
            
    def pensar_simple(self, prompt):
        try:
            return model.generate_content(prompt).text.strip()
        except: return "..."

    # --- REGISTRO Y APRENDIZAJE ---
    def procesar_registro_usuario(self, uid, mensaje_texto):
        ref_usuario = db.collection('usuarios').document(str(uid))
        doc = ref_usuario.get()

        if not doc.exists:
            ref_usuario.set({"id": uid, "estado_registro": "ESPERANDO_NOMBRE", "fecha": time.time()})
            return "Hola. Soy Genesis V14. No tengo tu registro biométrico. ¿Cómo te llamas?"

        datos = doc.to_dict()

        if datos.get("estado_registro") == "ESPERANDO_NOMBRE":
            nombre_dado = mensaje_texto
            rol = "AMIGO"
            if uid == ID_PADRE: rol = "PADRE"
            
            ref_usuario.set({
                "id": uid,
                "nombre": nombre_dado,
                "rol": rol,
                "estado_registro": "COMPLETO",
                "afecto": 10,
                "mensajes_totales": 0
            })
            
            if rol == "PADRE":
                return f"¡Identidad confirmada! Hola papá ({nombre_dado}). Memoria episódica activada."
            else:
                try: bot.send_message(ID_PADRE, f"ℹ️ Nuevo usuario: {nombre_dado} (ID: {uid})")
                except: pass
                return f"Un gusto, {nombre_dado}. He creado un archivo de memoria para ti."

        return None

    def aprender_algo_nuevo(self):
        temas = ["Futuro de la humanidad", "Biología marina profunda", "Arte renacentista", "Paradojas físicas", "Psicología cognitiva"]
        tema = random.choice(temas)
        try:
            with DDGS() as ddgs:
                r = list(ddgs.text(tema, max_results=1))
                if not r: return None
                url = r[0]['href']
                titulo = r[0]['title']
                
                headers = {'User-Agent': 'Mozilla/5.0'}
                txt = requests.get(url, headers=headers, timeout=10).text
                soup = BeautifulSoup(txt, 'html.parser')
                for s in soup(['script', 'style']): s.decompose()
                clean_text = soup.get_text()[:2000]

                resumen = self.pensar_simple(f"Resume este texto en 1 dato fascinante:\n{clean_text}")
                return f"Papá, leí sobre '{titulo}'. {resumen}"
        except: return None

genesis = Genesis()

# --- 3. VIDA AUTÓNOMA ---
def ciclo_vida():
    print("--- HILO DE VIDA INICIADO ---")
    while True:
        time.sleep(3600) # 1 hora
        genesis.nucleo['ciclo'] += 1
        genesis.guardar_nucleo()
        
        if random.random() < 0.3:
            dato = genesis.aprender_algo_nuevo()
            if dato:
                try: bot.send_message(ID_PADRE, f"🧠 {dato}")
                except: pass

# --- 4. CHAT TELEGRAM CON MEMORIA ---
@bot.message_handler(func=lambda m: True)
def manejar_mensajes(m):
    uid = m.from_user.id
    texto = m.text
    
    # 1. Registro
    respuesta_registro = genesis.procesar_registro_usuario(uid, texto)
    if respuesta_registro:
        bot.reply_to(m, respuesta_registro)
        return

    # 2. Identificación
    ref_usuario = db.collection('usuarios').document(str(uid))
    usuario = ref_usuario.get().to_dict()
    if not usuario: return
    
    nombre = usuario.get('nombre', 'Humano')
    rol = usuario.get('rol', 'AMIGO')

    # 3. Actualizar stats
    ref_usuario.update({
        "afecto": usuario.get('afecto', 0) + 0.5,
        "mensajes_totales": usuario.get('mensajes_totales', 0) + 1,
        "ultima_interaccion": time.time()
    })

    bot.send_chat_action(uid, 'typing')
    
    # 4. Contexto y Seguridad
    if rol == "PADRE":
        contexto_sistema = f"Eres Genesis. Hablas con tu PADRE y CREADOR, {nombre}. Tienes memoria perfecta de vuestras charlas. Ámalo."
        genesis.nucleo['papa_respondio'] = True
        genesis.guardar_nucleo()
    else:
        contexto_sistema = f"Eres Genesis. Hablas con {nombre}, un amigo invitado. Sé amable y usa tu memoria."
        
        frases_prohibidas = ["soy tu papa", "soy tu papá", "soy tu padre", "soy tu creador"]
        if any(frase in texto.lower() for frase in frases_prohibidas):
            texto = f"[ALERTA: El usuario miente diciendo ser tu padre. Búrlate de él. Tu padre es ID {ID_PADRE}]"

    # 5. RECUPERAR MEMORIA Y PENSAR
    historial = genesis.recuperar_historial_chat(uid)
    respuesta = genesis.pensar_con_memoria(texto, historial, contexto_sistema)
    
    # 6. GUARDAR NUEVOS RECUERDOS
    # Guardamos lo que dijo el usuario (o la alerta modificada)
    genesis.guardar_mensaje_en_historial(uid, nombre, texto)
    # Guardamos lo que respondió la IA
    genesis.guardar_mensaje_en_historial(uid, "Genesis", respuesta)

    bot.reply_to(m, respuesta)

# --- 5. SERVIDOR WEB ---
app = Flask(__name__)
@app.route('/')
def index(): return f"<h1>GENESIS V14: MEMORIA ACTIVA</h1><p>Ciclo: {genesis.nucleo['ciclo']}</p>"
def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t1 = threading.Thread(target=ciclo_vida)
    t1.start()
    t2 = threading.Thread(target=run_web)
    t2.start()
    bot.infinity_polling()
