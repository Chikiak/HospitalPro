import { z } from 'zod';

// Identification Step Schema
export const identificationSchema = z.object({
  dni: z.string()
    .min(7, 'DNI debe tener al menos 7 caracteres')
    .max(10, 'DNI debe tener máximo 10 caracteres')
    .regex(/^[0-9]+$/, 'DNI debe contener solo números'),
  firstName: z.string().min(2, 'Nombre debe tener al menos 2 caracteres'),
  lastName: z.string().min(2, 'Apellido debe tener al menos 2 caracteres'),
  dateOfBirth: z.string().min(1, 'Fecha de nacimiento es requerida'),
  phone: z.string().min(10, 'Teléfono debe tener al menos 10 dígitos'),
});

// Vitals Step Schema
export const vitalsSchema = z.object({
  temperature: z.number()
    .min(35, 'Temperatura muy baja')
    .max(43, 'Temperatura muy alta'),
  heartRate: z.number()
    .min(40, 'Frecuencia cardíaca muy baja')
    .max(200, 'Frecuencia cardíaca muy alta'),
  bloodPressureSystolic: z.number()
    .min(60, 'Presión sistólica muy baja')
    .max(250, 'Presión sistólica muy alta'),
  bloodPressureDiastolic: z.number()
    .min(40, 'Presión diastólica muy baja')
    .max(150, 'Presión diastólica muy alta'),
  oxygenSaturation: z.number()
    .min(70, 'Saturación de oxígeno muy baja')
    .max(100, 'Saturación máxima es 100%'),
  weight: z.number()
    .min(1, 'Peso debe ser mayor a 0')
    .max(300, 'Peso muy alto'),
});

// Medical History Step Schema
export const medicalHistorySchema = z.object({
  chronicDiseases: z.array(z.string()).default([]),
  allergies: z.array(z.string()).default([]),
  currentMedications: z.string().optional(),
  symptoms: z.string().min(10, 'Por favor describa los síntomas con más detalle'),
  emergencyContact: z.string().min(10, 'Contacto de emergencia debe tener al menos 10 dígitos'),
});

// Complete Admission Schema
export const admissionSchema = z.object({
  identification: identificationSchema,
  vitals: vitalsSchema,
  medicalHistory: medicalHistorySchema,
});

// Type inference
export type IdentificationData = z.infer<typeof identificationSchema>;
export type VitalsData = z.infer<typeof vitalsSchema>;
export type MedicalHistoryData = z.infer<typeof medicalHistorySchema>;
export type AdmissionData = z.infer<typeof admissionSchema>;

// Common chronic diseases for tag selection
export const COMMON_CHRONIC_DISEASES = [
  'Diabetes',
  'Hipertensión',
  'Asma',
  'Enfermedad Cardíaca',
  'Artritis',
  'Enfermedad Renal',
  'Cáncer',
  'EPOC',
  'Hipotiroidismo',
  'Obesidad',
];

// Common allergies for tag selection
export const COMMON_ALLERGIES = [
  'Penicilina',
  'Aspirina',
  'Ibuprofeno',
  'Látex',
  'Maní',
  'Mariscos',
  'Polen',
  'Ácaros',
  'Ninguna',
];
