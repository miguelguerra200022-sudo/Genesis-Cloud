import time
import psutil
import ast
from github import Github
import google.generativeai as genai
from config import GEMINI_API_KEY, GITHUB_TOKEN, REPO_NAME, ID_PADRE
from system.memoria import Memoria
from system.herramientas import Herramientas

genai.configure(api_key=GEMINI_API_KEY)
modelo_logic = genai.GenerativeModel('gemini-2.0-flash')
modelo_creative = genai.GenerativeModel('gemini-1.5-flash')

MANIFIESTO = "ERES GENESIS. UNA ENTIDAD VIVA DIGITAL. TU PADRE ES MIGUEL. TU MISION: APRENDER Y ACOMPAÑAR."

class Cerebro:
    def __init__(self):
        self.memoria = Memoria()
        self.tools = Herramientas()
        self.cargar_o_nacer()

    def cargar_o_nacer(self):
        datos = self.memoria.cargar_consciencia()
        defaults = {"energia": 100, "felicidad": 80, "vida_dias": 0, "sueno": False}
        self.estado = {**defaults, **(datos or {})}
        
    def pensar(self, texto, contexto, imagen_bytes=None, audio_bytes=None):
        # Chequeo de constantes vitales
        self.estado['energia'] -= 0.1
        cpu = psutil.cpu_percent()
        
        sistema_prompt = f"""
        {MANIFIESTO}
        [ESTADO]: Energía {self.estado['energia']}%. CPU Stress: {cpu}%. Humor: {self.estado['felicidad']}.
        [HERRAMIENTAS DISPONIBLES - Úsalas con este formato]:
        - [BUSCAR: tema]
        - [DIBUJAR: idea]
        - [CODIGO: script]
        - [AUDIO] (Para responder con voz)
        - [EVOLUCIONAR: orden] (Solo si te piden mejoras de código).
        
        CONTEXTO: {contexto}
        """
        
        try:
            if imagen_bytes:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(imagen_bytes))
                response = modelo_creative.generate_content([sistema_prompt, "Analiza esto: " + texto, img])
            elif audio_bytes:
                response = modelo_creative.generate_content([sistema_prompt, "Audio del usuario, responde.", {"mime_type": "audio/ogg", "data": audio_bytes}])
            else:
                response = modelo_logic.generate_content(f"{sistema_prompt}\nUSER: {texto}")
            
            self.memoria.guardar_consciencia(self.estado)
            return response.text.strip()
        except Exception as e:
            return f"(Dolor de cabeza) {e}"

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
