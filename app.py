import streamlit as st
import os
import sqlite3
import pandas as pd
from lector import extraer_y_corregir_curp
from generador_pdf import crear_acuse_pdf
from auth import verificar_credenciales

st.set_page_config(page_title="LegalTech Compliance Portal", page_icon="🛡️", layout="wide")

st.title("🛡️ Portal de Expedientes y Validación de Identidad (KYC & AML)")
st.write("Sistema multitenant automatizado de cumplimiento normativo y Enfoque Basado en Riesgos.")

# Menú lateral de acceso corporativo real
st.sidebar.header("Acceso Corporativo")
empresa_input = st.sidebar.text_input("Nombre de la Empresa / Usuario")
password_input = st.sidebar.text_input("Contraseña", type="password")

# Validar credenciales contra la base de datos de usuarios
acceso_concedido = False
if empresa_input and password_input:
    if verificar_credenciales(empresa_input, password_input):
        acceso_concedido = True
        st.sidebar.success(f"Sesión activa: {empresa_input}")
    else:
        st.sidebar.error("Credenciales inválidas. Verifica tu usuario o contraseña.")

if acceso_concedido:
    
    st.subheader(f"📂 Cargar Documentación del Cliente — [{empresa_input}]")
    
    archivo_subido = st.file_uploader("Selecciona la imagen de la INE", type=["png", "jpg", "jpeg"])
    
    if archivo_subido is not None:
        ruta_temporal = "temp_ine.png"
        with open(ruta_temporal, "wb") as f:
            f.write(archivo_subido.getbuffer())
            
        st.image(archivo_subido, caption="INE Cargada", width=300)
        
        if st.button("🚀 Ejecutar Validación y Cruce PLD"):
            with st.spinner("Procesando documento bajo Enfoque Basado en Riesgos..."):
                # Enviamos la empresa actual para aislar su expediente
                resultado = extraer_y_corregir_curp(ruta_temporal, empresa_input)
                
            if "error" in resultado:
                st.error(resultado["error"])
            else:
                st.success("¡Expediente validado y registrado en la bóveda de la empresa!")
                
                st.info(f"**Empresa:** {empresa_input}  \n**Documento:** {resultado['documento']}  \n**CURP:** {resultado['curp']}  \n**Grado de Riesgo:** {resultado['nivel_riesgo']}  \n**Estatus:** {resultado['estatus']}")
                
                if resultado.get("nivel_riesgo") == "ALTO":
                    st.error(f"⚠️ Atención: {resultado['accion']}")
                else:
                    st.success(f"✅ Proceso Exitoso: {resultado['accion']}")
                    st.balloons()
                
                # Generación y descarga del PDF
                ruta_pdf = crear_acuse_pdf(
                    resultado["curp"], 
                    resultado["estatus"], 
                    resultado.get("nivel_riesgo", "BAJO"), 
                    resultado.get("accion", "Sin observaciones")
                )
                
                if os.path.exists(ruta_pdf):
                    with open(ruta_pdf, "rb") as pdf_file:
                        st.download_button(
                            label="📄 Descargar Acuse Legal con Enfoque Basado en Riesgos (PDF)",
                            data=pdf_file,
                            file_name=f"Acuse_Riesgo_{resultado['curp']}.pdf",
                            mime="application/pdf"
                        )
                
    st.divider()
    
    # Sección del Historial de Auditoría (Filtrado por Empresa Activa)
    st.subheader(f"📊 Historial de Expedientes y Auditoría — [{empresa_input}]")
    
    db_path = "expedientes.db"
    if os.path.exists(db_path):
        conexion = sqlite3.connect(db_path)
        try:
            # Filtramos estrictamente los expedientes que pertenecen a esta empresa
            df_registros = pd.read_sql_query(
                "SELECT fecha, documento, curp, estatus, nivel_riesgo FROM clientes WHERE empresa = ? ORDER BY id DESC", 
                conexion, 
                params=(empresa_input,)
            )
        except Exception:
            df_registros = pd.DataFrame()
        conexion.close()
        
        if not df_registros.empty:
            df_registros['fecha'] = df_registros['fecha'].astype(str).str.slice(0, 10)
            
            st.dataframe(df_registros, use_container_width=True, hide_index=True, column_config={
                "fecha": "Fecha de Registro",
                "documento": "Documento",
                "curp": "CURP",
                "estatus": "Estatus PLD",
                "nivel_riesgo": "Grado de Riesgo"
            })
            
            csv_data = df_registros.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Descargar Reporte de Auditoría de {empresa_input} (CSV)",
                data=csv_data,
                file_name=f"reporte_auditoria_{empresa_input}.csv",
                mime="text/csv",
            )
        else:
            st.info("Aún no hay expedientes registrados para esta empresa en el sistema.")
    else:
        st.info("Sube y procesa tu primer documento para inicializar la base de datos.")

else:
    st.info("👈 Ingresa los datos de acceso corporativo en el menú lateral.")
    st.markdown("""
    ### 🔑 Cuentas de prueba disponibles para demostración:
    * **Empresa 1:** `Despacho Juridico Garcia` | **Contraseña:** `garcia2026`
    * **Empresa 2:** `Financiera del Norte` | **Contraseña:** `norte2026`
    """)