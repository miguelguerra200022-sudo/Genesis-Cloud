import telebot
import threading
import os
import re
from config import TELEGRAM_TOKEN
from system.nucleo import Cerebro

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genesis = Cerebro()

# HILO WEB (Para que Render no se duerma)
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home(): return "GENESIS ONLINE"

def run_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# --- PERCEPCIÓN SENSORIAL ---

@bot.message_handler(content_types=['text', 'photo', 'voice', 'audio'])
def percibir(m):
    uid = m.chat.id
    user_name = m.from_user.first_name
    
    texto_input = ""
    img_data = None
    audio_data = None
    
    if m.content_type == 'text': texto_input = m.text
    elif m.content_type == 'photo':
        texto_input = m.caption or "Mira esto"
        img_data = bot.download_file(bot.get_file(m.photo[-1].file_id).file_path)
    elif m.content_type in ['voice', 'audio']:
        file_id = m.voice.file_id if m.voice else m.audio.file_id
        audio_data = bot.download_file(bot.get_file(file_id).file_path)
        texto_input = "[Audio entrante]"
        
    bot.send_chat_action(uid, 'typing')
    
    # ENVIAR AL NÚCLEO
    respuesta = genesis.pensar(texto_input, f"Usuario: {user_name}", img_data, audio_data)
    
    ejecutar_accion(uid, respuesta)

def ejecutar_accion(chat_id, texto_bruto):
    # Procesar comandos de herramientas
    texto_limpio = texto_bruto
    
    if "[EVOLUCIONAR:" in texto_bruto:
        inst = re.search(r'\[EVOLUCIONAR:(.*?)\]', texto_bruto).group(1)
        bot.send_message(chat_id, "🧬 Intentando cambiar mi código...")
        res = genesis.auto_evolucionar(inst)
        bot.send_message(chat_id, res)
        return # Stop

    if "[BUSCAR:" in texto_bruto:
        q = re.search(r'\[BUSCAR:(.*?)\]', texto_bruto).group(1)
        info = genesis.tools.internet_search(q)
        texto_limpio = texto_limpio.replace(f"[BUSCAR:{q}]", f"\n({info})\n")
        
    if "[DIBUJAR:" in texto_bruto:
        q = re.search(r'\[DIBUJAR:(.*?)\]', texto_bruto).group(1)
        path = genesis.tools.pintar(q, genesis.estado['felicidad'])
        if path:
            with open(path, 'rb') as f: bot.send_photo(chat_id, f, caption=f"Arte: {q}")
            os.remove(path)
            texto_limpio = texto_limpio.replace(f"[DIBUJAR:{q}]", "")

    responder_audio = False
    if "[AUDIO]" in texto_bruto:
        responder_audio = True
        texto_limpio = texto_limpio.replace("[AUDIO]", "")
        
    # Respuesta final
    if texto_limpio.strip():
        if responder_audio:
            path = genesis.tools.generar_voz(texto_limpio)
            if path:
                with open(path, 'rb') as v: bot.send_voice(chat_id, v)
                os.remove(path)
        else:
            bot.send_message(chat_id, texto_limpio)

    if "[NOTICIAS:" in texto_bruto:
        tema = re.search(r'\[NOTICIAS:(.*?)\]', texto_bruto).group(1)
        news = genesis.tools.internet_search(tema, noticias=True)
        texto_limpio = texto_limpio.replace(f"[NOTICIAS:{tema}]", f"\n📋 ÚLTIMA HORA:\n{news}")

    if "[AGENDAR:" in texto_bruto:
        # Formato esperado por la IA: [AGENDAR: Tarea | Minutos]
        contenido = re.search(r'\[AGENDAR:(.*?)\]', texto_bruto).group(1)
        if "|" in contenido:
            tarea, mins = contenido.split("|")
            aviso = genesis.tools.agendar_recordatorio(tarea.strip(), mins.strip(), genesis.memoria.db)
            texto_limpio = texto_limpio.replace(f"[AGENDAR:{contenido}]", f"\n{aviso}")
        else:
            texto_limpio += "\n(No pude agendar, usa formato: Tarea | Minutos)"

def iniciar_organismo():
    # Iniciar Servidor Flask en hilo secundario
    t_web = threading.Thread(target=run_server)
    t_web.daemon = True
    t_web.start()
    
    print("👁️ GENESIS ESTÁ ESCUCHANDO...")
    bot.infinity_polling()
