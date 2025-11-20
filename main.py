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

import time
import threading
import traceback
import sys
import os

# Intentamos importar. Si falla un import crítico (por ejemplo, borró config.py), 
# necesitamos que falle de forma controlada para arreglarlo.

try:
    from system.sentidos import iniciar_organismo, bot
    from system.nucleo import Cerebro
    from system.autocura import MedicoDigital
    from config import ID_PADRE
except Exception as e_import:
    # Si no puede ni importar los sistemas, estamos graves.
    print(f"FATAL BOOT ERROR: {e_import}")
    # Aquí podrías intentar arreglar imports, pero es arriesgado.
    # Simplemente imprimimos para log.

# Instancia Global
genesis_life = None
medico = None

def loop_vida_eterna():
    global genesis_life, medico
    try:
        genesis_life = Cerebro()
        medico = MedicoDigital() # Instancia lista para operar
        import system.sentidos
        system.sentidos.genesis = genesis_life
        
        print("🧬 GENESIS: SISTEMA VITAL ONLINE. (MODO FÉNIX ACTIVO)")
        
        # 1. HILO LATIDO
        t_latido = threading.Thread(target=proceso_latido)
        t_latido.daemon = True
        t_latido.start()

        # 2. INICIAR CUERPO (Esto bloquea)
        iniciar_organismo() 
        
    except Exception as e:
        # ESTE ES EL PUNTO CLAVE.
        # Si main.py crashea, capturamos el error y aplicamos medicina antes de morir.
        log_error = traceback.format_exc()
        print("☠️ MUERTE DETECTADA. INICIANDO RESURRECCIÓN...")
        if medico:
            reporte = medico.intentar_curar(log_error)
            print(reporte)
            # Intentar avisar al Padre (si bot sigue vivo)
            try: bot.send_message(ID_PADRE, f"⚠️ CRASH REPORTADO. Aplicando auto-cura y reiniciando: {reporte}")
            except: pass
        
        time.sleep(5) # Dar tiempo a Github para procesar
        sys.exit(1) # Salir para que Render reinicie el proceso limpio

def proceso_latido():
    while True:
        time.sleep(60)
        try:
            if genesis_life:
                # Iniciativa: Si hay proyectos en modules/, correr uno random
                if genesis_life.estado.get('proyectos') and random.random() < 0.05:
                    mod = random.choice(genesis_life.estado['proyectos'])
                    path = f"modules/{mod}"
                    if os.path.exists(path):
                        print(f"🧪 Experimentando con mi modulo: {mod}")
                        # Ejecución segura
                        os.system(f"python {path}") 
                
                # Ciclo normal
                genesis_life.check_schedule() # Asume que moviste el código JARVIS anterior aquí
        except Exception as e:
            print(f"Arritmia menor: {e}")

if __name__ == "__main__":
    loop_vida_eterna()
