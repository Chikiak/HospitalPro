import { useState } from 'react';
import { Download } from 'lucide-react';
import ExcelJS from 'exceljs';
import Button from '../../components/ui/Button';
import api from '../../lib/api';

interface PatientData {
  id: number;
  dni: string;
  full_name: string;
  is_active: boolean;
  medical_history: Record<string, unknown> | null;
  allergies: string | null;
}

export default function ExportExcel() {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);

    try {
      // Fetch patient data from backend
      const response = await api.get<PatientData[]>('/patients/');
      const patients = response.data;

      if (patients.length === 0) {
        setError('No hay pacientes registrados para exportar');
        return;
      }

      // Prepare data for Excel
      const excelData = patients.map((patient) => {
        // Extract medical history fields if available
        const medicalHistory = patient.medical_history || {};
        
        return {
          'ID': patient.id,
          'DNI': patient.dni,
          'Paciente': patient.full_name,
          'Estado': patient.is_active ? 'Activo' : 'Inactivo',
          'Alergias': patient.allergies || 'N/A',
          // Add medical history fields dynamically
          'Enfermedades Crónicas': medicalHistory.chronic_diseases || 'N/A',
          'Cirugías Previas': medicalHistory.previous_surgeries || 'N/A',
          'Medicación Actual': medicalHistory.current_medications || 'N/A',
          'Antecedentes Familiares': medicalHistory.family_history || 'N/A',
          'Hábitos': medicalHistory.habits || 'N/A',
          'Otros Datos Médicos': medicalHistory.other_medical_info || 'N/A',
        };
      });

      // Create workbook and worksheet using ExcelJS
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('Pacientes');

      // Add headers
      worksheet.columns = [
        { header: 'ID', key: 'ID', width: 10 },
        { header: 'DNI', key: 'DNI', width: 15 },
        { header: 'Paciente', key: 'Paciente', width: 30 },
        { header: 'Estado', key: 'Estado', width: 10 },
        { header: 'Alergias', key: 'Alergias', width: 30 },
        { header: 'Enfermedades Crónicas', key: 'Enfermedades Crónicas', width: 30 },
        { header: 'Cirugías Previas', key: 'Cirugías Previas', width: 30 },
        { header: 'Medicación Actual', key: 'Medicación Actual', width: 30 },
        { header: 'Antecedentes Familiares', key: 'Antecedentes Familiares', width: 30 },
        { header: 'Hábitos', key: 'Hábitos', width: 30 },
        { header: 'Otros Datos Médicos', key: 'Otros Datos Médicos', width: 30 },
      ];

      // Add data rows
      worksheet.addRows(excelData);

      // Style the header row
      worksheet.getRow(1).font = { bold: true };
      worksheet.getRow(1).fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFE0E0E0' },
      };

      // Generate filename with current date
      const now = new Date();
      const dateStr = now.toLocaleDateString('sv-SE'); // YYYY-MM-DD format
      const filename = `pacientes_${dateStr}.xlsx`;

      // Generate and download the file
      const buffer = await workbook.xlsx.writeBuffer();
      const blob = new Blob([buffer], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      
      // Create download link and trigger download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
      window.URL.revokeObjectURL(url);

    } catch (err) {
      console.error('Error al exportar datos:', err);
      setError('Error al exportar los datos. Por favor, intente nuevamente.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Exportar Datos de Pacientes</h2>
          <p className="text-sm text-slate-500 mt-1">
            Descarga un archivo Excel con la información de todos los pacientes registrados
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="premium-card p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="bg-primary/10 p-3 rounded-xl">
              <Download className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900">Exportar a Excel</h3>
              <p className="text-sm text-slate-500 mt-1">
                El archivo incluirá: DNI, Nombre completo, Alergias y datos del historial médico
              </p>
            </div>
          </div>
          <Button
            onClick={handleExport}
            isLoading={isExporting}
            className="flex items-center gap-2 whitespace-nowrap"
          >
            <Download className="h-4 w-4" />
            {isExporting ? 'Exportando...' : 'Descargar Excel'}
          </Button>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg">
        <p className="text-sm font-medium">
          <strong>Nota de Seguridad:</strong> Este archivo contiene información médica sensible. 
          Manéjelo con confidencialidad y de acuerdo a las políticas de privacidad del hospital.
        </p>
      </div>
    </div>
  );
}
