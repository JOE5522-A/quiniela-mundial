import streamlit as st
import json

# Configuración limpia para pantallas de celular
st.set_page_config(page_title="Panel Administrador", layout="centered")

# --- MANEJO SEGURO DE ARCHIVOS Y JSON ---
def cargar_datos():
    try:
        with open("datos_quinela.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        datos = {}
    
    # Asegura la consistencia de las estructuras obligatorias
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

pestana_partidos, pestana_usuarios = st.tabs([
    "⚽ Partidos del Día", 
    "👥 Activar y Gestionar Usuarios"
])

# --- PESTAÑA 1: CONFIGURAR Y CERRAR PARTIDOS ---
with pestana_partidos:
    st.subheader("📌 Configurar Partido Activo")
    
    if datos["partido_actual"].get("estado") == "finalizado":
        st.warning("⚠️ El partido anterior ya fue cerrado. Configura el nuevo juego abajo.")
    else:
        st.info(f"⚽ Partido activo: **{datos['partido_actual']['local']} vs {datos['partido_actual']['visitante']}**")
    
    nuevo_local = st.text_input("⚽ Equipo Local:", value=datos["partido_actual"]["local"])
    nuevo_visitante = st.text_input("⚽ Equipo Visitante:", value=datos["partido_actual"]["visitante"])
    
    if st.button("📢 Cambiar Partido del Día", use_container_width=True):
        if datos["partido_actual"].get("estado") == "activo" and len(datos.get("pronosticos", {})) > 0:
            st.error("❌ Hay pronósticos activos. Finaliza el partido actual antes de cambiar los equipos.")
        elif nuevo_local.strip() == "" or nuevo_visitante.strip() == "":
            st.error("❌ Los nombres no pueden estar vacíos.")
        else:
            datos["partido_actual"] = {"local": nuevo_local, "visitante": nuevo_visitante, "estado": "activo"}
            datos["pronosticos"] = {} 
            guardar_datos(datos)
            st.success("¡Partido cambiado con éxito!")
            st.rerun()

    st.divider()
    
    st.subheader("🏁 Cargar Marcador Oficial y Sumar Puntos")
    if datos["partido_actual"].get("estado") == "finalizado":
        st.success("✅ Partido evaluado con éxito.")
    else:
        st.write(f"Introduce el resultado final de: **{datos['partido_actual']['local']} vs {datos['partido_actual']['visitante']}**")
        col1, col2 = st.columns(2)
        with col1: gol_r_local = st.number_input(f"Goles {datos['partido_actual']['local']}", min_value=0, step=1, key="gl")
        with col2: gol_r_vis = st.number_input(f"Goles {datos['partido_actual']['visitante']}", min_value=0, step=1, key="gv")
            
        if st.button("🧠 Finalizar Partido y Calcular Puntos", use_container_width=True):
            conteo_procesados = 0
            for apodo, pronostico in datos.get("pronosticos", {}).items():
                if apodo in datos["usuarios"] and datos["usuarios"][apodo].get("activo", False) == True:
                    nuevos_puntos = calcular_puntos(pronostico["local"], pronostico["visitante"], gol_r_local, gol_r_vis)
                    datos["usuarios"][apodo]["puntos"] += nuevos_puntos
                    conteo_procesados += 1
            
            datos["historial_partidos"].append({
                "local": datos["partido_actual"]["local"], "visitante": datos["partido_actual"]["visitante"],
                "goles_local": gol_r_local, "goles_visitante": gol_r_vis
            })
            datos["partido_actual"]["estado"] = "finalizado"
            guardar_datos(datos)
            st.success(f"⚽ ¡Cerrado! Marcador cargado para {conteo_procesados} usuarios activos.")
            st.rerun()

# --- PESTAÑA 2: GESTIÓN Y APROBACIÓN DE USUARIOS ---
with pestana_usuarios:
    st.subheader("⏳ Jugadores Pendientes de Aprobación")
    
    # Forzar verificación de que "activo" exista como llave en cada perfil
    pendientes = []
    for apodo, info in datos["usuarios"].items():
        if info.get("activo", False) == False:
            pendientes.append(apodo)
    
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
    
    st.subheader("📊 Ranking y Control de Accesos")
    usuarios_ordenados = sorted(datos["usuarios"].items(), key=lambda x: x[1]["puntos"], reverse=True)
    
    datos_tabla = [
        {"Posición": f"{i}º", "Apodo": apodo, "Puntos": info["puntos"], "Estado": "🟢 Activo" if info.get("activo", False) else "⏳ Pendiente"}
        for i, (apodo, info) in enumerate(usuarios_ordenados, 1)
    ]
    if datos_tabla: st.table(datos_tabla)
        
    st.divider()
    st.subheader("🚫 Suspender Jugadores Activos")
    activos = [apodo for apodo, info in datos["usuarios"].items() if info.get("activo", False) == True]
    if activos:
        usuario_seleccionado = st.selectbox("Selecciona un usuario para desactivar:", activos)
        if st.button(f"🔒 Desactivar Cuenta de {usuario_seleccionado}", use_container_width=True, type="primary"):
            datos["usuarios"][usuario_seleccionado]["activo"] = False
            guardar_datos(datos)
            st.rerun()
    else:
        st.info("No hay usuarios activos para suspender.")
