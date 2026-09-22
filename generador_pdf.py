from fpdf import FPDF
import datetime

def crear_acuse_pdf(curp, estatus, nivel_riesgo, accion):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Acuse de Cumplimiento Normativo (PLD/AML)", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 6, txt="Conforme al Enfoque Basado en Riesgos (LFPIORPI)", ln=True, align='C')
    pdf.ln(8)
    
    pdf.set_font("Arial", size=12)
    fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    pdf.cell(200, 8, txt=f"Fecha y Hora de Consulta: {fecha_actual}", ln=True)
    pdf.cell(200, 8, txt="Documento Analizado: Credencial para Votar (INE)", ln=True)
    pdf.cell(200, 8, txt=f"CURP Extraida: {curp}", ln=True)
    pdf.ln(5)
    
    # Estilos según el Nivel de Riesgo
    if nivel_riesgo == "ALTO":
        pdf.set_text_color(220, 20, 60) # Rojo
    elif nivel_riesgo == "MEDIO":
        pdf.set_text_color(255, 140, 0) # Naranja
    else:
        pdf.set_text_color(34, 139, 34) # Verde
        
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt=f"GRADO DE RIESGO ASIGNADO: {nivel_riesgo}", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=f"Dictamen: {estatus}\nAccion Requerida: {accion}")
    
    # Restaurar texto negro
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=11)
    pdf.ln(20)
    
    pdf.cell(200, 8, txt="___________________________________________________", ln=True, align='C')
    pdf.cell(200, 8, txt="Firma del Oficial de Cumplimiento Responsable", ln=True, align='C')
    
    ruta_pdf = f"acuse_{curp}.pdf"
    pdf.output(ruta_pdf)
    
    return ruta_pdf