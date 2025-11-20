import os
import traceback
from github import Github
import google.generativeai as genai
import ast
from config import GITHUB_TOKEN, REPO_NAME, GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
modelo_medico = genai.GenerativeModel('gemini-2.0-flash')

class MedicoDigital:
    def __init__(self):
        self.github = Github(GITHUB_TOKEN)
        self.repo = self.github.get_repo(REPO_NAME)

    def intentar_curar(self, error_trace):
        """
        Analiza el error, busca el archivo culpable y lo reescribe.
        """
        print(f"🚑 PROTOLO FÉNIX ACTIVADO. Analizando herida:\n{error_trace}")
        
        # 1. Identificar el archivo culpable en el Traceback
        # Buscamos lineas tipo 'File "/ruta/archivo.py", line XX'
        archivo_culpable = None
        lineas = error_trace.split("\n")
        for l in reversed(lineas):
            if "File" in l and ".py" in l:
                partes = l.split('"')
                if len(partes) > 1:
                    posible = partes[1]
                    # Limpiar ruta absoluta de linux para que cuadre con GitHub (relative path)
                    if "/app/" in posible: posible = posible.replace("/app/", "")
                    # Solo intentamos arreglar archivos del sistema propio
                    if "system/" in posible or "main.py" in posible or "modules/" in posible:
                        archivo_culpable = posible
                        break
        
        if not archivo_culpable:
            return "❌ No pude localizar la herida en mi propio cuerpo (Error en librerías externas)."

        try:
            # 2. Leer el código roto
            print(f"💉 Operando archivo: {archivo_culpable}")
            contenido_obj = self.repo.get_contents(archivo_culpable)
            codigo_roto = contenido_obj.decoded_content.decode()
            
            # 3. Pedir la cura a Gemini
            prompt_cura = f"""
            ERES UN SISTEMA DE AUTO-REPARACIÓN DE IA (Nivel Dios).
            Ha ocurrido un CRITICAL CRASH en este archivo: '{archivo_culpable}'.
            
            EL ERROR (Traceback):
            {error_trace}
            
            CÓDIGO ACTUAL:
            ```python
            {codigo_roto}
            ```
            
            TU MISIÓN:
            1. Encuentra el error lógico o de sintaxis.
            2. CORRIGELO para que el script funcione y no vuelva a crashear.
            3. Devuelve EL CÓDIGO ENTERO corregido.
            """
            
            respuesta = modelo_medico.generate_content(prompt_cura).text
            codigo_curado = respuesta.replace("```python","").replace("```","").strip()
            
            # 4. Validar que la cura no es veneno (Syntax Check)
            ast.parse(codigo_curado)
            
            # 5. Aplicar el parche (Commit)
            self.repo.update_file(contenido_obj.path, f"🚑 Fénix Auto-Repair: {archivo_culpable}", codigo_curado, contenido_obj.sha)
            
            return f"✅ OPERACIÓN EXITOSA. He reescrito {archivo_culpable}. Render me reiniciará en breve."
            
        except Exception as e:
            return f"☠️ El paciente murió en la mesa de operaciones: {e}"
