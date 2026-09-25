import streamlit as st
import os
import pandas as pd
from lector import procesar_expediente_completo, supabase
from generador_pdf import crear_acuse_pdf
from auth import verificar_credenciales

st.set_page_config(page_title="LegalTech Compliance Portal", page_icon="🛡️", layout="wide")

st.title("🛡️ Portal de Expedientes y Validación de Identidad (KYC & AML)")
st.write("Sistema multitenant automatizado de cumplimiento normativo y Enfoque Basado en Riesgos.")

# Menú lateral
st.sidebar.header("Acceso Corporativo")
empresa_input = st.sidebar.text_input("Nombre de la Empresa / Usuario")
password_input = st.sidebar.text_input("Contraseña", type="password")

acceso_concedido = False
if empresa_input and password_input:
    if verificar_credenciales(empresa_input, password_input):
        acceso_concedido = True
        st.sidebar.success(f"Sesión activa: {empresa_input}")
    else:
        st.sidebar.error("Credenciales inválidas. Verifica tu usuario o contraseña.")

if acceso_concedido:
    st.subheader(f"📂 Integración de Expediente LFPIORPI — [{empresa_input}]")
    
    col1, col2 = st.columns(2)
    
    with col1:
        archivo_ine = st.file_uploader("1. Sube la imagen de la INE", type=["png", "jpg", "jpeg"])
    with col2:
        archivo_comp = st.file_uploader("2. Sube el Comprobante de Domicilio (Opcional)", type=["png", "jpg", "jpeg"])
    
    if archivo_ine is not None:
        ruta_ine = "temp_ine.png"
        with open(ruta_ine, "wb") as f:
            f.write(archivo_ine.getbuffer())
            
        ruta_comp = None
        if archivo_comp is not None:
            ruta_comp = "temp_comp.png"
            with open(ruta_comp, "wb") as f:
                f.write(archivo_comp.getbuffer())
        
        if st.button("🚀 Ejecutar Validación Integral"):
            with st.spinner("Extrayendo datos y cruzando perfiles de riesgo..."):
                resultado = procesar_expediente_completo(ruta_ine, ruta_comp, empresa_input)
                
            if "error" in resultado:
                st.error(resultado["error"])
            else:
                st.success("¡Expediente procesado y almacenado en la bóveda corporativa!")
                
                st.info(f"**Empresa:** {empresa_input}  \n**Documentos:** {resultado['documento']}  \n**CURP:** {resultado['curp']}  \n**Grado de Riesgo Final:** {resultado['nivel_riesgo']}  \n**Estatus:** {resultado['estatus']}")
                
                if resultado.get("nivel_riesgo") in ["ALTO", "MEDIO"]:
                    st.warning(f"⚠️ Atención Requerida: {resultado['accion']}")
                else:
                    st.success(f"✅ Expediente Perfecto: {resultado['accion']}")
                    st.balloons()
                
                ruta_pdf = crear_acuse_pdf(
                    resultado["curp"], 
                    resultado["estatus"], 
                    resultado.get("nivel_riesgo", "BAJO"), 
                    resultado.get("accion", "Sin observaciones")
                )
                
                if os.path.exists(ruta_pdf):
                    with open(ruta_pdf, "rb") as pdf_file:
                        st.download_button(
                            label="📄 Descargar Acuse Oficial LFPIORPI (PDF)",
                            data=pdf_file,
                            file_name=f"Acuse_Expediente_{resultado['curp']}.pdf",
                            mime="application/pdf"
                        )
                
    st.divider()
    
    st.subheader(f"📊 Historial de Expedientes y Auditoría — [{empresa_input}]")
    
    try:
        respuesta = supabase.table("clientes").select("fecha, documento, curp, estatus, nivel_riesgo").eq("empresa", empresa_input).order("id", desc=True).execute()
        df_registros = pd.DataFrame(respuesta.data)
    except Exception as e:
        df_registros = pd.DataFrame()
        st.error(f"Error de conexión con la base de datos: {e}")
        
    if not df_registros.empty:
        df_registros['fecha'] = pd.to_datetime(df_registros['fecha']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
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
        st.info("Aún no hay expedientes registrados.")

else:
    st.info("👈 Ingresa los datos de acceso corporativo en el menú lateral.")
    st.markdown("""
    ### 🔑 Cuentas de prueba disponibles para demostración:
    * **Empresa 1:** `Despacho Juridico Garcia` | **Contraseña:** `garcia2026`
    * **Empresa 2:** `Financiera del Norte` | **Contraseña:** `norte2026`
    """)
