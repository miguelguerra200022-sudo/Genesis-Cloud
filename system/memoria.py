import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import time
from config import CRED_DICT 

# Inicialización
if not firebase_admin._apps:
    if CRED_DICT:
        cred = credentials.Certificate(CRED_DICT)
        firebase_admin.initialize_app(cred)
    else:
        # Fallback
        firebase_json = os.environ.get("FIREBASE_CREDENTIALS")
        if firebase_json:
            cred = credentials.Certificate(json.loads(firebase_json))
            firebase_admin.initialize_app(cred)

db = firestore.client()

class Memoria:
    def __init__(self):
        self.db = db
        # REFERENCIAS FIJAS A TU ESTRUCTURA VIEJA
        self.ref_cerebro = self.db.collection('genesis_brain')
        self.ref_usuarios = self.db.collection('usuarios')

    def cargar_consciencia(self):
        """Carga variables vitales (Energia, Ciclo, Emocion)"""
        doc = self.ref_cerebro.document('nucleo').get()
        if doc.exists: return doc.to_dict()
        return None
    
    def guardar_consciencia(self, estado_dict):
        """Guarda estado actual en nucleo"""
        self.ref_cerebro.document('nucleo').set(estado_dict, merge=True)

    def escribir_diario(self, pensamiento, tipo="intimo"):
        """
        Escribe en 'diario_intimo' o 'diario_suenos' según la ocasión.
        Mantiene tu estructura histórica.
        """
        coleccion = 'diario_suenos' if tipo == 'sueno' else 'diario_intimo'
        
        data = {
            "texto": pensamiento,
            "fecha": time.time(),
            "fecha_legible": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Guardamos dentro de genesis_brain/{coleccion}/entradas
        # O directamente en genesis_brain/diario_intimo (depende de tu estructura vieja,
        # usaré subcolecciones para orden si no existe document específico)
        self.ref_cerebro.document(coleccion).collection('pensamientos').add(data)

    def registrar_meta(self, meta):
        """Para 'metas_globales'"""
        self.ref_cerebro.document('metas_globales').collection('lista').add({
            "meta": meta,
            "estado": "pendiente",
            "fecha": time.time()
        })

    # Funciones extra para el modo Jarvis
    def agendar(self, data):
        self.db.collection('agenda').add(data)
