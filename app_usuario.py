import streamlit as st
import json

st.set_page_config(page_title="Quiniela Mundial 2026", layout="centered")

def cargar_datos():
    with open("datos_quinela.json", "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_datos(datos):
    with open("datos_quinela.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

datos = cargar_datos()

if "partido_actual" not in datos:
    datos["partido_actual"] = {"local": "México", "visitante": "Sudáfrica"}

st.title("🏆 Mi Quiniela Web")

parametros = st.query_params
codigo_desde_enlace = parametros.get("invitacion", "")

if "usuario_logueado" not in st.session_state:
    st.session_state["usuario_logueado"] = None

# --- INICIO DE SESIÓN Y REGISTRO ---
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
                    st.rerun()
                else: st.error("❌ Contraseña incorrecta.")
            else: st.error("❌ El apodo no existe.")

    elif modo_acceso == "📝 Registrarme por primera vez":
        st.subheader("Crear Cuenta de Invitado")
        codigo_sucio = st.text_input("Código de Invitación:", value=codigo_desde_enlace)
        if "?invitacion=" in codigo_sucio:
            codigo_ticket = codigo_sucio.split("?invitacion=")[-1].strip().upper()
        else:
            codigo_ticket = codigo_sucio.strip().upper()
        
        nuevo_apodo = st.text_input("Inventa tu Apodo Público:")
        nuevo_password = st.text_input("Inventa tu Contraseña Secreta:", type="password")
        
        if st.button("🚀 Crear mi Cuenta y Jugar", use_container_width=True):
            datos = cargar_datos()
            if codigo_ticket in datos.get("codigos_registro", {}):
                if datos["codigos_registro"][codigo_ticket]["usado"]:
                    st.error("❌ Este código ya fue utilizado.")
                elif nuevo_apodo in datos["usuarios"]:
                    st.error("❌ Ese apodo ya está siendo usado.")
                elif nuevo_apodo == "" or nuevo_password == "":
                    st.error("⚠️ Rellena todos los campos.")
                else:
                    datos["usuarios"][nuevo_apodo] = {"password": nuevo_password, "puntos": 0, "activo": True}
                    datos["codigos_registro"][codigo_ticket]["usado"] = True
                    datos["codigos_registro"][codigo_ticket]["por_usuario"] = nuevo_apodo
                    guardar_datos(datos)
                    st.session_state["usuario_logueado"] = nuevo_apodo
                    st.query_params.clear()
                    st.rerun()
            else: st.error("❌ Código inválido.")

# --- PÁGINA PRINCIPAL DE JUEGO ---
else:
    apodo_usuario = st.session_state["usuario_logueado"]
    
    col_inf, col_btn = st.columns(2)
    with col_inf:
        st.write(f"👤 Usuario: **{apodo_usuario}**")
    with col_btn:
        if st.button("❌ Salir", use_container_width=True):
            st.session_state["usuario_logueado"] = None
            st.rerun()
            
    st.divider()

    pestana_juego, pestana_ranking = st.tabs(["📝 Mis Pronósticos", "📊 Tabla de Posiciones"])

    with pestana_juego:
        st.write("⚽ **Partido de Hoy:**")
        
        # LEEMOS LOS NOMBRES QUE PUSO EL ADMINISTRADOR EN TIEMPO REAL
        equipo_local = datos["partido_actual"]["local"]
        equipo_visitante = datos["partido_actual"]["visitante"]
        
        st.subheader(f"🗓️ {equipo_local} vs {equipo_visitante}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**{equipo_local}**")
            goles_local = st.number_input("Goles ", min_value=0, max_value=10, step=1, key="goles_l")
        with col2:
            st.markdown("<h3 style='text-align: center; margin-top: 25px;'>VS</h3>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"**{equipo_visitante}**")
            goles_vis = st.number_input("Goles  ", min_value=0, max_value=10, step=1, key="goles_v")
        
        st.divider()
        if st.button("💾 Guardar mi Pronóstico", use_container_width=True):
            datos = cargar_datos()
            if "pronosticos" not in datos:
                datos["pronosticos"] = {}
            # Guardamos con etiquetas genéricas (local/visitante) para que funcione con cualquier partido
            datos["pronosticos"][apodo_usuario] = {"local": goles_local, "visitante": goles_vis}
            guardar_datos(datos)
            st.success("¡Pronóstico guardado con éxito!")

    with pestana_ranking:
        st.subheader("🔝 Top Jugadores del Mundial")
        datos = cargar_datos()
        datos_tabla = [{"Posición": f"{i}º", "Apodo": user, "Puntos": info["puntos"]} for i, (user, info) in enumerate(datos["usuarios"].items(), 1)]
        st.table(datos_tabla)
