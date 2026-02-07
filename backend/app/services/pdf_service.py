from datetime import datetime
from io import BytesIO
from typing import Any

from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.user_repository import UserRepository


class MedicalRecordPDF(FPDF):
    """Custom PDF class for medical records."""
    
    def header(self):
        """Add header to each page."""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'HospitalPro - Historia Clinica', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        """Add footer to each page."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')


async def generate_medical_record_pdf(patient_id: int, db: AsyncSession) -> BytesIO:
    """
    Generate a PDF of a patient's medical record.
    
    Args:
        patient_id: The patient's user ID
        db: Database session
        
    Returns:
        BytesIO object containing the PDF data
    """
    # Get patient data
    user_repo = UserRepository(db)
    patient = await user_repo.get_by_id(patient_id)
    
    if not patient:
        raise ValueError(f"Patient {patient_id} not found")
    
    # Get medical record
    medical_record_repo = MedicalRecordRepository(db)
    medical_record = await medical_record_repo.get_by_patient_id(patient_id)
    
    if not medical_record:
        raise ValueError(f"No medical record found for patient {patient_id}")
    
    # Create PDF
    pdf = MedicalRecordPDF()
    pdf.add_page()
    
    # Patient Information
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Datos del Paciente', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Nombre: {patient.full_name}', 0, 1)
    pdf.cell(0, 8, f'DNI: {patient.dni}', 0, 1)
    pdf.ln(5)
    
    # Registration Survey
    if medical_record.registration_survey:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Encuesta de Registro', 0, 1)
        pdf.set_font('Arial', '', 11)
        
        survey = medical_record.registration_survey
        for key, value in survey.items():
            # Format key nicely
            formatted_key = key.replace('_', ' ').title()
            # Handle different value types
            if isinstance(value, (list, dict)):
                value_str = str(value)
            else:
                value_str = str(value) if value else "N/A"
            
            pdf.multi_cell(0, 6, f'{formatted_key}: {value_str}')
        
        pdf.ln(5)
    
    # Medical History Entries
    if medical_record.entries:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Historial de Consultas y Laboratorios', 0, 1)
        
        for idx, entry in enumerate(medical_record.entries, 1):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, f'Entrada #{idx}', 0, 1)
            
            pdf.set_font('Arial', '', 11)
            
            # Entry details
            if 'timestamp' in entry:
                pdf.cell(0, 6, f"Fecha: {entry['timestamp']}", 0, 1)
            
            if 'entry_type' in entry:
                entry_type = entry['entry_type']
                type_label = 'Consulta' if entry_type == 'consultation' else 'Resultado de Laboratorio'
                pdf.cell(0, 6, f"Tipo: {type_label}", 0, 1)
            
            if 'specialty' in entry and entry['specialty']:
                pdf.cell(0, 6, f"Especialidad: {entry['specialty']}", 0, 1)
            
            if 'doctor_name' in entry and entry['doctor_name']:
                pdf.cell(0, 6, f"Doctor: {entry['doctor_name']}", 0, 1)
            
            if 'diagnosis' in entry and entry['diagnosis']:
                pdf.multi_cell(0, 6, f"Diagnostico: {entry['diagnosis']}")
            
            if 'notes' in entry and entry['notes']:
                pdf.multi_cell(0, 6, f"Notas: {entry['notes']}")
            
            if 'results' in entry and entry['results']:
                pdf.multi_cell(0, 6, f"Resultados: {entry['results']}")
            
            pdf.ln(3)
    
    # Footer with generation date
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    generation_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    pdf.cell(0, 8, f'Fecha de generacion: {generation_date}', 0, 1, 'R')
    
    # Output to BytesIO
    pdf_bytes = BytesIO()
    pdf_output = pdf.output(dest='S').encode('latin1')
    pdf_bytes.write(pdf_output)
    pdf_bytes.seek(0)
    
    return pdf_bytes
