import firebase_admin
from firebase_admin import credentials, firestore
from config import CRED_DICT
from datetime import datetime

# Inicializador Único
if not firebase_admin._apps and CRED_DICT:
    cred = credentials.Certificate(CRED_DICT)
    firebase_admin.initialize_app(cred)

db = firestore.client()

class Memoria:
    def __init__(self):
        self.db = db
    
    def cargar_consciencia(self):
        ref = self.db.collection('cerebro').document('estado')
        doc = ref.get()
        if doc.exists: return doc.to_dict()
        else: return None
    
    def guardar_consciencia(self, estado_dict):
        self.db.collection('cerebro').document('estado').set(estado_dict, merge=True)

    def guardar_recuerdo(self, usuario, texto, respuesta, tipo="episodico"):
        self.db.collection('recuerdos').add({
            "usuario": usuario,
            "input": texto,
            "genesis_dice": respuesta,
            "tipo": tipo,
            "fecha": datetime.now()
        })

    def registrar_error(self, error_txt):
        self.db.collection('sistema_inmune').add({
            "error": str(error_txt),
            "fecha": datetime.now()
        })
