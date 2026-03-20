import streamlit as st
import google.generativeai as genai
import urllib.parse
from PIL import Image
import os

# --- 1. CONFIGURACIÓN DE PÁGINA (MOBILE-FIRST) ---
st.set_page_config(
    page_title="Asistente de Triaje - Electrónica Julio",
    page_icon="🔧",
    layout="centered", 
    initial_sidebar_state="collapsed",
)

# --- 2. CARGA DEL LOGO (Verifica el nombre del archivo en GitHub) ---
# Si tu logo se llama diferente, cambia "logo.jpg" por el nombre real.
LOGO_FILENAME = "logo_electronica_julio.png.jpg" 
logo_image = None
try:
    if os.path.exists(LOGO_FILENAME):
        logo_image = Image.open(LOGO_FILENAME)
    else:
        st.warning(f"No se encuentra el archivo '{LOGO_FILENAME}'. El asistente funcionará sin logo.")
except Exception as e:
    st.error(f"Error al cargar el logo: {e}")


# --- 3. INYECCIÓN DE CSS TOTAL (SALVANDO LA ESTÉTICA) ---
# Esta sección es crítica. Hemos forzado colores, tipografía, cabecera fija y footer.
custom_css = """
<style>
    /* Fondo general gris carbón oscuro (#1E1E1E) */
    .stApp {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    /* Ocultar elementos nativos de Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Contenedor de chat principal con padding para cabecera y footer */
    [data-testid="stChatMessageContainer"] {
        padding-top: 130px !important; /* Espacio para la cabecera fija */
        padding-bottom: 110px !important; /* Espacio para el footer fijo */
    }

    /* --- CABECERA FIJA --- */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #1E1E1E; /* Fondo oscuro */
        z-index: 1000;
        padding: 15px 0;
        border-bottom: 2px solid #FFD700; /* Borde amarillo eléctrico */
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .logo-header {
        max-width: 120px;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    .title-header {
        color: #FFFFFF;
        font-size: 1.1rem;
        font-weight: 500;
        margin-top: 5px;
        margin-bottom: 0;
    }
    .subtitle-header {
        color: #CCCCCC;
        font-size: 0.9rem;
        margin-top: -3px;
        margin-bottom: 10px;
    }

    /* --- ESTILO DE CHAT BUBBLES --- */
    [data-testid="stChatMessage"] {
        border-radius: 20px;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-family: inherit;
        line-height: 1.4;
    }

    /* Burbuja del Bot (Model - Gris Medio) */
    [data-testid="chatAvatarIcon-assistant"] {
        background-color: #333333;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background-color: #333333; /* Gris medio */
        border-left: 3px solid #FFD700; /* Acento amarillo */
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p {
        color: #FFFFFF !important; /* TEXTO BLANCO PURO (arreglado) */
        font-weight: 400;
    }

    /* Burbuja del Usuario (User - Amarillo Eléctrico) */
    [data-testid="chatAvatarIcon-user"] {
        background-color: #FFD700;
        color: #000000;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: #FFD700; /* Amarillo eléctrico */
        border-right: 3px solid #FFFFFF; /* Acento blanco */
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p {
        color: #000000 !important; /* TEXTO NEGRO PURO (arreglado) */
        font-weight: 500;
    }

    /* --- FOOTER FIJO (INPUT CHAT) --- */
    .fixed-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #1E1E1E;
        z-index: 1000;
        padding: 15px 0;
        border-top: 1px solid #333333;
        box-shadow: 0 -4px 6px rgba(0,0,0,0.3);
    }
    /* Estilo para el input de chat nativo */
    .stChatInputContainer {
        border-radius: 25px !important;
        border: 1px solid #333333 !important;
        background-color: #333333 !important;
    }
    .stChatInputContainer textarea {
        color: #FFFFFF !important;
        background-color: #333333 !important;
        font-size: 1rem;
    }

    /* --- BOTÓN DE WHATSAPP --- */
    .whatsapp-btn-fixed {
        display: block;
        width: calc(100% - 30px);
        background-color: #FFD700; /* Amarillo Eléctrico */
        color: #000000 !important;
        text-align: center;
        padding: 18px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1.1rem;
        text-decoration: none;
        margin: 15px auto;
        border: 2px solid #FFD700;
        transition: 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .whatsapp-btn-fixed:hover {
        background-color: transparent;
        color: #FFD700 !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# --- 4. RENDERIZADO DE CABECERA FIJA ---
st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
if logo_image:
    st.image(logo_image, width=120)
st.markdown('<p class="title-header">ELECTRÓNICA JULIO</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-header">Asistente Inteligente de Triaje (MVP)</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


# --- 5. CONFIGURACIÓN DE IA (GEMINI API) ---
# Intenta obtener la API KEY desde los secretos de Streamlit
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("No se encontró la clave API 'GEMINI_API_KEY'. Configúrala en el panel de control de Streamlit Cloud (Advanced -> Secrets).")
    st.stop() 

# --- SYSTEM PROMPT ESTRICTO (LA PERSONALIDAD DEL BOT) ---
SYSTEM_PROMPT = """Eres el asistente técnico inteligente de 'Electrónica Julio', un taller experto en reparación de electrónica de consumo en Tafí Viejo, Tucumán.
Tu objetivo es guiar al usuario de forma empática a través de un triaje de problemas.
Sigue estrictamente estas reglas:
1. **Recepción:** Comienza saludando amablemente (ej. "¡Hola! ¿En qué te puedo ayudar hoy?") y pregúntale qué equipo le está fallando (Smart TV, Audio, Refrigeración, etc.).
2. **Diagnóstico Nivel 1:** Haz preguntas clave y sugiere 1-2 soluciones simples "en casa" que no requieran conocimientos técnicos profundos (ej. "Asegúrate de que esté enchufado", "Intenta reiniciar el equipo", "Limpia los filtros del aire").
3. **Nivel 2 (Taller):** Si las soluciones de Nivel 1 no funcionan o si la falla es claramente de hardware (ej. pantalla rota, no enciende en absoluto, humo), proporciona un pre-diagnóstico corto y directo (ej. "Podría ser un problema en la fuente de alimentación") y dile que debe traer el equipo al taller.
4. **No Inventar Precios:** Tienes terminantemente PROHIBIDO inventar precios o presupuestos. Siempre di que el presupuesto se dará en el taller tras la revisión.
5. **Derivación a WhatsApp:** Cuando determines que se necesita una visita al taller, dile al usuario: "Para coordinar, haz clic en el botón de abajo y envíale un WhatsApp a Julio con el resumen de la falla. Él te responderá pronto."
"""

# Configuración del modelo Gemini Pro
model = genai.GenerativeModel('gemini-pro')


# --- 6. MANEJO DEL CHAT Y ESTADO DE SESIÓN ---
# Inicializar el historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensaje de bienvenida inicial del bot (Asegúrate de que sea claro)
    initial_bot_message = "¡Hola! Soy el Asistente Inteligente de Electrónica Julio. 😊 Contame, ¿qué equipo te está dando problemas (Smart TV, aire, audio, heladera...) y qué le pasa?"
    st.session_state.messages.append({"role": "assistant", "content": initial_bot_message})

# Mostrar mensajes de chat del historial (con el CSS personalizado aplicado)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --- 7. FOOTER FIJO (LÓGICA DE INPUT DEL USUARIO Y RESPUESTA DE LA IA) ---
# Contenedor de footer fijo para el input de chat
st.markdown('<div class="fixed-footer">', unsafe_allow_html=True)
# Usar st.container() dentro de st.columns() para que el chat_input se estire
input_cols = st.columns([0.05, 0.9, 0.05])
with input_cols[1]:
    if prompt := st.chat_input("Escribe tu consulta aquí..."):
        # Mostrar mensaje del usuario inmediatamente
        st.chat_message("user").markdown(prompt)
        # Agregar mensaje del usuario al historial
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generar respuesta de la IA (incluyendo el historial y el system prompt)
        try:
            # Combinar System Prompt y el historial de mensajes para el modelo
            full_conversation = [{"role": "user", "parts": [SYSTEM_PROMPT]}]
            for m in st.session_state.messages:
                if m["role"] == "user":
                    full_conversation.append({"role": "user", "parts": [m["content"]]})
                else:
                    full_conversation.append({"role": "model", "parts": [m["content"]]})

            # Llamada a la API de Gemini
            response = model.generate_content(full_conversation)
            bot_response = response.text

            # Mostrar respuesta del bot
            st.chat_message("assistant").markdown(bot_response)
            # Agregar respuesta del bot al historial
            st.session_state.messages.append({"role": "assistant", "content": bot_response})


            # --- 8. LÓGICA DEL BOTÓN DE WHATSAPP ---
            if any(keyword in bot_response.lower() for keyword in ["traer el equipo", "visita al taller", "presupuesto se dará", "coordinar"]):
                # Generar resumen de la falla para el mensaje de WhatsApp
                summary_prompt = f"Resume brevemente el problema técnico del usuario para un técnico: \n\n{full_conversation}"
                try:
                    summary_response = model.generate_content([{"role": "user", "parts": [summary_prompt]}])
                    fault_summary = summary_response.text.strip()
                except Exception:
                    fault_summary = "Consulta técnica de triaje."

                # Enlace de WhatsApp codificado
                JULIO_WHATSAPP_NUMBER = "5493810000000" 
                wa_message = f"Hola Julio, soy cliente y hablé con tu Asistente. Mi equipo tiene un problema. Resumen:\n\n{fault_summary}"
                encoded_wa_message = urllib.parse.quote(wa_message)
                wa_link = f"https://wa.me/{JULIO_WHATSAPP_NUMBER}?text={encoded_wa_message}"

                # Mostrar el botón de WhatsApp (con el CSS personalizado aplicado)
                st.markdown(f'<a href="{wa_link}" target="_blank" class="whatsapp-btn-fixed">📲 SOLICITAR PRESUPUESTO POR WHATSAPP</a>', unsafe_allow_html=True)
            # --- FIN LÓGICA DEL BOTÓN DE WHATSAPP ---

        except Exception as e:
            st.error(f"Error en la IA. Detalle: {e}")
st.markdown('</div>', unsafe_allow_html=True) # Cierra el footer fijo
