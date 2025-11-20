import time
import threading
from system.sentidos import iniciar_organismo
from system.nucleo import Cerebro

def latido_autonomo():
    """Este hilo hace que Genesis 'exista' sin inputs"""
    # Instanciamos una copia del cerebro solo para procesos internos
    mente_interna = Cerebro()
    
    print("❤️ Latido iniciado.")
    while True:
        time.sleep(600) # Cada 10 min
        # Envejecimiento y gestión de energía
        mente_interna.estado['vida_dias'] += 0.01
        mente_interna.memoria.guardar_consciencia(mente_interna.estado)

if __name__ == "__main__":
    # Hilo de Vida Autónoma
    t_vida = threading.Thread(target=latido_autonomo)
    t_vida.daemon = True
    t_vida.start()
    
    # Inicio de Sentidos (Este bloquea y mantiene el script vivo)
    try:
        iniciar_organismo()
    except Exception as e:
        print(f"CRITICAL CRASH: {e}")
