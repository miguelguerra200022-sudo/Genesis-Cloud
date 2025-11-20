import subprocess
from duckduckgo_search import DDGS
from PIL import Image, ImageDraw, ImageFilter
from gtts import gTTS
import random
import time
import datetime
from firebase_admin import firestore

# Para los cálculos de fecha
import locale
try: locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except: pass

class Herramientas:
    def __init__(self):
        pass

    def internet_search(self, query, noticias=False):
        """Busca en la web normal o específicamente noticias"""
        try:
            with DDGS() as ddgs:
                if noticias:
                    res = list(ddgs.news(query, max_results=3))
                    texto = ""
                    for n in res:
                        texto += f"- {n['title']} (Fuente: {n['source']})\n"
                    return texto if texto else "No hay noticias relevantes."
                else:
                    res = list(ddgs.text(query, max_results=1))
                    return res[0]['body'] + f" (Link: {res[0]['href']})" if res else "Red vacía."
        except Exception as e: return f"Error web: {e}"

    def agendar_recordatorio(self, tarea, minutos_espera, db_ref):
        """Crea un recordatorio futuro en la base de datos"""
        tiempo_futuro = datetime.datetime.now() + datetime.timedelta(minutes=float(minutos_espera))
        db_ref.collection('agenda').add({
            "tarea": tarea,
            "trigger_time": tiempo_futuro,
            "estado": "pendiente"
        })
        return f"⏰ He guardado tu recordatorio para las {tiempo_futuro.strftime('%H:%M')}."

    def obtener_fecha_hora(self):
        return datetime.datetime.now().strftime("Hoy es %A %d de %B, son las %H:%M horas.")

    # ... MANTENER LAS FUNCIONES ANTIGUAS DE EJECUTAR CODIGO, PINTAR Y GENERAR VOZ AQUÍ ABAJO ...
    def ejecutar_codigo(self, codigo_py):
        archivo = "temp_lab.py"
        with open(archivo, "w") as f: f.write(codigo_py)
        try:
            res = subprocess.run(["python", archivo], capture_output=True, text=True, timeout=5)
            return f"OUTPUT: {res.stdout}\nERROR: {res.stderr}"
        except Exception as e: return f"Fallo ejecución: {e}"

    def pintar(self, prompt, felicidad_nivel):
        try:
            img = Image.new('RGB', (1024, 1024), color='black')
            draw = ImageDraw.Draw(img)
            base_r = 255 if felicidad_nivel > 50 else 50
            for _ in range(150):
                coords = [random.randint(0,1024) for _ in range(4)]
                draw.line(coords, fill=(base_r, random.randint(0,255), random.randint(100,255)), width=3)
            path = f"arte_{int(time.time())}.png"
            img.save(path)
            return path
        except: return None

    def generar_voz(self, texto):
        try:
            path = "voz_temp.ogg"
            tts = gTTS(texto, lang='es', tld='com.mx')
            tts.save(path)
            return path
        except: return None
