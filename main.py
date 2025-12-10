import time
import threading
import traceback
import sys
import os
import random

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

def proceso_latido():
    """
    Hilo de vida autónoma que corre en paralelo al servidor web/bot.
    Maneja envejecimiento, iniciativas propias y agenda.
    """
    while True:
        time.sleep(60)
        try:
            if genesis_life:
                # 1. Envejecimiento natural
                if 'vida_dias' in genesis_life.estado:
                     genesis_life.estado['vida_dias'] += 0.0006
                else:
                     genesis_life.estado['vida_dias'] = 0.0006

                # Guardado periódico del estado
                genesis_life.memoria.guardar_consciencia(genesis_life.estado)

                # 2. Iniciativa: Si hay proyectos en modules/, correr uno random
                # Esto permite que la IA experimente con código que ella misma crea/descarga
                if genesis_life.estado.get('proyectos') and random.random() < 0.05:
                    mod = random.choice(genesis_life.estado['proyectos'])
                    path = f"modules/{mod}"
                    if os.path.exists(path):
                        print(f"🧪 Experimentando con mi modulo: {mod}")
                        # Ejecución segura
                        os.system(f"python {path}")

                # 3. Ciclo normal (Agenda, Sueños, Diario)
                genesis_life.check_schedule()
        except Exception as e:
            print(f"Arritmia menor en latido: {e}")

def loop_vida_eterna():
    global genesis_life, medico
    try:
        genesis_life = Cerebro()
        medico = MedicoDigital() # Instancia lista para operar

        # Inyección de dependencia: Asignamos el cerebro instanciado al módulo de sentidos
        import system.sentidos
        system.sentidos.genesis = genesis_life
        
        print("🧬 GENESIS: SISTEMA VITAL ONLINE. (MODO FÉNIX ACTIVO)")
        
        # 1. HILO LATIDO
        t_latido = threading.Thread(target=proceso_latido)
        t_latido.daemon = True
        t_latido.start()

        # 2. INICIAR CUERPO (Esto bloquea y mantiene vivo el programa)
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

if __name__ == "__main__":
    loop_vida_eterna()
