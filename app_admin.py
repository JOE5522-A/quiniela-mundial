import streamlit as st
import json
import random
import string

st.set_page_config(page_title="Panel Administrador", layout="centered")

def cargar_datos():
    with open("datos_quinela.json", "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_datos(datos):
    with open("datos_quinela.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# Lógica de cálculo de puntos basada en tus 4 reglas
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

datos = cargar_datos()

# Aseguramos que existan las secciones necesarias en el archivo
if "partido_actual" not in datos:
    datos["partido_actual"] = {"local": "México", "visitante": "Sudáfrica"}
if "codigos_registro" not in datos:
    datos["codigos_registro"] = {}

st.title("⚙️ Panel de Control - Administrador")

pestana_partidos, pestana_invitaciones = st.tabs(["⚽ Partidos del Día", "🎫 Generar Invitaciones"])

# --- NUEVA PESTAÑA: CONFIGURAR Y CERRAR PARTIDOS ---
with pestana_partidos:
    st.subheader("📌 Configurar Partido Activo")
    st.write("Escribe aquí los equipos que jugarán hoy para actualizar la app de tus amigos:")
    
    nuevo_local = st.text_input("⚽ Equipo Local:", value=datos["partido_actual"]["local"])
    nuevo_visitante = st.text_input("⚽ Equipo Visitante:", value=datos["partido_actual"]["visitante"])
    
    if st.button("📢 Cambiar Partido del Día", use_container_width=True):
        datos["partido_actual"]["local"] = nuevo_local
        datos["partido_actual"]["visitante"] = nuevo_visitante
        # Al cambiar de partido, limpiamos los pronósticos del juego anterior
        datos["pronosticos"] = {} 
        guardar_datos(datos)
        st.success(f"¡Activado con éxito! Ahora tus amigos verán en su celular: {nuevo_local} vs {nuevo_visitante}")

    st.divider()
    
    # --- SECCIÓN PARA CARGAR EL RESULTADO CUANDO TERMINE ---
    st.subheader("🏁 Cargar Marcador Oficial y Sumar Puntos")
    st.write(f"Introduce el resultado final de: **{datos['partido_actual']['local']} vs {datos['partido_actual']['visitante']}**")
    
    col1, col2 = st.columns(2)
    with col1:
        gol_r_local = st.number_input(f"Goles {datos['partido_actual']['local']}", min_value=0, max_value=10, step=1)
    with col2:
        gol_r_vis = st.number_input(f"Goles {datos['partido_actual']['visitante']}", min_value=0, max_value=10, step=1)
        
    if st.button("🧠 Finalizar Partido y Calcular Puntos", use_container_width=True):
        conteo_procesados = 0
        for apodo, pronostico in datos.get("pronosticos", {}).items():
            gol_u_local = pronostico["local"]
            gol_u_vis = pronostico["visitante"]
            
            nuevos_puntos = calcular_puntos(gol_u_local, gol_u_vis, gol_r_local, gol_r_vis)
            datos["usuarios"][apodo]["puntos"] += nuevos_puntos
            conteo_procesados += 1
            
        guardar_datos(datos)
        st.success(f"⚽ ¡Partido cerrado! Marcador oficial: {datos['partido_actual']['local']} {gol_r_local} - {gol_r_vis} {datos['partido_actual']['visitante']}.")
        st.info(f"📊 Se procesaron los puntos de {conteo_procesados} amigos.")

# --- PESTAÑA 2: GENERAR INVITACIONES ---
with pestana_invitaciones:
    st.subheader("Generar Códigos de Registro")
    if st.button("➕ Generar 1 Código Nuevo", use_container_width=True):
        letras_numeros = string.ascii_uppercase + string.digits
        codigo_generado = "MUN-" + "".join(random.choices(letras_numeros, k=5))
        datos["codigos_registro"][codigo_generado] = {"usado": False, "por_usuario": ""}
        guardar_datos(datos)
        st.success(f"¡Código generado!")
        st.info(f"📋 **Enlace para WhatsApp:**\n`http://localhost:8501/?invitacion={codigo_generado}`")
