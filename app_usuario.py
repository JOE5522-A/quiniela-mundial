import streamlit as st
import json

# Configuración limpia para pantallas de celular
st.set_page_config(page_title="Quiniela Mundial 2026", layout="centered")

# --- FUNCIONES PARA MANEJAR EL ALMACÉN ---
def cargar_datos():
    with open("datos_quinela.json", "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_datos(datos):
    with open("datos_quinela.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

datos = cargar_datos()

if "codigos_registro" not in datos:
    datos["codigos_registro"] = {}

st.title("🏆 Mi Quiniela Web")

parametros = st.query_params
codigo_desde_enlace = parametros.get("invitacion", "")

if "usuario_logueado" not in st.session_state:
    st.session_state["usuario_logueado"] = None

# --- SI NO HA INICIADO SESIÓN, MOSTRAR MENÚ DE ACCESO ---
if st.session_state["usuario_logueado"] is None:
    modo_acceso = st.radio("Elige una opción:", ["🔑 Iniciar Sesión", "📝 Registrarme por primera vez"], horizontal=True)
    
    if modo_acceso == "🔑 Iniciar Sesión":
        st.subheader("Entrar a mi Cuenta")
        apodo_ingresado = st.text_input("Apodo de usuario:")
        password_ingresado = st.text_input("Contraseña:", type="password")
        
        if st.button("🚪 Entrar", use_container_width=True):
            if apodo_ingresado in datos["usuarios"]:
                if password_ingresado == datos["usuarios"][apodo_ingresado]["password"]:
                    st.session_state["usuario_logueado"] = apodo_ingresado
                    st.success(f"¡Bienvenido de vuelta {apodo_ingresado}!")
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta.")
            else:
                st.error("❌ El apodo ingresado no existe.")

    elif modo_acceso == "📝 Registrarme por primera vez":
        st.subheader("Crear Cuenta de Invitado")
        st.write("Introduce el código secreto o el enlace completo de WhatsApp:")
        
        codigo_sucio = st.text_input("Código de Invitación:", value=codigo_desde_enlace)
        
        # --- CORRECTOR AUTOMÁTICO DE ENLACES INTELIGENTE ---
        if "?invitacion=" in codigo_sucio:
            codigo_ticket = codigo_sucio.split("?invitacion=")[-1].strip().upper()
        else:
            codigo_ticket = codigo_sucio.strip().upper()
        
        st.divider()
        st.write("Crea tus datos de acceso privados:")
        nuevo_apodo = st.text_input("Inventa tu Apodo Público (Ej: ElCrackDelGrupo):")
        nuevo_password = st.text_input("Inventa tu Contraseña Secreta:", type="password")
        
        if st.button("🚀 Crear mi Cuenta y Jugar", use_container_width=True):
            datos = cargar_datos()
            
            if codigo_ticket in datos.get("codigos_registro", {}):
                if datos["codigos_registro"][codigo_ticket]["usado"]:
                    st.error("❌ Este código ya fue utilizado por otra persona.")
                elif nuevo_apodo in datos["usuarios"]:
                    st.error("❌ Ese apodo ya está siendo usado por otro amigo.")
                elif nuevo_apodo == "" or nuevo_password == "":
                    st.error("⚠️ Por favor rellena todos los campos.")
                else:
                    # Cuenta activa por defecto al usar un boleto válido
                    datos["usuarios"][nuevo_apodo] = {"password": nuevo_password, "puntos": 0, "activo": True}
                    datos["codigos_registro"][codigo_ticket]["usado"] = True
                    datos["codigos_registro"][codigo_ticket]["por_usuario"] = nuevo_apodo
                    
                    guardar_datos(datos)
                    
                    st.session_state["usuario_logueado"] = nuevo_apodo
                    st.success(f"🎉 ¡Felicidades {nuevo_apodo}! Cuenta creada.")
                    st.query_params.clear()
                    st.rerun()
            else:
                st.error(f"❌ Código de Invitación inválido ({codigo_ticket}). Revisa que esté bien escrito.")

# --- PÁGINA PRINCIPAL DE JUEGO (SI YA LOGUEÓ) ---
else:
    apodo_usuario = st.session_state["usuario_logueado"]
    
    col_inf, col_btn = st.columns(2)
    with col_inf:
        st.write(f"👤 Sesión activa: **{apodo_usuario}**")
    with col_btn:
        if st.button("❌ Salir", use_container_width=True):
            st.session_state["usuario_logueado"] = None
            st.rerun()
            
    st.divider()

    pestana_juego, pestana_ranking = st.tabs(["📝 Mis Pronósticos", "📊 Tabla de Posiciones"])

    with pestana_juego:
        st.write("⚽ **Partidos de Hoy:** Jueves 11 de Junio")
        st.subheader("🇲🇽 México vs 🇿🇦 Sudáfrica")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("🇲🇽 **México**")
            goles_mex = st.number_input("Goles", min_value=0, max_value=10, step=1, key="goles_mex")
        with col2:
            st.markdown("<h3 style='text-align: center; margin-top: 25px;'>VS</h3>", unsafe_allow_html=True)
        with col3:
            st.markdown("🇿🇦 **Sudáfrica**")
            goles_rsa = st.number_input("Goles ", min_value=0, max_value=10, step=1, key="goles_rsa")
        
        st.divider()
        if st.button("💾 Guardar mi Pronóstico", use_container_width=True):
            datos = cargar_datos()
            if "pronosticos" not in datos:
                datos["pronosticos"] = {}
            datos["pronosticos"][apodo_usuario] = {"mex": goles_mex, "rsa": goles_rsa}
            guardar_datos(datos)
            st.success("¡Pronóstico guardado en tu pendrive!")

    with pestana_ranking:
        st.subheader("🔝 Top Jugadores del Mundial")
        datos = cargar_datos()
        datos_tabla = [{"Posición": f"{i}º", "Apodo": user, "Puntos": info["puntos"]} for i, (user, info) in enumerate(datos["usuarios"].items(), 1)]
        st.table(datos_tabla)
