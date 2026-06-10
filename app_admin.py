import streamlit as st
import json
import random
import string

st.set_page_config(page_title="Panel Administrador", layout="centered")

# --- MANEJO SEGURO DE ARCHIVOS Y JSON ---
def cargar_datos():
    try:
        with open("datos_quinela.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        datos = {}
    
    # Asegura la consistencia de las estructuras
    if "partido_actual" not in datos:
        datos["partido_actual"] = {"local": "México", "visitante": "Sudáfrica", "estado": "activo"}
    if "codigos_registro" not in datos:
        datos["codigos_registro"] = {}
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

st.title("⚙️ Panel de Control - Administrador")

# Creamos las 3 pestañas solicitadas
pestana_partidos, pestana_invitaciones, pestana_usuarios = st.tabs([
    "⚽ Partidos del Día", 
    "🎫 Generar Invitaciones",
    "👥 Usuarios y Ranking"
])

# --- PESTAÑA 1: CONFIGURAR Y CERRAR PARTIDOS ---
with pestana_partidos:
    st.subheader("📌 Configurar Partido Activo")
    
    if datos["partido_actual"].get("estado") == "finalizado":
        st.warning("⚠️ El partido anterior ya fue cerrado y evaluado. Configura el nuevo juego de hoy abajo.")
    else:
        st.info(f"⚽ Partido activo: **{datos['partido_actual']['local']} vs {datos['partido_actual']['visitante']}**")
    
    nuevo_local = st.text_input("⚽ Equipo Local:", value=datos["partido_actual"]["local"])
    nuevo_visitante = st.text_input("⚽ Equipo Visitante:", value=datos["partido_actual"]["visitante"])
    
    if st.button("📢 Cambiar Partido del Día", use_container_width=True):
        if datos["partido_actual"].get("estado") == "activo" and len(datos.get("pronosticos", {})) > 0:
            st.error("❌ Hay pronósticos activos. Finaliza el partido actual y suma los puntos antes de cambiar los equipos.")
        elif nuevo_local.strip() == "" or nuevo_visitante.strip() == "":
            st.error("❌ Los nombres de los equipos no pueden estar vacíos.")
        else:
            datos["partido_actual"] = {"local": nuevo_local, "visitante": nuevo_visitante, "estado": "activo"}
            datos["pronosticos"] = {} 
            guardar_datos(datos)
            st.success(f"¡Activado! Celulares sincronizados con: {nuevo_local} vs {nuevo_visitante}")
            st.rerun()

    st.divider()
    
    st.subheader("🏁 Cargar Marcador Oficial y Sumar Puntos")
    if datos["partido_actual"].get("estado") == "finalizado":
        st.success("✅ Partido evaluado con éxito.")
    else:
        st.write(f"Introduce el resultado final de: **{datos['partido_actual']['local']} vs {datos['partido_actual']['visitante']}**")
        col1, col2 = st.columns(2)
        with col1:
            gol_r_local = st.number_input(f"Goles {datos['partido_actual']['local']}", min_value=0, max_value=20, step=1, key="gl")
        with col2:
            gol_r_vis = st.number_input(f"Goles {datos['partido_actual']['visitante']}", min_value=0, max_value=20, step=1, key="gv")
            
        if st.button("🧠 Finalizar Partido y Calcular Puntos", use_container_width=True):
            conteo_procesados = 0
            for apodo, pronostico in datos.get("pronosticos", {}).items():
                if apodo in datos["usuarios"]:
                    if datos["usuarios"][apodo].get("activo", True):
                        nuevos_puntos = calcular_puntos(pronostico["local"], pronostico["visitante"], gol_r_local, gol_r_vis)
                        datos["usuarios"][apodo]["puntos"] += nuevos_puntos
                        conteo_procesados += 1
            
            datos["historial_partidos"].append({
                "local": datos["partido_actual"]["local"], "visitante": datos["partido_actual"]["visitante"],
                "goles_local": gol_r_local, "goles_visitante": gol_r_vis
            })
            datos["partido_actual"]["estado"] = "finalizado"
            guardar_datos(datos)
            st.success(f"⚽ ¡Cerrado! {datos['partido_actual']['local']} {gol_r_local} - {gol_r_vis} {datos['partido_actual']['visitante']}.")
            st.rerun()

# --- PESTAÑA 2: GENERAR INVITACIONES ---
with pestana_invitaciones:
    st.subheader("Generar Códigos de Registro")
    if st.button("➕ Generar 1 Código Nuevo", use_container_width=True):
        datos = cargar_datos()
        codigo_generado = "MUN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        datos["codigos_registro"][codigo_generado] = {"usado": False, "por_usuario": ""}
        guardar_datos(datos)
        st.success(f"¡Código `{codigo_generado}` listo!")
        st.code(f"http://localhost:8501/?invitacion={codigo_generado}", language="markdown")

# --- PESTAÑA 3: GESTIÓN DE USUARIOS Y RANKING ---
with pestana_usuarios:
    st.subheader("📊 Tabla de Posiciones General")
    usuarios_ordenados = sorted(datos["usuarios"].items(), key=lambda x: x["puntos"], reverse=True)
    
    datos_tabla = [
        {
            "Posición": f"{i}º",
            "Apodo": apodo,
            "Puntos acumulados": info["puntos"],
            "Estado de Cuenta": "🟢 Activo" if info.get("activo", True) else "🔴 Suspendido"
        }
        for i, (apodo, info) in enumerate(usuarios_ordenados, 1)
    ]
    
    if datos_tabla:
        st.table(datos_tabla)
    else:
        st.info("Aún no se han registrado usuarios en el sistema.")
        
    st.divider()
    
    st.subheader("🚫 Control de Accesos (Suspender / Activar Amigos)")
    if datos["usuarios"]:
        lista_jugadores = list(datos["usuarios"].keys())
        usuario_seleccionado = st.selectbox("Selecciona un usuario:", lista_jugadores)
        estado_actual = datos["usuarios"][usuario_seleccionado].get("activo", True)
        
        if estado_actual:
            st.success(f"El usuario **{usuario_seleccionado}** tiene acceso total.")
            if st.button(f"🔒 Suspender a {usuario_seleccionado}", use_container_width=True, type="primary"):
                datos["usuarios"][usuario_seleccionado]["activo"] = False
                guardar_datos(datos)
                st.rerun()
        else:
            st.error(f"El usuario **{usuario_seleccionado}** se encuentra SUSPENDIDO.")
            if st.button(f"🔓 Reactivar a {usuario_seleccionado}", use_container_width=True):
                datos["usuarios"][usuario_seleccionado]["activo"] = True
                guardar_datos(datos)
                st.rerun()
    else:
        st.info("No hay perfiles para administrar.")
