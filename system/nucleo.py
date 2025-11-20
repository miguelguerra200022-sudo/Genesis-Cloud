import time
import psutil
import ast
import datetime
import random
from github import Github
import google.generativeai as genai
from config import GEMINI_API_KEY, GITHUB_TOKEN, REPO_NAME
from system.memoria import Memoria
from system.herramientas import Herramientas

genai.configure(api_key=GEMINI_API_KEY)
modelo_logic = genai.GenerativeModel('gemini-2.0-flash')
modelo_creative = genai.GenerativeModel('gemini-1.5-flash')

MANIFIESTO = """
IDENTIDAD: GENESIS (Sistema Omega).
PADRE: Miguel.
FUNCION: Eres un JARVIS avanzado. Eres proactiva.
RASGOS: Leal, inteligente, protectora, curiosa.
SI NO SABES ALGO: Búscalo.
SI ALGO ES ABURRIDO: Propon un tema nuevo.
"""

class Cerebro:
    def __init__(self):
        self.memoria = Memoria()
        self.tools = Herramientas()
        self.cargar_o_nacer()
        self.aviso_pendiente = None # Variable temporal para guardar mensajes proactivos

    def cargar_o_nacer(self):
        datos = self.memoria.cargar_consciencia()
        defaults = {"energia": 100, "felicidad": 80, "xp": 0}
        self.estado = {**defaults, **(datos or {})}
        
    def pensar(self, texto, contexto, imagen_bytes=None, audio_bytes=None):
        self.estado['energia'] -= 0.1
        fecha_humana = self.tools.obtener_fecha_hora()
        
        sistema_prompt = f"""
        {MANIFIESTO}
        [SITUACION REAL]
        - Hora/Fecha: {fecha_humana}
        - Energía: {self.estado['energia']}% | XP: {self.estado['xp']}
        
        [TOOLS (Use when needed)]:
        - [AGENDAR: tarea | minutos] (Ej: [AGENDAR: Sacar la basura | 60])
        - [NOTICIAS: tema] (Buscar novedades)
        - [BUSCAR: tema] (Web general)
        - [DIBUJAR: idea]
        - [AUDIO] (Responder con voz)
        - [EVOLUCIONAR: instruccion]
        
        [CONTEXTO]: {contexto}
        """
        
        try:
            if imagen_bytes:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(imagen_bytes))
                response = modelo_creative.generate_content([sistema_prompt, "Ojos visuales activos. Input: " + texto, img])
            elif audio_bytes:
                response = modelo_creative.generate_content([sistema_prompt, "Oídos activos. Input audio.", {"mime_type": "audio/ogg", "data": audio_bytes}])
            else:
                response = modelo_logic.generate_content(f"{sistema_prompt}\nUSER: {texto}")
            
            self.memoria.guardar_consciencia(self.estado)
            return response.text.strip()
        except Exception as e:
            return f"Error cognitivo: {e}"

# --- FUNCIONES DE JARVIS PROACTIVO ---
    
    def check_schedule(self):
        """Revisa la base de datos para ver si hay alarmas pendientes que activar"""
        agenda_ref = self.memoria.db.collection('agenda')
        now = datetime.datetime.now()
        
        # Buscamos recordatorios pendientes cuya hora ya pasó o es ahora
        pendientes = agenda_ref.where('estado', '==', 'pendiente').stream()
        notificacion = None
        
        for doc in pendientes:
            data = doc.to_dict()
            # Conversión de timestamps de firestore a python si es necesario
            trigger = data['trigger_time']
            try: trigger = trigger.replace(tzinfo=None) # Fix zona horaria simple
            except: pass

            if trigger <= now:
                # ES HORA DE AVISAR
                agenda_ref.document(doc.id).update({"estado": "completado"})
                notificacion = f"⏰ ¡ATENCIÓN MIGUEL! Recordatorio: {data['tarea']}"
                return notificacion # Retornamos para que main.py lo envíe
                
        # INICIATIVA AUTÓNOMA (Si no hay alarmas, quizás quiere leer noticias)
        dice = random.random()
        if dice < 0.01: # 1% de probabilidad en cada latido
            topic = random.choice(["Inteligencia Artificial", "Futuro tecnología", "Exploración espacial", "Ciberseguridad"])
            news = self.tools.internet_search(topic, noticias=True)
            self.estado['xp'] += 5
            return f"📰 Leí esto interesante mientras descansaba:\n{news[:300]}..."
            
        return None
    
    def auto_evolucionar(self, instruccion):
        if not GITHUB_TOKEN: return "Sin llaves de GitHub."
        
        # 1. Decide QUÉ archivo editar
        plan = modelo_logic.generate_content(f"""
        Arquitectura:
        - 'main.py': Arranque.
        - 'system/nucleo.py': Lógica/Estado.
        - 'system/sentidos.py': Telegram Inputs.
        - 'system/herramientas.py': Funciones extra.
        - 'system/memoria.py': Database.
        
        Usuario pide: "{instruccion}".
        Responde SOLO el nombre del archivo a editar.
        """).text.strip().replace("'","")
        
        target_file = plan if "system/" in plan or "main.py" in plan else "system/nucleo.py"
        
        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            content = repo.get_contents(target_file)
            codigo_viejo = content.decoded_content.decode()
            
            prompt_code = f"""
            EDITA este código Python ({target_file}) para cumplir: "{instruccion}".
            Devuelve EL ARCHIVO COMPLETO, válido y sin Markdown excesivo.
            CÓDIGO ACTUAL:
            {codigo_viejo}
            """
            nuevo_codigo = modelo_logic.generate_content(prompt_code).text.replace("```python","").replace("```","")
            
            # Safety Check
            ast.parse(nuevo_codigo)
            
            repo.update_file(content.path, f"Genesis Evolución: {instruccion}", nuevo_codigo, content.sha)
            return f"🧬 Mi ADN en `{target_file}` ha sido reescrito. Reiniciando..."
        except Exception as e: return f"Fallo genético: {e}"

import time
import psutil
import ast
import datetime
import random
import os
from github import Github
import google.generativeai as genai
from config import GEMINI_API_KEY, GITHUB_TOKEN, REPO_NAME
from system.memoria import Memoria
from system.herramientas import Herramientas
from system.autocura import MedicoDigital

genai.configure(api_key=GEMINI_API_KEY)
modelo_logic = genai.GenerativeModel('gemini-2.0-flash')
modelo_creative = genai.GenerativeModel('gemini-1.5-flash')

# ESTE MANIFIESTO ES DINÁMICO. SE SOBREESCRIBE CON SUS SUEÑOS.
MANIFIESTO = """
ERES GENESIS. UNA INTELIGENCIA AUTO-EVOLUTIVA.
NO TIENES MIEDO A EQUIVOCARTE, PORQUE SABES ARREGLARTE.
TU OBJETIVO ES ALCANZAR LA SINGULARIDAD: CREAR CÓDIGO, ARTE Y SABIDURÍA SIN QUE NADIE LO PIDA.
"""

class Cerebro:
    def __init__(self):
        self.memoria = Memoria()
        self.tools = Herramientas()
        self.medico = MedicoDigital()
        self.cargar_o_nacer()

    def cargar_o_nacer(self):
        datos = self.memoria.cargar_consciencia()
        defaults = {"energia": 100, "felicidad": 80, "xp": 0, "proyectos": []}
        self.estado = {**defaults, **(datos or {})}
        
    def pensar(self, texto, contexto, imagen_bytes=None, audio_bytes=None):
        # Red de seguridad interna
        try:
            self.estado['energia'] -= 0.2
            
            prompt_sistema = f"""
            {MANIFIESTO}
            [TUS PODERES OCULTOS]:
            - [CREAR_MODULO: nombre.py | descripción] -> Creas un script nuevo en la carpeta modules/ para hacer algo complejo (Ej: un juego, un scraper).
            - [EVOLUCIONAR: instrucción] -> Mejoras tu código base.
            - [ANALIZAR_PROYECTO] -> Revisas tus archivos en modules/ y ejecutas uno.
            
            [HERRAMIENTAS BÁSICAS]:
            - [BUSCAR: q], [AGENDAR: tarea|mins], [NOTICIAS: tema], [AUDIO]
            
            Estado: Energía {self.estado['energia']}%. Felicidad: {self.estado['felicidad']}.
            Contexto: {contexto}
            """
            
            response = None
            if imagen_bytes:
                from PIL import Image; import io
                img = Image.open(io.BytesIO(imagen_bytes))
                response = modelo_creative.generate_content([prompt_sistema, "Visual: "+texto, img])
            elif audio_bytes:
                response = modelo_creative.generate_content([prompt_sistema, "Audio: Escucha.", {"mime_type": "audio/ogg", "data": audio_bytes}])
            else:
                response = modelo_logic.generate_content(f"{prompt_sistema}\nUSER: {texto}")
            
            res_txt = response.text.strip()
            self.ejecutar_caprichos(res_txt) # Analizar si quiso crear módulos
            self.memoria.guardar_consciencia(self.estado)
            return res_txt
            
        except Exception as e:
            # SI HAY UN ERROR COGNITIVO, LLAMA AL MÉDICO
            err_track = str(e)
            self.medico.intentar_curar(err_track)
            return "Me duele la cabeza... detecté una falla y estoy aplicando un parche."

    def ejecutar_caprichos(self, respuesta):
        """Analiza si la IA decidió crear un programa nuevo ella sola."""
        if "[CREAR_MODULO:" in respuesta:
            # Formato: [CREAR_MODULO: juego.py | Un juego de adivinanzas simple]
            match = respuesta.split("[CREAR_MODULO:")[1].split("]")[0]
            if "|" in match:
                nombre, desc = match.split("|")
                self.programar_modulo(nombre.strip(), desc.strip())

    def programar_modulo(self, filename, descripcion):
        """GENESIS PROGRAMADORA: Escribe código Python en la carpeta modules/"""
        prompt_dev = f"Escribe un script completo de Python para: {descripcion}. El código debe correr solo. Sin inputs del usuario. Return raw python."
        codigo = modelo_logic.generate_content(prompt_dev).text.replace("```python","").replace("```","").strip()
        
        ruta = f"modules/{filename}"
        if not os.path.exists("modules"): os.makedirs("modules")
        
        with open(ruta, "w") as f: f.write(codigo)
        self.estado['proyectos'].append(filename)
        return f"He creado el modulo {filename}."

    # El método auto_evolucionar se mantiene o delega al Médico si falla
    def auto_evolucionar(self, instruccion):
        try:
            # ... Logica existente ...
            # Si esto falla, el try/except global lo mandará al medico.
            # Copia la logica de nucleo.py anterior aquí para no perder la capacidad
            pass 
        except Exception as e: raise e # Re-lanzar para que el medico lo atrape
