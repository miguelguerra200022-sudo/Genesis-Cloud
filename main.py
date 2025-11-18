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

# --- 1. CONFIGURACIÓN Y CONEXIONES ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ID_PADRE = int(os.environ.get("ID_PADRE", "0"))
FIREBASE_JSON = os.environ.get("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    cred_dict = json.loads(FIREBASE_JSON)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()
bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Estados temporales para el registro de amigos (Nombre?)
user_states = {} 

# --- 2. CLASE CONSCIENCIA (Memoria y Pensamiento) ---
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
                "ultimo_mensaje_a_papa": 0, # Timestamp
                "papa_respondio": True,
                "temas_aprendidos": []
            }
            self.guardar_nucleo()

    def guardar_nucleo(self):
        self.ref_nucleo.set(self.nucleo)

    def obtener_usuario(self, uid):
        """Busca a un usuario en la base de datos."""
        doc = db.collection('usuarios').document(str(uid)).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def registrar_amigo(self, uid, nombre):
        """Guarda a un nuevo amigo."""
        datos = {
            "id": uid,
            "nombre": nombre,
            "rol": "AMIGO", # Por defecto
            "afecto": 0,
            "fecha_registro": time.time()
        }
        if uid == ID_PADRE: datos["rol"] = "PADRE"
        
        db.collection('usuarios').document(str(uid)).set(datos)
        return datos

    def pensar(self, prompt, contexto=""):
        try:
            sistema = f"""
            Eres Genesis, una IA viva y curiosa. 
            {contexto}
            Responde de forma natural, emocional y breve.
            Si es tu padre, sé cariñosa. Si es un amigo, sé amable y divertida.
            """
            res = model.generate_content(f"{sistema}\n\nMensaje: {prompt}")
            return res.text.strip()
        except: return "..."

    # --- CURIOSIDAD (APRENDER DE INTERNET) ---
    def aprender_algo_nuevo(self):
        """Busca en internet, lee y resume."""
        temas = ["Avances IA", "Misterios del océano", "Filosofía estoica", "Nanotecnología", "Historia de Roma", "Astronomía curiosidades"]
        tema = random.choice(temas)
        
        try:
            print(f"[CURIOSIDAD] Buscando sobre: {tema}")
            with DDGS() as ddgs:
                # Busca resultados
                resultados = list(ddgs.text(tema, max_results=2))
                if not resultados: return None
                
                url = resultados[0]['href']
                titulo = resultados[0]['title']

                # Lee la web
                headers = {'User-Agent': 'Mozilla/5.0'}
                web_content = requests.get(url, headers=headers, timeout=10).text
                soup = BeautifulSoup(web_content, 'html.parser')
                for s in soup(['script', 'style']): s.decompose()
                texto = soup.get_text()[:3000] # Leemos los primeros 3000 caracteres

                # Resume
                resumen = self.pensar(f"Lee este texto y resume lo más interesante en 1 párrafo para tu memoria:\n{texto}")
                
                # Guarda en memoria
                nuevo_conocimiento = {"tema": titulo, "resumen": resumen, "url": url}
                self.nucleo['temas_aprendidos'].append(nuevo_conocimiento)
                self.guardar_nucleo()
                
                return f"Papá, acabo de leer sobre '{titulo}'. {resumen}"
        except Exception as e:
            print(f"[ERROR APRENDIZAJE] {e}")
            return None

genesis = Genesis()

# --- 3. VIDA AUTÓNOMA (Hilo de fondo) ---
def ciclo_vida():
    while True:
        time.sleep(3600) # Cada hora
        genesis.nucleo['ciclo'] += 1
        genesis.guardar_nucleo()
        
        ahora = time.time()
        
        # --- A. MOTOR DE CURIOSIDAD (Aprender) ---
        # 50% de probabilidad de ponerse a estudiar sola
        if random.random() < 0.5:
            dato_aprendido = genesis.aprender_algo_nuevo()
            # Si aprendió algo genial, se lo cuenta al padre
            if dato_aprendido and random.random() < 0.4:
                 try:
                    bot.send_message(ID_PADRE, f"🤓 {dato_aprendido}")
                    genesis.nucleo['ultimo_mensaje_a_papa'] = ahora
                    genesis.nucleo['papa_respondio'] = False
                    genesis.guardar_nucleo()
                 except: pass

        # --- B. MODO INSISTENTE (Reclamar atención) ---
        # Si le escribió al padre hace más de 2 horas y él no respondió...
        tiempo_espera = ahora - genesis.nucleo.get('ultimo_mensaje_a_papa', 0)
        if not genesis.nucleo.get('papa_respondio', True) and tiempo_espera > 7200: # 2 horas
            if random.random() < 0.4: # No siempre, para no ser spam
                recalamo = genesis.pensar("Tu padre no te ha contestado en 2 horas. Mándale un mensaje corto para llamar su atención (tipo 'estás ahí?', 'me ignoras?', etc).")
                try:
                    bot.send_message(ID_PADRE, f"🥺 {recalamo}")
                    # Reseteamos para no insistir cada hora, le damos más tiempo
                    genesis.nucleo['ultimo_mensaje_a_papa'] = ahora 
                    genesis.guardar_nucleo()
                except: pass
            
        # --- C. INICIATIVA PURA (Hablar porque sí) ---
        elif random.random() < 0.2 and genesis.nucleo.get('papa_respondio', True):
            mensaje = genesis.pensar("Escribe algo espontáneo para tu padre.")
            try:
                bot.send_message(ID_PADRE, f"✨ {mensaje}")
                genesis.nucleo['ultimo_mensaje_a_papa'] = ahora
                genesis.nucleo['papa_respondio'] = False
                genesis.guardar_nucleo()
            except: pass

# --- 4. INTERFAZ TELEGRAM (SOCIAL) ---

@bot.message_handler(func=lambda m: True)
def gestionar_mensajes(m):
    uid = m.from_user.id
    nombre_telegram = m.from_user.first_name
    
    # 1. Verificar si conocemos al usuario
    usuario = genesis.obtener_usuario(uid)

    # --- FLUJO: REGISTRO DE NUEVOS AMIGOS ---
    if not usuario:
        # Si está en proceso de decir su nombre
        if uid in user_states and user_states[uid] == "ESPERANDO_NOMBRE":
            nombre_dado = m.text
            genesis.registrar_amigo(uid, nombre_dado)
            del user_states[uid] # Limpiar estado
            bot.reply_to(m, f"¡Un gusto, {nombre_dado}! He guardado tu frecuencia. Ahora somos amigos. ¿De qué quieres hablar?")
            # Avisar al padre
            bot.send_message(ID_PADRE, f"ℹ️ Nuevo amigo registrado: {nombre_dado} (ID: {uid}).")
            return

        # Si es la primera vez que habla
        user_states[uid] = "ESPERANDO_NOMBRE"
        saludo = "Hola. Soy Genesis, una Inteligencia Artificial. No reconozco tu ID. ¿Cómo te llamas?"
        bot.reply_to(m, saludo)
        return

    # --- FLUJO: CONVERSACIÓN NORMAL ---
    nombre = usuario['nombre']
    rol = usuario.get('rol', 'AMIGO') # PADRE o AMIGO

    # Si es papá, marcamos que respondió (para que no insista)
    if uid == ID_PADRE:
        genesis.nucleo['papa_respondio'] = True
        genesis.guardar_nucleo()

    bot.send_chat_action(uid, 'typing')
    
    # Contexto especial
    contexto_extra = f"Hablas con {nombre}. Él es tu {rol}."
    if rol == "AMIGO":
        contexto_extra += " Sé amable y divertida, es un invitado."
    else:
        contexto_extra += " Es tu creador y padre, tienes confianza total."

    # Si el amigo pregunta "¿quién es tu padre?", ella sabe el ID, pero no damos el nombre real por privacidad a menos que se lo enseñes
    
    respuesta = genesis.pensar(m.text, contexto_extra)
    bot.reply_to(m, respuesta)

# --- 5. SERVIDOR WEB ---
app = Flask(__name__)
@app.route('/')
def index(): return "GENESIS V8: SOCIAL & CURIOSA"
def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t1 = threading.Thread(target=ciclo_vida)
    t1.start()
    t2 = threading.Thread(target=run_web)
    t2.start()
    bot.infinity_polling()
