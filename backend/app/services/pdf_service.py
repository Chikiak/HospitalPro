from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.user_repository import UserRepository

# Path to fonts directory
FONT_DIR = Path(__file__).parent / "fonts"


class MedicalRecordPDF(FPDF):
    """Custom PDF class for medical records."""
    
    def __init__(self):
        """Initialize PDF with UTF-8 font support."""
        super().__init__()
        
        # Register DejaVu fonts for UTF-8 support (accents, tildes)
        font_path = FONT_DIR / "DejaVuSans.ttf"
        if font_path.exists():
            self.add_font("DejaVu", "", str(font_path), uni=True)
            self.add_font("DejaVu", "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"), uni=True)
            self.add_font("DejaVu", "I", str(FONT_DIR / "DejaVuSans-Oblique.ttf"), uni=True)
            self._font_family = "DejaVu"
        else:
            # Fallback to Helvetica if DejaVu fonts are not available
            self._font_family = "Helvetica"
    
    def header(self):
        """Add header to each page."""
        self.set_font(self._font_family, 'B', 16)
        self.cell(0, 10, 'HospitalPro - Historia Clínica', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(5)
    
    def footer(self):
        """Add footer to each page."""
        self.set_y(-15)
        self.set_font(self._font_family, 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', align='C')


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
    pdf.set_font(pdf._font_family, 'B', 14)
    pdf.cell(0, 10, 'Datos del Paciente', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font(pdf._font_family, '', 12)
    pdf.cell(0, 8, f'Nombre: {patient.full_name}', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, f'DNI: {patient.dni}', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)
    
    # Registration Survey
    if medical_record.registration_survey:
        pdf.set_font(pdf._font_family, 'B', 14)
        pdf.cell(0, 10, 'Encuesta de Registro', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font(pdf._font_family, '', 11)
        
        survey = medical_record.registration_survey
        for key, value in survey.items():
            # Format key nicely
            formatted_key = key.replace('_', ' ').title()
            # Handle different value types
            if isinstance(value, (list, dict)):
                value_str = str(value)[:100]  # Limit length
            else:
                value_str = str(value)[:100] if value else "N/A"
            
            # Use cell instead of multi_cell to avoid wrapping issues
            try:
                pdf.cell(0, 6, f'{formatted_key}: {value_str}', new_x='LMARGIN', new_y='NEXT')
            except Exception:
                # If cell fails, skip this field
                pass
        
        pdf.ln(5)
    
    # Medical History Entries
    if medical_record.entries:
        pdf.set_font(pdf._font_family, 'B', 14)
        pdf.cell(0, 10, 'Historial de Consultas y Laboratorios', new_x='LMARGIN', new_y='NEXT')
        
        for idx, entry in enumerate(medical_record.entries, 1):
            pdf.set_font(pdf._font_family, 'B', 12)
            pdf.cell(0, 8, f'Entrada #{idx}', new_x='LMARGIN', new_y='NEXT')
            
            pdf.set_font(pdf._font_family, '', 11)
            
            # Entry details
            try:
                if 'timestamp' in entry:
                    pdf.cell(0, 6, f"Fecha: {entry['timestamp']}", new_x='LMARGIN', new_y='NEXT')
                
                if 'entry_type' in entry:
                    entry_type = entry['entry_type']
                    type_label = 'Consulta' if entry_type == 'consultation' else 'Resultado de Laboratorio'
                    pdf.cell(0, 6, f"Tipo: {type_label}", new_x='LMARGIN', new_y='NEXT')
                
                if 'specialty' in entry and entry['specialty']:
                    pdf.cell(0, 6, f"Especialidad: {entry['specialty']}", new_x='LMARGIN', new_y='NEXT')
                
                if 'doctor_name' in entry and entry['doctor_name']:
                    pdf.cell(0, 6, f"Doctor: {entry['doctor_name']}", new_x='LMARGIN', new_y='NEXT')
                
                if 'diagnosis' in entry and entry['diagnosis']:
                    diag_text = str(entry['diagnosis'])[:100]
                    pdf.cell(0, 6, f"Diagnóstico: {diag_text}", new_x='LMARGIN', new_y='NEXT')
                
                if 'notes' in entry and entry['notes']:
                    notes_text = str(entry['notes'])[:100]
                    pdf.cell(0, 6, f"Notas: {notes_text}", new_x='LMARGIN', new_y='NEXT')
                
                if 'results' in entry and entry['results']:
                    # Format results dict nicely
                    if isinstance(entry['results'], dict):
                        results_text = "Resultados: " + ", ".join([f"{k}: {v}" for k, v in entry['results'].items()])[:100]
                    else:
                        results_text = f"Resultados: {str(entry['results'])[:100]}"
                    pdf.cell(0, 6, results_text, new_x='LMARGIN', new_y='NEXT')
            except Exception:
                # If any field fails, skip it
                pass
            
            pdf.ln(3)
    
    # Footer with generation date
    pdf.ln(10)
    pdf.set_font(pdf._font_family, 'I', 10)
    generation_date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    pdf.cell(0, 8, f'Fecha de generación: {generation_date}', align='R', new_x='LMARGIN', new_y='NEXT')
    
    # Output to BytesIO
    pdf_bytes = BytesIO()
    pdf_output = pdf.output()
    pdf_bytes.write(pdf_output)
    pdf_bytes.seek(0)
    
    return pdf_bytes
