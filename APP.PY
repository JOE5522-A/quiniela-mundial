import streamlit as st
import json
from datetime import datetime
import zoneinfo

# Configuración adaptable para pantallas de celulares
st.set_page_config(page_title="Quiniela Mundial 2026", layout="centered")

# --- MANEJO CENTRALIZADO DE LA BASE DE DATOS ---
def cargar_datos():
    try:
        with open("datos_quinela.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        datos = {}
    
    # Garantizar estructuras obligatorias para evitar caídas
    if "partido_actual" not in datos:
        datos["partido_actual"] = {"local": "México", "visitante": "Sudáfrica", "estado": "activo"}
    if "usuarios" not in datos:
        datos["usuarios"] = {}
    if "pronosticos" not in datos:
        datos["pronosticos"] = {}
    if "historial_partidos" not in datos:
        datos["historial_partidos"] = []
    return datos

def guardar_datos(datos):
    with open("datos_quinela.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# Motor de puntos oficial
def calcular_puntos(gol_u_local, gol_u_vis, gol_r_local, gol_r_vis):
    ganador_real = "local" if gol_r_local > gol_r_vis else ("visitante" if gol_r_vis > gol_r_local else "empate")
    ganador_pronostico = "local" if gol_u_local > gol_u_vis else ("visitante" if gol_u_vis > gol_u_local else "empate")
    marcador_exacto = (gol_u_local == gol_r_local) and (gol_u_vis == gol_r_vis)
    
    if ganador_real == "empate" and ganador_pronostico == "empate":
        return 4 if marcador_exacto else 1
    elif ganador_real == ganador_pronostico:
        return 5 if marcador_exacto else 3
    else:
        return 0

# Inicialización
datos = cargar_datos()

if "usuario_logueado" not in st.session_state:
    st.session_state["usuario_logueado"] = None

st.title("🏆 Mi Quiniela Web 2026")

# --- CONTROL DE ACCESO (LOGIN Y REGISTRO DIRECTO) ---
if st.session_state["usuario_logueado"] is None:
    modo_acceso = st.radio("Elige una opción:", ["🔑 Iniciar Sesión", "📝 Registrarme y crear cuenta"], horizontal=True)
    
    if modo_acceso == "🔑 Iniciar Sesión":
        st.subheader("Entrar a mi Cuenta")
        apodo_ingresado = st.text_input("Apodo de usuario:").strip()
        password_ingresado = st.text_input("Contraseña:", type="password")
        
        if st.button("🚪 Entrar", use_container_width=True):
            # 🔐 ACCESO MAESTRO SECRETO PARA EL ADMINISTRADOR
            if apodo_ingresado.upper() == "ADMIN" and password_ingresado == "ADMIN1234":
                st.session_state["usuario_logueado"] = "ADMIN"
                st.rerun()
            elif apodo_ingresado in datos["usuarios"]:
                if password_ingresado == datos["usuarios"][apodo_ingresado]["password"]:
                    st.session_state["usuario_logueado"] = apodo_ingresado
                    st.rerun()
                else: st.error("❌ Contraseña incorrecta.")
            else: st.error("❌ El apodo no existe.")

    elif modo_acceso == "📝 Registrarme y crear cuenta":
        st.subheader("Registro Público de Jugadores")
        nuevo_apodo = st.text_input("Inventa tu Apodo Público (Ej: JORGUE12):").strip()
        nuevo_password = st.text_input("Inventa tu Contraseña Secreta:", type="password")
        
        if st.button("🚀 Registrarme y Esperar Activación", use_container_width=True):
            datos = cargar_datos()
            if nuevo_apodo.upper() == "ADMIN":
                st.error("❌ No puedes registrarte con el nombre protegido 'ADMIN'.")
            elif nuevo_apodo in datos["usuarios"]:
                st.error("❌ Ese apodo ya está siendo usado.")
            elif nuevo_apodo == "" or nuevo_password == "":
                st.error("⚠️ Rellena todos los campos.")
            else:
                # Se guarda inactivo por defecto (False) esperando tu aprobación
                datos["usuarios"][nuevo_apodo] = {"password": nuevo_password, "puntos": 0, "activo": False}
                guardar_datos(datos)
                st.success("🎉 ¡Cuenta creada con éxito! Dile al Administrador que te active para empezar a enviar pronósticos.")
                st.rerun()

# --- VISTA DE PANELES (LOGUEADO) ---
else:
    usuario_actual = st.session_state["usuario_logueado"]
    
    col_inf, col_btn = st.columns(2)
    with col_inf: st.write(f"👤 Conectado como: **{usuario_actual}**")
    with col_btn:
        if st.button("❌ Salir de la Cuenta", use_container_width=True):
            st.session_state["usuario_logueado"] = None
            st.rerun()
            
    st.divider()

    # ==========================================
    # ⚙️ MÓDULO PRIVADO DEL ADMINISTRADOR
    # ==========================================
    if usuario_actual == "ADMIN":
        st.subheader("🛠️ PANEL DE CONTROL ADMINISTRATIVO")
        pestana_partidos, pestana_usuarios = st.tabs(["⚽ Partidos del Día", "👥 Activar y Gestionar Usuarios"])
        
        with pestana_partidos:
            st.write("### Configurar Partido Activo")
            nuevo_local = st.text_input("⚽ Equipo Local:", value=datos["partido_actual"]["local"])
            nuevo_visitante = st.text_input("⚽ Equipo Visitante:", value=datos["partido_actual"]["visitante"])
            
            if st.button("📢 Cambiar Partido del Día", use_container_width=True):
                if datos["partido_actual"].get("estado") == "activo" and len(datos.get("pronosticos", {})) > 0:
                    st.error("❌ Hay pronósticos activos sin evaluar. Cierra el partido actual primero.")
                elif nuevo_local.strip() == "" or nuevo_visitante.strip() == "":
                    st.error("❌ Los nombres no pueden estar vacíos.")
                else:
                    datos["partido_actual"] = {"local": nuevo_local, "visitante": nuevo_visitante, "estado": "activo"}
                    datos["pronosticos"] = {} 
                    guardar_datos(datos)
                    st.success("¡Partido cambiado exitosamente!")
                    st.rerun()
            
            st.divider()
            st.write("### Cargar Marcador y Sumar Puntos")
            if datos["partido_actual"].get("estado") == "finalizado":
                st.success("✅ Partido actual cerrado.")
            else:
                col1, col2 = st.columns(2)
                with col1: gol_r_local = st.number_input(f"Goles {datos['partido_actual']['local']}", min_value=0, step=1, key="adm_l")
                with col2: gol_r_vis = st.number_input(f"Goles {datos['partido_actual']['visitante']}", min_value=0, step=1, key="adm_v")
                
                if st.button("🧠 Finalizar Partido y Calcular Puntos", use_container_width=True):
                    conteo = 0
                    for apodo, pronostico in datos.get("pronosticos", {}).items():
                        if apodo in datos["usuarios"] and datos["usuarios"][apodo].get("activo", False) == True:
                            puntos_ganados = calcular_puntos(pronostico["local"], pronostico["visitante"], gol_r_local, gol_r_vis)
                            datos["usuarios"][apodo]["puntos"] += puntos_ganados
                            conteo += 1
                    datos["historial_partidos"].append({
                        "local": datos["partido_actual"]["local"], "visitante": datos["partido_actual"]["visitante"],
                        "goles_local": gol_r_local, "goles_visitante": gol_r_vis
                    })
                    datos["partido_actual"]["estado"] = "finalizado"
                    guardar_datos(datos)
                    st.success(f"⚽ Puntos cargados correctamente a {conteo} usuarios activos.")
                    st.rerun()

        with pestana_usuarios:
            st.write("### ⏳ Jugadores Pendientes de Aprobación")
            pendientes = [apodo for apodo, info in datos["usuarios"].items() if info.get("activo", False) == False]
            
            if pendientes:
                st.warning(f"Tienes {len(pendientes)} usuario(s) esperando activación.")
                for usuario_p in pendientes:
                    col_user, col_btn_aprob = st.columns(2)
                    with col_user:
                        st.write(f"👤 **{usuario_p}**")
                    with col_btn_aprob:
                        if st.button(f"✅ Activar", key=f"act_{usuario_p}", use_container_width=True):
                            datos["usuarios"][usuario_p]["activo"] = True
                            guardar_datos(datos)
                            st.success(f"¡{usuario_p} aprobado!")
                            st.rerun()
            else:
                st.info("No hay usuarios pendientes por activar.")
                
            st.divider()
            st.write("### 📊 Ranking General y Estados")
            usuarios_ordenados = sorted(datos["usuarios"].items(), key=lambda x: x[1]["puntos"], reverse=True)
            
            datos_tabla = [
                {"Posición": f"{i}º", "Apodo": apodo, "Puntos": info["puntos"], "Estado": "🟢 Activo" if info.get("activo", False) else "⏳ Pendiente"}
                for i, (apodo, info) in enumerate(usuarios_ordenados, 1)
            ]
            if datos_tabla: st.table(datos_tabla)
                
            st.divider()
            st.write("### 🚫 Suspender Jugadores Activos")
            activos = [apodo for apodo, info in datos["usuarios"].items() if info.get("activo", False) == True]
            if activos:
                usuario_seleccionado = st.selectbox("Selecciona un usuario para desactivar:", activos)
                if st.button(f"🔒 Desactivar Cuenta de {usuario_seleccionado}", use_container_width=True, type="primary"):
                    datos["usuarios"][usuario_seleccionado]["activo"] = False
                    guardar_datos(datos)
                    st.rerun()

    # ==========================================
    # 📱 MÓDULO PÚBLICO PARA JUGADORES / AMIGOS
