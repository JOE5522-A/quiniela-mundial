import streamlit as st
import json
from datetime import datetime
import zoneinfo

# Configuración limpia para pantallas de celular
st.set_page_config(page_title="Quiniela Mundial 2026", layout="centered")

# --- FUNCIONES PARA MANEJAR EL ALMACÉN ---
def cargar_datos():
    try:
        with open("datos_quinela.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        datos = {}
    
    # Asegurar estructuras básicas y evitar errores de llaves inexistentes
    if "partido_actual" not in datos:
        datos["partido_actual"] = {"local": "México", "visitante": "Sudáfrica", "estado": "activo"}
    if "usuarios" not in datos:
        datos["usuarios"] = {}
    if "codigos_registro" not in datos:
        datos["codigos_registro"] = {}
    if "pronosticos" not in datos:
        datos["pronosticos"] = {}
    return datos

def guardar_datos(datos):
    with open("datos_quinela.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# Cargar los datos al iniciar la app
datos = cargar_datos()

st.title("🏆 Mi Quiniela Web")

# Captura de parámetros desde el enlace de WhatsApp
parametros = st.query_params
codigo_desde_enlace = parametros.get("invitacion", "")

if "usuario_logueado" not in st.session_state:
    st.session_state["usuario_logueado"] = None

# --- SECCIÓN 1: INICIO DE SESIÓN Y REGISTRO ---
if st.session_state["usuario_logueado"] is None:
    modo_acceso = st.radio("Elige una opción:", ["🔑 Iniciar Sesión", "📝 Registrarme por primera vez"], horizontal=True)
    
    if modo_acceso == "🔑 Iniciar Sesión":
        st.subheader("Entrar a mi Cuenta")
        apodo_ingresado = st.text_input("Apodo de usuario:").strip()
        password_ingresado = st.text_input("Contraseña:", type="password")
        
        if st.button("🚪 Entrar", use_container_width=True):
            if apodo_ingresado in datos["usuarios"]:
                # 🔒 Validación de cuenta suspendida por el administrador
                if not datos["usuarios"][apodo_ingresado].get("activo", True):
                    st.error("❌ Tu cuenta se encuentra suspendida temporalmente por el Administrador.")
                elif password_ingresado == datos["usuarios"][apodo_ingresado]["password"]:
                    st.session_state["usuario_logueado"] = apodo_ingresado
                    st.rerun()
                else: 
                    st.error("❌ Contraseña incorrecta.")
            else: 
                st.error("❌ El apodo no existe.")

    elif modo_acceso == "📝 Registrarme por primera vez":
        st.subheader("Crear Cuenta de Invitado")
        codigo_sucio = st.text_input("Código de Invitación:", value=codigo_desde_enlace)
        
        if "?invitacion=" in codigo_sucio:
            codigo_ticket = codigo_sucio.split("?invitacion=")[-1].strip().upper()
        else:
            codigo_ticket = codigo_sucio.strip().upper()
        
        nuevo_apodo = st.text_input("Inventa tu Apodo Público:").strip()
        nuevo_password = st.text_input("Inventa tu Contraseña Secreta:", type="password")
        
        if st.button("🚀 Crear mi Cuenta y Jugar", use_container_width=True):
            datos = cargar_datos()  # Recargar datos para evitar sobreescritura diferida
            if codigo_ticket in datos.get("codigos_registro", {}):
                if datos["codigos_registro"][codigo_ticket]["usado"]:
                    st.error("❌ Este código ya fue utilizado.")
                elif nuevo_apodo in datos["usuarios"]:
                    st.error("❌ Ese apodo ya está siendo usado.")
                elif nuevo_apodo == "" or nuevo_password == "":
                    st.error("⚠️ Rellena todos los campos.")
                else:
                    # Guardar el perfil completo de forma limpia
                    datos["usuarios"][nuevo_apodo] = {"password": nuevo_password, "puntos": 0, "activo": True}
                    datos["codigos_registro"][codigo_ticket]["usado"] = True
                    datos["codigos_registro"][codigo_ticket]["por_usuario"] = nuevo_apodo
                    guardar_datos(datos)
                    st.session_state["usuario_logueado"] = nuevo_apodo
                    st.query_params.clear()  # Limpiar la URL de la barra de direcciones
                    st.rerun()
            else: 
                st.error("❌ Código inválido.")

# --- SECCIÓN 2: PÁGINA PRINCIPAL DE JUEGO (LOGUEADO) ---
else:
    apodo_usuario = st.session_state["usuario_logueado"]
    
    # Barra superior con la información del perfil del jugador
    col_inf, col_btn = st.columns(2)
    with col_inf:
        st.write(f"👤 Usuario: **{apodo_usuario}**")
    with col_btn:
        if st.button("❌ Salir de la Cuenta", use_container_width=True):
            st.session_state["usuario_logueado"] = None
            st.rerun()
            
    st.divider()

    pestana_juego, pestana_ranking = st.tabs(["📝 Mis Pronósticos", "📊 Tabla de Posiciones"])

    with pestana_juego:
        st.write("⚽ **Partido de Hoy:**")
        
        equipo_local = datos["partido_actual"]["local"]
        equipo_visitante = datos["partido_actual"]["visitante"]
        
        st.subheader(f"🗓️ {equipo_local} vs {equipo_visitante}")
        
        # --- CANDADO DE SEGURIDAD AUTOMÁTICO ---
        zona_mex = zoneinfo.ZoneInfo("America/Mexico_City")
        hora_actual_mex = datetime.now(zona_mex)
        hora_limite_partido = datetime(2026, 6, 11, 13, 0, 0, tzinfo=zona_mex)
        
        # Se bloquea si el Admin ya cerró el partido o si pasó la hora del juego inaugural
        partido_comenzado = (datos["partido_actual"].get("estado") == "finalizado") or (hora_actual_mex >= hora_limite_partido)

        # Cargar valores guardados previamente por este usuario concreto
        pronostico_previo = datos.get("pronosticos", {}).get(apodo_usuario, {"local": 0, "visitante": 0})

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**{equipo_local}**")
            goles_local = st.number_input("Goles ", min_value=0, max_value=10, step=1, key="goles_l", value=int(pronostico_previo["local"]), disabled=partido_comenzado)
        with col2:
            st.markdown("<h3 style='text-align: center; margin-top: 25px;'>VS</h3>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"**{equipo_visitante}**")
            goles_vis = st.number_input("Goles  ", min_value=0, max_value=10, step=1, key="goles_v", value=int(pronostico_previo["visitante"]), disabled=partido_comenzado)
        
        st.divider()
        
        # Pestaña interactiva desplegable con las reglas de puntuación oficiales
        with st.expander("🎯 Ver Sistema de Puntuación Oficial"):
            st.markdown("""
            * **1 Punto:** Acertar Empate sin marcador exacto.
            * **3 Puntos:** Acertar Ganador sin marcador exacto.
            * **4 Puntos:** Acertar Empate CON marcador exacto.
            * **5 Puntos:** Acertar Ganador CON marcador exacto.
            """)
        
        if partido_comenzado:
            st.error("🔒 Los pronósticos para este encuentro están oficialmente CERRADOS.")
        else:
            if st.button("💾 Guardar mi Pronóstico", use_container_width=True):
                datos = cargar_datos()  # Recarga preventiva antes de escribir para no chocar datos
                
                datos["pronosticos"][apodo_usuario] = {
                    "local": goles_local, 
                    "visitante": goles_vis
                }
                
                guardar_datos(datos)
                st.success("¡Tu pronóstico ha sido guardado con éxito!")

    with pestana_ranking:
        st.subheader("🔝 Top Jugadores de la Quiniela")
        datos = cargar_datos()
        
        # Ordenación estricta por puntos en formato descendente
        usuarios_ordenados = sorted(datos["usuarios"].items(), key=lambda x: x["puntos"], reverse=True)
        
        datos_tabla = [
            {
                "Posición": f"{i}º", 
                "Apodo": user, 
                "Puntos Total": info["puntos"]
            } for i, (user, info) in enumerate(usuarios_ordenados, 1)
        ]
        
        if datos_tabla:
            st.table(datos_tabla)
        else:
            st.info("Aún no hay usuarios registrados en la tabla de posiciones.")
