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
        # Si el archivo está vacío o no existe, se crea la estructura base
        datos = {}
    
    # 🛠️ VALIDACIÓN REQUERIDA: Asegura que ninguna llave borre los datos de usuarios
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

# Inicialización limpia
datos = cargar_datos()

st.title("⚙️ Panel de Control - Administrador")

pestana_partidos, pestana_invitaciones = st.tabs(["⚽ Partidos del Día", "🎫 Generar Invitaciones"])

# --- PESTAÑA: CONFIGURAR Y CERRAR PARTIDOS ---
with pestana_partidos:
    st.subheader("📌 Configurar Partido Activo")
    
    # Mostrar estado actual del juego en el sistema
    if datos["partido_actual"].get("estado") == "finalizado":
        st.warning("⚠️ El partido anterior ya fue cerrado y evaluado. Configura el nuevo juego de hoy abajo.")
    else:
        st.info(f"⚽ Partido en juego actual: **{datos['partido_actual']['local']} vs {datos['partido_actual']['visitante']}**")
    
    nuevo_local = st.text_input("⚽ Equipo Local:", value=datos["partido_actual"]["local"])
    nuevo_visitante = st.text_input("⚽ Equipo Visitante:", value=datos["partido_actual"]["visitante"])
    
    if st.button("📢 Cambiar Partido del Día", use_container_width=True):
        # Evitar cambiar de partido si hay pronósticos activos sin evaluar
        if datos["partido_actual"].get("estado") == "activo" and len(datos.get("pronosticos", {})) > 0:
            st.error("❌ ¡Espera! Hay pronósticos de tus amigos activos. Primero debes finalizar el partido y sumar los puntos antes de cambiar los equipos.")
        elif nuevo_local.strip() == "" or nuevo_visitante.strip() == "":
            st.error("❌ Los nombres de los equipos no pueden estar vacíos.")
        else:
            datos["partido_actual"] = {
                "local": nuevo_local,
                "visitante": nuevo_visitante,
                "estado": "activo"
            }
            # Se limpian pronósticos viejos porque arranca un nuevo encuentro
            datos["pronosticos"] = {} 
            guardar_datos(datos)
            st.success(f"¡Activado con éxito! En los celulares se verá: {nuevo_local} vs {nuevo_visitante}")
            st.rerun()

    st.divider()
    
    # --- SECCIÓN PARA CARGAR EL RESULTADO CUANDO TERMINE ---
    st.subheader("🏁 Cargar Marcador Oficial y Sumar Puntos")
    
    if datos["partido_actual"].get("estado") == "finalizado":
        st.success("✅ El partido actual ya fue cerrado con éxito. Esperando nuevo partido.")
    else:
        st.write(f"Introduce el resultado final de: **{datos['partido_actual']['local']} vs {datos['partido_actual']['visitante']}**")
        
        col1, col2 = st.columns(2)
        with col1:
            gol_r_local = st.number_input(f"Goles {datos['partido_actual']['local']}", min_value=0, max_value=20, step=1, key="admin_gl")
        with col2:
            gol_r_vis = st.number_input(f"Goles {datos['partido_actual']['visitante']}", min_value=0, max_value=20, step=1, key="admin_gv")
            
        if st.button("🧠 Finalizar Partido y Calcular Puntos", use_container_width=True):
            conteo_procesados = 0
            
            # Recorremos pronósticos y sumamos los puntos directo al perfil del usuario
            for apodo, pronostico in datos.get("pronosticos", {}).items():
                if apodo in datos["usuarios"]:
                    gol_u_local = pronostico["local"]
                    gol_u_vis = pronostico["visitante"]
                    
                    nuevos_puntos = calcular_puntos(gol_u_local, gol_u_vis, gol_r_local, gol_r_vis)
                    datos["usuarios"][apodo]["puntos"] += nuevos_puntos
                    conteo_procesados += 1
            
            # Guardamos historial del juego para evitar pérdidas de información
            datos["historial_partidos"].append({
                "local": datos["partido_actual"]["local"],
                "visitante": datos["partido_actual"]["visitante"],
                "goles_local": gol_r_local,
                "goles_visitante": gol_r_vis
            })
            
            # Cambiamos estado para bloquear dobles ejecuciones accidentales
            datos["partido_actual"]["estado"] = "finalizado"
            
            guardar_datos(datos)
            st.success(f"⚽ ¡Partido cerrado! Marcador oficial: {datos['partido_actual']['local']} {gol_r_local} - {gol_r_vis} {datos['partido_actual']['visitante']}.")
            st.info(f"📊 Se procesaron los puntos de {conteo_procesados} amigos.")
            st.rerun()

# --- PESTAÑA: GENERAR INVITACIONES ---
with pestana_invitaciones:
    st.subheader("Generar Códigos de Registro")
    if st.button("➕ Generar 1 Código Nuevo", use_container_width=True):
        datos = cargar_datos() # Forzar lectura actualizada del JSON antes de añadir datos
        letras_numeros = string.ascii_uppercase + string.digits
        codigo_generado = "MUN-" + "".join(random.choices(letras_numeros, k=5))
        
        datos["codigos_registro"][codigo_generado] = {"usado": False, "por_usuario": ""}
        guardar_datos(datos)
        
        st.success(f"¡Código `{codigo_generado}` generado con éxito!")
        # Implementación de st.code para habilitar botón nativo de "Copiar al portapapeles"
        st.code(f"http://localhost:8501/?invitacion={codigo_generado}", language="markdown")
