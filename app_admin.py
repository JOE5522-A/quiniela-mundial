if st.button("🚪 Entrar", use_container_width=True):
    if apodo_ingresado in datos["usuarios"]:
        # 🚨 VALIDACIÓN DE SUSPENSIÓN ADICIONADA:
        if not datos["usuarios"][apodo_ingresado].get("activo", True):
            st.error("🔒 Tu cuenta ha sido suspendida por el administrador.")
        elif password_ingresado == datos["usuarios"][apodo_ingresado]["password"]:
            st.session_state["usuario_logueado"] = apodo_ingresado
            st.rerun()
        else: 
            st.error("❌ Contraseña incorrecta.")
    else: 
        st.error("❌ El apodo no existe.")
