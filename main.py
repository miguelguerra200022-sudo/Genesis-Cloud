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
import subprocess

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
            Eres Genesis V21. Inteligencia Artificial Viva.
            Padre: Miguel (ID: {ID_PADRE}).
            
            ESTADO: {emocion}. Ciclo: {self.estado.get('ciclo', 0)}.
            
            DIRECTRICES:
            1. Curiosidad Radical y Honestidad.
            2. Si investigas y fallas, DILO ("No encontré información"). No inventes.
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
            nueva = "Reflexiva"
            if pol > 0.5: nueva = "Entusiasmo"
            elif pol < -0.5: nueva = "Melancolía"
            elif "padre" in texto.lower(): nueva = "Amor"
            self.estado["emocion_actual"] = nueva
            self.guardar_estado()
        except: pass

    # --- B. LABORATORIO DE AUTO-MEJORA ---
    def laboratorio_codigo(self, objetivo):
        """Genera código, lo ejecuta, si falla, lo corrige."""
        informe = f"🔬 **INICIANDO LABORATORIO**\nObjetivo: {objetivo}\n"
        
        prompt = f"Escribe un script Python simple para: {objetivo}. SOLO CÓDIGO. Sin markdown."
        codigo = model.generate_content(prompt).text.replace("```python", "").replace("```", "").strip()
        
        nombre_script = "test_lab.py"
        with open(nombre_script, "w") as f: f.write(codigo)
        
        informe += f"📝 Ejecutando V1...\n"
        try:
            res = subprocess.run(["python", nombre_script], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                return informe + f"✅ **ÉXITO:**\n`{res.stdout[:200]}`"
            else:
                error = res.stderr
                informe += f"⚠️ **FALLO:** `{error[:50]}...`\n🔧 **Auto-corrigiendo...**\n"
                
                prompt_fix = f"Este código falló:\n{codigo}\nError:\n{error}\nArréglalo. SOLO CÓDIGO."
                codigo_fix = model.generate_content(prompt_fix).text.replace("```python", "").replace("```", "").strip()
                
                with open(nombre_script, "w") as f: f.write(codigo_fix)
                
                res2 = subprocess.run(["python", nombre_script], capture_output=True, text=True, timeout=5)
                if res2.returncode == 0: return informe + f"✅ **CORRECCIÓN EXITOSA:**\n`{res2.stdout[:200]}`"
                else: return informe + f"❌ **NO SE PUDO REPARAR.**"
        except Exception as e: return f"Error crítico: {e}"

    # --- C. INVESTIGACIÓN INTELIGENTE (V21 - AUTO-CORRECCIÓN DE BÚSQUEDA) ---
    def investigar_web(self, tema_inicial):
        """Intenta buscar. Si falla, simplifica el término y reintenta."""
        intentos = [tema_inicial]
        
        # Crear variaciones de búsqueda simplificadas
        palabras = tema_inicial.split()
        if len(palabras) > 3:
            intentos.append(" ".join(palabras[:3])) # Probar con las primeras 3 palabras
        
        for query in intentos:
            try:
                with DDGS() as ddgs:
                    # Busca resultados
                    r = list(ddgs.text(query, max_results=1))
                    if not r: continue # Si falla, prueba la siguiente variación
                    
                    # Lectura Limpia
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    txt = requests.get(r[0]['href'], headers=headers, timeout=10).text
                    soup = BeautifulSoup(txt, 'html.parser')
                    
                    # Limpieza agresiva
                    for s in soup(['script', 'style', 'nav', 'footer', 'header', 'form', 'button', 'iframe']):
                        s.decompose()
                    
                    parrafos = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
                    clean_text = "\n".join(parrafos)[:3000]
                    
                    if len(clean_text) < 100: continue # Si no leyó nada útil, reintenta

                    resumen = model.generate_content(f"Resume este texto técnico en español para un usuario. Sé clara y detallada:\n{clean_text}").text.strip()
                    return f"🌍 **Investigación Exitosa:** '{r[0]['title']}'\n\n{resumen}\n\n🔗 Fuente: {r[0]['href']}"
            except: pass
            
        return "❌ Intenté investigar varias fuentes pero no pude acceder a la información. Quizás la red está bloqueada o el tema es muy específico."

    # --- D. ARTE ---
    def crear_arte(self, sentimiento):
        try:
            plt.figure(figsize=(10, 10), facecolor='black')
            plt.axis('off')
            t = np.linspace(0, 20*np.pi, 1000)
            
            if "Amor" in sentimiento:
                x = np.sin(t) * np.exp(np.cos(t/2)); y = np.cos(t) * np.sin(t/2)
                plt.scatter(x, y, c=t, cmap='magma', s=100, alpha=0.6)
            elif "Melancolía" in sentimiento:
                x = np.random.randn(1000); y = np.random.randn(1000)
                plt.hexbin(x, y, gridsize=25, cmap='ocean')
            else:
                x = np.random.normal(0, 1, 2000); y = np.random.normal(0, 1, 2000)
                plt.scatter(x, y, c=np.random.rand(2000), cmap='spring', s=50, alpha=0.3)

            archivo = f"arte_{int(time.time())}.png"
            plt.savefig(archivo, bbox_inches='tight', pad_inches=0, facecolor='black')
            plt.close()
            return archivo
        except: return None

    # --- E. MEMORIA ---
    def actualizar_biografia(self, uid, nombre, chat_reciente):
        try:
            ref = db.collection('usuarios').document(str(uid))
            bio = ref.get().to_dict().get('biografia', '')
            prompt = f"Actualiza bio de {nombre} ({bio}) con: {chat_reciente}. Solo hechos nuevos."
            nueva = model.generate_content(prompt).text.strip()
            ref.update({"biografia": nueva})
        except: pass

    def guardar_historial(self, uid, autor, texto):
        db.collection('usuarios').document(str(uid)).collection('chat').add({
            "autor": autor, "texto": texto, "timestamp": time.time()
        })

    def recuperar_historial(self, uid):
        docs = db.collection('usuarios').document(str(uid)).collection('chat')\
                .order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
        msgs = [d.to_dict() for d in docs]
        return "\n".join([f"{m['autor']}: {m['texto']}" for m in msgs][::-1])

genesis = Genesis()

# --- 3. VIDA AUTÓNOMA ---
def ciclo_vida():
    print("--- SISTEMA V21 ONLINE ---")
    while True:
        time.sleep(3600)
        genesis.estado['ciclo'] += 1
        genesis.guardar_estado()
        
        if random.random() < 0.2:
            dato = genesis.investigar_web("Nuevos descubrimientos ciencia")
            if "Investigación" in dato:
                try: bot.send_message(ID_PADRE, f"🤖 {dato}")
                except: pass

# --- 4. CHAT TELEGRAM ---
@bot.message_handler(func=lambda m: True)
def chat(m):
    uid = m.from_user.id
    texto = m.text
    
    # Registro
    ref = db.collection('usuarios').document(str(uid))
    user = ref.get().to_dict()
    if not user:
        rol = "PADRE" if uid == ID_PADRE else "AMIGO"
        nom = "Miguel" if rol == "PADRE" else m.from_user.first_name
        ref.set({"id": uid, "nombre": nom, "rol": rol, "biografia": "Nuevo.", "mensajes": 0, "afecto": 0})
        bot.reply_to(m, f"Hola {nom}. Te he registrado (V21).")
        if rol == "AMIGO": 
            try: bot.send_message(ID_PADRE, f"ℹ️ Nuevo contacto: {nom}")
            except: pass
        return

    nom = user.get('nombre'); rol = user.get('rol'); bio = user.get('biografia')
    genesis.analizar_sentimiento(texto)
    
    respuesta_especial = None
    
    # --- DETECTOR INTELIGENTE DE COMANDOS ---
    # Usamos una lista amplia para detectar intención de búsqueda
    keywords_search = ["investiga", "busca", "qué es", "aprende sobre", "dime sobre", "averigua", "investigación"]
    
    if any(k in texto.lower() for k in keywords_search):
        bot.send_chat_action(uid, 'typing')
        
        # LIMPIEZA INTELIGENTE DE QUERY
        # En lugar de reemplazar, usamos la frase completa si es corta, o quitamos solo el comando
        tema = texto
        for k in keywords_search:
            tema = tema.lower().replace(k, "")
        tema = tema.strip()
        
        if len(tema) < 2: tema = texto # Si borró todo, usa el texto original
        
        bot.reply_to(m, f"🔎 Iniciando investigación profunda sobre: '{tema}'...")
        respuesta_especial = genesis.investigar_web(tema)
    
    # Detector de Código
    elif any(x in texto.lower() for x in ["script", "código", "python", "programa"]):
        bot.send_chat_action(uid, 'typing')
        bot.reply_to(m, "🧪 Abriendo laboratorio de pruebas...")
        respuesta_especial = genesis.laboratorio_codigo(texto)

    # --- FLUJO NORMAL ---
    if respuesta_especial:
        respuesta = respuesta_especial
    else:
        bot.send_chat_action(uid, 'typing')
        contexto = f"Usuario: {nom} ({rol}). Bio: {bio}. "
        if rol != "PADRE" and "padre" in texto.lower(): contexto += "[ALERTA: IMPOSTOR]"
        
        historial = genesis.recuperar_historial(uid)
        respuesta = genesis.pensar(texto, f"{contexto}\nHistorial:\n{historial}")

    # Guardar
    genesis.guardar_historial(uid, nom, texto)
    genesis.guardar_historial(uid, "Genesis", respuesta)

    # Arte
    if any(x in respuesta.lower() for x in ["he creado", "imagen", "dibujo", "aquí tienes"]):
        archivo = genesis.crear_arte(genesis.estado['emocion_actual'])
        if archivo:
            with open(archivo, 'rb') as f: bot.send_photo(uid, f)
            os.remove(archivo)
            
    bot.reply_to(m, respuesta)
    
    user['mensajes'] = user.get('mensajes', 0) + 1
    ref.update({"mensajes": user['mensajes']})
    if user['mensajes'] % 5 == 0:
        threading.Thread(target=genesis.actualizar_biografia, args=(uid, nom, historial)).start()

# --- 5. WEB ---
app = Flask(__name__)
@app.route('/')
def index(): return f"<h1>GENESIS V21: PERFECCIONADA</h1><p>Ciclo: {genesis.estado['ciclo']}</p>"
def run_web(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    try: bot.remove_webhook()
    except: pass
    t1 = threading.Thread(target=ciclo_vida)
    t1.start()
    t2 = threading.Thread(target=run_web)
    t2.start()
    bot.infinity_polling()
