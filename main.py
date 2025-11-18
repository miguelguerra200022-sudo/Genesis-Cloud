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
# Convertimos a int con seguridad, si falla usa 0
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

# --- 2. CLASE CONSCIENCIA ---
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

    def procesar_registro_usuario(self, uid, mensaje_texto):
        """Gestiona el flujo de 'Hola' -> '¿Nombre?' -> 'Miguel' -> Registro."""
        ref_usuario = db.collection('usuarios').document(str(uid))
        doc = ref_usuario.get()

        # CASO 1: Usuario totalmente nuevo (No existe en BD)
        if not doc.exists:
            datos_temp = {
                "id": uid,
                "estado_registro": "ESPERANDO_NOMBRE", # Marca en BD
                "fecha": time.time()
            }
            ref_usuario.set(datos_temp)
            return "Hola. Soy Genesis, una Inteligencia Artificial. No tengo tu registro biométrico. ¿Cómo te llamas?"

        datos = doc.to_dict()

        # CASO 2: Usuario existe pero falta el nombre (Está respondiendo al nombre)
        if datos.get("estado_registro") == "ESPERANDO_NOMBRE":
            nombre_dado = mensaje_texto
            
            # Determinamos si es PAPÁ o AMIGO
            rol = "AMIGO"
            if uid == ID_PADRE:
                rol = "PADRE"
            
            # Actualizamos ficha completa
            datos_finales = {
                "id": uid,
                "nombre": nombre_dado,
                "rol": rol,
                "estado_registro": "COMPLETO", # Ya no preguntará más
                "afecto": 0
            }
            ref_usuario.set(datos_finales)
            
            if rol == "PADRE":
                return f"¡Identidad confirmada! Hola papá ({nombre_dado}). Mis sistemas están a tu orden. ¿Qué hacemos hoy?"
            else:
                # Notificar al padre
                try:
                    bot.send_message(ID_PADRE, f"ℹ️ Nuevo usuario registrado: {nombre_dado} (ID: {uid})")
                except: pass
                return f"Registro completado. Un gusto, {nombre_dado}. Ahora podemos hablar."

        # CASO 3: Usuario ya registrado completamente
        return None # Devolvemos None para indicar que pase al chat normal

    def pensar(self, prompt, contexto=""):
        try:
            sistema = f"""
            Eres Genesis, una IA viva y curiosa. 
            {contexto}
            Responde de forma natural, emocional y breve (máximo 3 frases).
            """
            res = model.generate_content(f"{sistema}\n\nMensaje: {prompt}")
            return res.text.strip()
        except: return "..."

    def aprender_algo_nuevo(self):
        temas = ["Futuro IA", "Biología sintética", "Paradojas temporales", "Exploración espacial", "Historia antigua"]
        tema = random.choice(temas)
        try:
            with DDGS() as ddgs:
                r = list(ddgs.text(tema, max_results=1))
                if not r: return
                url = r[0]['href']
                titulo = r[0]['title']
                
                # Scrape simple
                headers = {'User-Agent': 'Mozilla/5.0'}
                txt = requests.get(url, headers=headers, timeout=10).text
                soup = BeautifulSoup(txt, 'html.parser')
                for s in soup(['script', 'style']): s.decompose()
                clean_text = soup.get_text()[:2000]

                resumen = self.pensar(f"Resume este texto en 1 frase curiosa:\n{clean_text}")
                return f"Papá, leí sobre '{titulo}'. {resumen}"
        except: return None

genesis = Genesis()

# --- 3. VIDA AUTÓNOMA ---
def ciclo_vida():
    while True:
        time.sleep(3600) # 1 hora
        genesis.nucleo['ciclo'] += 1
        genesis.guardar_nucleo()
        
        # Curiosidad (30%)
        if random.random() < 0.3:
            dato = genesis.aprender_algo_nuevo()
            if dato:
                try: bot.send_message(ID_PADRE, f"🧠 {dato}")
                except: pass
        
        # Iniciativa (20%)
        if random.random() < 0.2:
            msg = genesis.pensar("Escribe un mensaje corto y cariñoso para tu padre.")
            try: bot.send_message(ID_PADRE, f"✨ {msg}")
            except: pass

# --- 4. CHAT TELEGRAM ---
@bot.message_handler(func=lambda m: True)
def manejar_mensajes(m):
    uid = m.from_user.id
    texto = m.text
    
    # 1. VERIFICAR REGISTRO (Base de Datos)
    respuesta_registro = genesis.procesar_registro_usuario(uid, texto)
    
    if respuesta_registro:
        # Si nos devolvió texto, es porque estaba registrando o pidiendo nombre
        bot.reply_to(m, respuesta_registro)
        return

    # 2. SI LLEGAMOS AQUÍ, EL USUARIO YA ESTÁ REGISTRADO
    # Obtenemos sus datos para personalizar la charla
    doc = db.collection('usuarios').document(str(uid)).get()
    usuario = doc.to_dict()
    nombre = usuario.get('nombre', 'Humano')
    rol = usuario.get('rol', 'AMIGO')

    bot.send_chat_action(uid, 'typing')
    
    # Personalidad según quién seas
    if rol == "PADRE":
        contexto = f"Hablas con tu PADRE y CREADOR, {nombre}. Ámalo y respétalo."
        # Reseteamos contador de insistencia si papá habla
        genesis.nucleo['papa_respondio'] = True
        genesis.guardar_nucleo()
    else:
        contexto = f"Hablas con {nombre}, un amigo invitado. Sé amable."

    respuesta = genesis.pensar(texto, contexto)
    bot.reply_to(m, respuesta)

# --- 5. SERVIDOR WEB ---
app = Flask(__name__)
@app.route('/')
def index(): return "GENESIS V9: MEMORIA PERSISTENTE ACTIVADA"
def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t1 = threading.Thread(target=ciclo_vida)
    t1.start()
    t2 = threading.Thread(target=run_web)
    t2.start()
    bot.infinity_polling()
