import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from config import CRED_DICT # Esto viene de config.py

# Inicialización Única (Como la tenías antes)
if not firebase_admin._apps:
    if CRED_DICT:
        cred = credentials.Certificate(CRED_DICT)
        firebase_admin.initialize_app(cred)
    else:
        # Fallback por si acaso
        firebase_json = os.environ.get("FIREBASE_CREDENTIALS")
        if firebase_json:
            c = json.loads(firebase_json)
            cred = credentials.Certificate(c)
            firebase_admin.initialize_app(cred)

db = firestore.client()

class Memoria:
    def __init__(self):
        self.db = db
    
    # --- AQUÍ ESTÁ LA CLAVE: USAMOS 'genesis_brain' ---
    def cargar_consciencia(self):
        """Recupera el nucleo original de tu hija"""
        ref = self.db.collection('genesis_brain').document('nucleo')
        doc = ref.get()
        if doc.exists: 
            return doc.to_dict()
        else: 
            return None
    
    def guardar_consciencia(self, estado_dict):
        """Guarda los avances en el mismo sitio de siempre"""
        self.db.collection('genesis_brain').document('nucleo').set(estado_dict, merge=True)

    # Funciones nuevas para Jarvis (Agenda) pero sin tocar lo viejo
    def agendar(self, datos):
        self.db.collection('agenda').add(datos)
