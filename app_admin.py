import streamlit as st
import json
import random
import string

# Configuración del panel de administración
st.set_page_config(page_title="Panel Administrador", layout="centered")

# --- FUNCIONES PARA MANEJAR EL ALMACÉN ---
def cargar_datos():
    with open("datos_quinela.json", "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_datos(datos):
    with open("datos_quinela.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

# --- FUNCIÓN MATEMÁTICA: CALCULAR REGLAS DE PUNTOS ---
def calcular_puntos(gol_u_mex, gol_u_rsa, gol_r_mex, gol_r_rsa):
    ganador_real = "mex" if gol_r_mex > gol_r_rsa else ("rsa" if gol_r_rsa > gol_r_mex else "empate")
    ganador_pronostico = "mex" if gol_u_mex > gol_u_rsa else ("rsa" if gol_u_rsa > gol_u_mex else "empate")
    marcador_exacto = (gol_u_mex == gol_r_mex) and (gol_u_rsa == gol_r_rsa)
    
    if ganador_real == "empate" and ganador_pronostico == "empate":
        return 4 if marcador_exacto else 1
    elif ganador_real == ganador_pronostico:
        return 5 if marcador_exacto else 3
    else:
        return 0

datos = cargar_datos()

if "codigos_registro" not in datos:
    datos["codigos_registro"] = {}

st.title("⚙️ Panel de Control - Administrador")

if st.button("🔄 Actualizar Pantalla / Refrescar Datos", use_container_width=True):
    st.toast("Datos sincronizados")

pestana_invitaciones, pestana_resultados = st.tabs(["🎫 Generar Invitaciones", "⚽ Cargar Resultados FIFA"])

# --- PESTAÑA 1: GENERAR INVITACIONES ---
with pestana_invitaciones:
    st.subheader("Generar Códigos de Registro para Amigos")
    
    if st.button("➕ Generar 1 Código Nuevo", use_container_width=True):
        letras_numeros = string.ascii_uppercase + string.digits
        codigo_generado = "MUN-" + "".join(random.choices(letras_numeros, k=5))
        
        datos["codigos_registro"][codigo_generado] = {"usado": False, "por_usuario": ""}
        guardar_datos(datos)
        
        st.success(f"¡Código generado!")
        enlace_amigo = f"http://localhost:8501/?invitacion={codigo_generado}"
        st.info(f"📋 **Enlace para WhatsApp:**\n`{enlace_amigo}`")

    st.divider()
    st.write("📊 **Historial de códigos creados:**")
    datos = cargar_datos()
    if datos["codigos_registro"]:
        for cod, info in datos["codigos_registro"].items():
            estado = "🔴 Usado por " + info["por_usuario"] if info["usado"] else "🟢 Libre / Disponible"
            st.write(f"- **{cod}**: {estado}")
    else:
        st.write("Aún no has generado ningún código.")

# --- PESTAÑA 2: CARGAR RESULTADOS ---
with pestana_resultados:
    st.subheader("Resultados Oficiales del Día")
    st.markdown("### 🇲🇽 México vs 🇿🇦 Sudáfrica")
    
    col1, col2 = st.columns(2)
    with col1:
        gol_r_mex = st.number_input("Goles México (Real)", min_value=0, max_value=10, step=1, key="real_mex")
    with col2:
        gol_r_rsa = st.number_input("Goles Sudáfrica (Real)", min_value=0, max_value=10, step=1, key="real_rsa")
        
    st.divider()
    
    if st.button("🧠 Finalizar Partido y Calcular Puntos", use_container_width=True):
        datos["resultados_reales"]["mex"] = gol_r_mex
        datos["resultados_reales"]["rsa"] = gol_r_rsa
        
        conteo_procesados = 0
        for apodo, pronostico in datos.get("pronosticos", {}).items():
            gol_u_mex = pronostico["mex"]
            gol_u_rsa = pronostico["rsa"]
            
            nuevos_puntos = calcular_puntos(gol_u_mex, gol_u_rsa, gol_r_mex, gol_r_rsa)
            datos["usuarios"][apodo]["puntos"] += nuevos_puntos
            conteo_procesados += 1
            
        guardar_datos(datos)
        st.success(f"⚽ ¡Partido cerrado! Marcador: México {gol_r_mex} - {gol_r_rsa} Sudáfrica.")
        st.info(f"📊 Se procesaron los puntos de {conteo_procesados} amigos activos.")
