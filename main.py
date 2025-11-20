import time
import threading
import telebot
import os
from system.sentidos import iniciar_organismo, bot, ejecutar_accion
from system.nucleo import Cerebro
from config import ID_PADRE

# Instanciamos cerebro compartido
genesis_life = Cerebro() 

def latido_autonomo():
    """
    El verdadero loop de vida. 
    - Revisa la agenda.
    - Decide si hablarte espontáneamente.
    - Gestiona su energía.
    """
    print("❤️ Latido JARVIS iniciado.")
    while True:
        time.sleep(60) # Revisa cada minuto (más preciso que antes)
        
        try:
            # 1. Revisar Agenda y Proactividad
            mensaje_proactivo = genesis_life.check_schedule()
            
            # 2. Si el cerebro tiene algo urgente que decir (Alarma o Noticia)
            if mensaje_proactivo and ID_PADRE != 0:
                # Usamos el bot importado para enviar mensaje push
                try:
                    bot.send_message(ID_PADRE, mensaje_proactivo)
                    print(f"🔔 Notificación enviada: {mensaje_proactivo}")
                except Exception as e:
                    print(f"No pude contactar al Padre: {e}")
            
            # 3. Envejecimiento natural
            genesis_life.estado['vida_dias'] += 0.0006
            genesis_life.memoria.guardar_consciencia(genesis_life.estado)
            
        except Exception as e:
            print(f"Arritmia en latido: {e}")

if __name__ == "__main__":
    # Importante: Asignamos el cerebro instanciado al módulo de sentidos para que compartan memoria RAM
    import system.sentidos
    system.sentidos.genesis = genesis_life 

    # Hilo de Vida Autónoma
    t_vida = threading.Thread(target=latido_autonomo)
    t_vida.daemon = True
    t_vida.start()
    
    # Inicio del sistema sensorial
    try:
        iniciar_organismo() # Esto inicia Flask y el Polling de Telegram
    except Exception as e:
        print(f"CRITICAL CRASH: {e}")
