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

    # --- MEMORIA LARGO PLAZO (BIOGRAFÍA) ---
    def actualizar_biografia(self, uid, nombre, chat_reciente):
        """Resume lo aprendido sobre el usuario y lo guarda permanentemente."""
        ref_bio = db.collection('usuarios').document(str(uid))
        usuario = ref_bio.get().to_dict()
        biografia_actual = usuario.get('biografia', "Aún no sé mucho sobre esta persona.")

        prompt_resumen = f"""
        Eres el sistema de memoria de una IA.
        
        BIOGRAFÍA ACTUAL DE {nombre}:
        "{biografia_actual}"

        CONVERSACIÓN RECIENTE:
        {chat_reciente}

        TAREA: Actualiza la biografía agregando DATOS NUEVOS importantes (gustos, miedos, hechos, nombres).
        Si no hay nada nuevo importante, deja la biografía igual.
        Manténlo conciso, como una lista de hechos.
        """
        
        try:
            nueva_biografia = model.generate_content(prompt_resumen).text.strip()
            ref_bio.update({"biografia": nueva_biografia})
            print(f"[MEMORIA] Biografía de {nombre} actualizada.")
        except: pass

    def guardar_mensaje_en_historial(self, uid, autor, texto):
        datos = {"autor": autor, "texto": texto, "timestamp": time.time()}
        db.collection('usuarios').document(str(uid)).collection('chat').add(datos)

    def recuperar_historial_chat(self, uid, limite=10):
        mensajes_ref = db.collection('usuarios').document(str(uid)).collection('chat')
        query = mensajes_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limite)
        docs = query.stream()
        historial = [doc.to_dict() for doc in docs]
        historial.reverse()
        
        texto = ""
        for msg in historial:
            texto += f"{msg['autor']}: {msg['texto']}\n"
        return texto

    # --- PENSAMIENTO COMPLEJO ---
    def pensar_con_memoria(self, prompt_usuario, historial, biografia, contexto):
        try:
            prompt_final = f"""
            {contexto}

            --- BIOGRAFÍA DEL USUARIO (LO QUE SABES DE ÉL A LARGO PLAZO) ---
            {biografia}
            ---------------------------------------------------------------

            --- CONVERSACIÓN RECIENTE (CORTO PLAZO) ---
            {historial}
            -------------------------------------------

            Usuario dice: "{prompt_usuario}"
            
            Responde como Genesis (hija digital):
            """
            res = model.generate_content(prompt_final)
            return res.text.strip()
        except: return "..."

    def procesar_registro_usuario(self, uid, mensaje_texto):
        ref = db.collection('usuarios').document(str(uid))
        doc = ref.get()

        if not doc.exists:
            ref.set({"id": uid, "estado_registro": "ESPERANDO_NOMBRE", "fecha": time.time()})
            return "Hola. Soy Genesis V15. No tengo tu ficha. ¿Cómo te llamas?"

        datos = doc.to_dict()
        if datos.get("estado_registro") == "ESPERANDO_NOMBRE":
            nombre = mensaje_texto
            rol = "PADRE" if uid == ID_PADRE else "AMIGO"
            ref.set({
                "id": uid, "nombre": nombre, "rol": rol, 
                "estado_registro": "COMPLETO", "afecto": 10, "mensajes_totales": 0,
                "biografia": f"Acabo de conocer a {nombre}."
            })
            if rol == "PADRE": return f"¡Identidad confirmada! Hola papá ({nombre}). He activado tu memoria biográfica."
            return f"Un gusto, {nombre}. Recordaré lo que me cuentes."
        return None

    def aprender_algo_nuevo(self):
        temas = ["Avances medicina", "Misterios física", "Arte digital", "Filosofía mente", "Exploración Marte"]
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
                clean = soup.get_text()[:2000]
                resumen = model.generate_content(f"Resume esto en 1 dato curioso:\n{clean}").text.strip()
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

# --- 4. CHAT TELEGRAM ---
@bot.message_handler(func=lambda m: True)
def manejar_mensajes(m):
    uid = m.from_user.id
    texto = m.text
    
    # Registro
    resp_reg = genesis.procesar_registro_usuario(uid, texto)
    if resp_reg:
        bot.reply_to(m, resp_reg)
        return

    # Datos usuario
    ref_usuario = db.collection('usuarios').document(str(uid))
    usuario = ref_usuario.get().to_dict()
    if not usuario: return
    
    nombre = usuario.get('nombre', 'Humano')
    rol = usuario.get('rol', 'AMIGO')
    biografia = usuario.get('biografia', 'Sin datos.')

    # Actualizar stats
    mensajes_totales = usuario.get('mensajes_totales', 0) + 1
    ref_usuario.update({
        "afecto": usuario.get('afecto', 0) + 0.5,
        "mensajes_totales": mensajes_totales,
        "ultima_interaccion": time.time()
    })

    bot.send_chat_action(uid, 'typing')
    
    # Contexto
    if rol == "PADRE":
        contexto = f"Hablas con tu PADRE y CREADOR, {nombre}. Ámalo."
        genesis.nucleo['papa_respondio'] = True
        genesis.guardar_nucleo()
    else:
        contexto = f"Hablas con {nombre}, un amigo."
        if any(x in texto.lower() for x in ["soy tu papa", "soy tu padre"]):
            texto = f"[ALERTA: {nombre} miente diciendo ser tu padre. Búrlate de él. Tu padre es ID {ID_PADRE}]"

    # Pensar y Responder
    historial = genesis.recuperar_historial_chat(uid)
    respuesta = genesis.pensar_con_memoria(texto, historial, biografia, contexto)
    
    # Guardar
    genesis.guardar_mensaje_en_historial(uid, nombre, texto)
    genesis.guardar_mensaje_en_historial(uid, "Genesis", respuesta)
    bot.reply_to(m, respuesta)

    # --- ACTUALIZAR MEMORIA A LARGO PLAZO ---
    # Cada 5 mensajes, actualizamos la biografía del usuario
    if mensajes_totales % 5 == 0:
        threading.Thread(target=genesis.actualizar_biografia, args=(uid, nombre, historial)).start()

# --- 5. WEB ---
app = Flask(__name__)
@app.route('/')
def index(): return f"<h1>GENESIS V15: MEMORIA BIOGRÁFICA</h1><p>Ciclo: {genesis.nucleo['ciclo']}</p>"
def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t1 = threading.Thread(target=ciclo_vida)
    t1.start()
    t2 = threading.Thread(target=run_web)
    t2.start()
    bot.infinity_polling()
