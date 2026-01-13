import React, { useEffect } from 'react';
import {
  useForm,
  type SubmitHandler,
  type UseFormRegister,
  type FieldErrors,
  type UseFormWatch,
  type UseFormSetValue,
} from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  admissionSchema,
  identificationSchema,
  vitalsSchema,
  medicalHistorySchema,
  type AdmissionData,
  COMMON_CHRONIC_DISEASES,
  COMMON_ALLERGIES,
} from '../schemas';
import { Wizard, WizardProgressBar, WizardNavigation, useWizard } from './Wizard/WizardContext';
import WizardStep from './Wizard/WizardStep';
import { HeartPulse } from 'lucide-react';

const STORAGE_KEY = 'admission_form_draft';

// Step 1: Identification Component
const IdentificationStep: React.FC<{
  register: UseFormRegister<AdmissionData>;
  errors: FieldErrors<AdmissionData>;
  watch: UseFormWatch<AdmissionData>;
}> = ({ register, errors, watch }) => {
  const { setCanGoNext } = useWizard();

  useEffect(() => {
    const subscription = watch((value) => {
      const result = identificationSchema.safeParse(value.identification);
      setCanGoNext(result.success);
    });
    return () => subscription.unsubscribe();
  }, [watch, setCanGoNext]);

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="dni" className="block text-sm font-medium text-gray-700 mb-1">
          DNI / Documento de Identidad *
        </label>
        <input
          id="dni"
          type="text"
          {...register('identification.dni')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="12345678"
        />
        {errors.identification?.dni && (
          <p className="mt-1 text-sm text-red-600">{errors.identification.dni.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
            Nombre *
          </label>
          <input
            id="firstName"
            type="text"
            {...register('identification.firstName')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Juan"
          />
          {errors.identification?.firstName && (
            <p className="mt-1 text-sm text-red-600">{errors.identification.firstName.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
            Apellido *
          </label>
          <input
            id="lastName"
            type="text"
            {...register('identification.lastName')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Pérez"
          />
          {errors.identification?.lastName && (
            <p className="mt-1 text-sm text-red-600">{errors.identification.lastName.message}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="dateOfBirth" className="block text-sm font-medium text-gray-700 mb-1">
          Fecha de Nacimiento *
        </label>
        <input
          id="dateOfBirth"
          type="date"
          {...register('identification.dateOfBirth')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {errors.identification?.dateOfBirth && (
          <p className="mt-1 text-sm text-red-600">{errors.identification.dateOfBirth.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
          Teléfono de Contacto *
        </label>
        <input
          id="phone"
          type="tel"
          {...register('identification.phone')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="1234567890"
        />
        {errors.identification?.phone && (
          <p className="mt-1 text-sm text-red-600">{errors.identification.phone.message}</p>
        )}
      </div>
    </div>
  );
};

// Step 2: Vitals Component
const VitalsStep: React.FC<{
  register: UseFormRegister<AdmissionData>;
  errors: FieldErrors<AdmissionData>;
  watch: UseFormWatch<AdmissionData>;
}> = ({ register, errors, watch }) => {
  const { setCanGoNext } = useWizard();

  useEffect(() => {
    const subscription = watch((value) => {
      const vitalsData = {
        temperature: parseFloat(String(value.vitals?.temperature)) || 0,
        heartRate: parseFloat(String(value.vitals?.heartRate)) || 0,
        bloodPressureSystolic: parseFloat(String(value.vitals?.bloodPressureSystolic)) || 0,
        bloodPressureDiastolic: parseFloat(String(value.vitals?.bloodPressureDiastolic)) || 0,
        oxygenSaturation: parseFloat(String(value.vitals?.oxygenSaturation)) || 0,
        weight: parseFloat(String(value.vitals?.weight)) || 0,
      };
      const result = vitalsSchema.safeParse(vitalsData);
      setCanGoNext(result.success);
    });
    return () => subscription.unsubscribe();
  }, [watch, setCanGoNext]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="temperature" className="block text-sm font-medium text-gray-700 mb-1">
            Temperatura (°C) *
          </label>
          <input
            id="temperature"
            type="number"
            step="0.1"
            {...register('vitals.temperature', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="36.5"
          />
          {errors.vitals?.temperature && (
            <p className="mt-1 text-sm text-red-600">{errors.vitals.temperature.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="heartRate" className="block text-sm font-medium text-gray-700 mb-1">
            Frecuencia Cardíaca (bpm) *
          </label>
          <input
            id="heartRate"
            type="number"
            {...register('vitals.heartRate', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="70"
          />
          {errors.vitals?.heartRate && (
            <p className="mt-1 text-sm text-red-600">{errors.vitals.heartRate.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="bloodPressureSystolic" className="block text-sm font-medium text-gray-700 mb-1">
            Presión Arterial Sistólica (mmHg) *
          </label>
          <input
            id="bloodPressureSystolic"
            type="number"
            {...register('vitals.bloodPressureSystolic', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="120"
          />
          {errors.vitals?.bloodPressureSystolic && (
            <p className="mt-1 text-sm text-red-600">{errors.vitals.bloodPressureSystolic.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="bloodPressureDiastolic" className="block text-sm font-medium text-gray-700 mb-1">
            Presión Arterial Diastólica (mmHg) *
          </label>
          <input
            id="bloodPressureDiastolic"
            type="number"
            {...register('vitals.bloodPressureDiastolic', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="80"
          />
          {errors.vitals?.bloodPressureDiastolic && (
            <p className="mt-1 text-sm text-red-600">{errors.vitals.bloodPressureDiastolic.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="oxygenSaturation" className="block text-sm font-medium text-gray-700 mb-1">
            Saturación de Oxígeno (%) *
          </label>
          <input
            id="oxygenSaturation"
            type="number"
            {...register('vitals.oxygenSaturation', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="98"
          />
          {errors.vitals?.oxygenSaturation && (
            <p className="mt-1 text-sm text-red-600">{errors.vitals.oxygenSaturation.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="weight" className="block text-sm font-medium text-gray-700 mb-1">
            Peso (kg) *
          </label>
          <input
            id="weight"
            type="number"
            step="0.1"
            {...register('vitals.weight', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="70"
          />
          {errors.vitals?.weight && (
            <p className="mt-1 text-sm text-red-600">{errors.vitals.weight.message}</p>
          )}
        </div>
      </div>
    </div>
  );
};

// Step 3: Medical History Component
const MedicalHistoryStep: React.FC<{
  register: UseFormRegister<AdmissionData>;
  errors: FieldErrors<AdmissionData>;
  watch: UseFormWatch<AdmissionData>;
  setValue: UseFormSetValue<AdmissionData>;
}> = ({ register, errors, watch, setValue }) => {
  const { setCanGoNext } = useWizard();
  const chronicDiseases = watch('medicalHistory.chronicDiseases') || [];
  const allergies = watch('medicalHistory.allergies') || [];

  useEffect(() => {
    const subscription = watch((value) => {
      const result = medicalHistorySchema.safeParse(value.medicalHistory);
      setCanGoNext(result.success);
    });
    return () => subscription.unsubscribe();
  }, [watch, setCanGoNext]);

  const toggleChronicDisease = (disease: string) => {
    const current = chronicDiseases || [];
    const updated = current.includes(disease)
      ? current.filter((d: string) => d !== disease)
      : [...current, disease];
    setValue('medicalHistory.chronicDiseases', updated);
  };

  const toggleAllergy = (allergy: string) => {
    const current = allergies || [];
    const updated = current.includes(allergy)
      ? current.filter((a: string) => a !== allergy)
      : [...current, allergy];
    setValue('medicalHistory.allergies', updated);
  };

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Enfermedades Crónicas
        </label>
        <div className="flex flex-wrap gap-2">
          {COMMON_CHRONIC_DISEASES.map((disease) => (
            <button
              key={disease}
              type="button"
              onClick={() => toggleChronicDisease(disease)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                chronicDiseases.includes(disease)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {disease}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Alergias
        </label>
        <div className="flex flex-wrap gap-2">
          {COMMON_ALLERGIES.map((allergy) => (
            <button
              key={allergy}
              type="button"
              onClick={() => toggleAllergy(allergy)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                allergies.includes(allergy)
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {allergy}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label htmlFor="currentMedications" className="block text-sm font-medium text-gray-700 mb-1">
          Medicamentos Actuales
        </label>
        <textarea
          id="currentMedications"
          {...register('medicalHistory.currentMedications')}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Liste los medicamentos que toma actualmente..."
        />
      </div>

      <div>
        <label htmlFor="symptoms" className="block text-sm font-medium text-gray-700 mb-1">
          Síntomas Actuales *
        </label>
        <textarea
          id="symptoms"
          {...register('medicalHistory.symptoms')}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Describa detalladamente los síntomas que presenta..."
        />
        {errors.medicalHistory?.symptoms && (
          <p className="mt-1 text-sm text-red-600">{errors.medicalHistory.symptoms.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="emergencyContact" className="block text-sm font-medium text-gray-700 mb-1">
          Contacto de Emergencia *
        </label>
        <input
          id="emergencyContact"
          type="tel"
          {...register('medicalHistory.emergencyContact')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="1234567890"
        />
        {errors.medicalHistory?.emergencyContact && (
          <p className="mt-1 text-sm text-red-600">{errors.medicalHistory.emergencyContact.message}</p>
        )}
      </div>
    </div>
  );
};

// Main Form Component
const AdmissionFormContent: React.FC = () => {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<AdmissionData>({
    // Type assertion is necessary due to a known incompatibility between @hookform/resolvers
    // and TypeScript's verbatimModuleSyntax option. The zodResolver is correctly typed at runtime
    // but TypeScript's strict module syntax validation incorrectly flags it as incompatible.
    // This is a known issue: https://github.com/react-hook-form/resolvers/issues/630
    // The resolver works correctly and provides full type safety for form validation.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(admissionSchema) as any,
    mode: 'onChange',
    defaultValues: {
      identification: {
        dni: '',
        firstName: '',
        lastName: '',
        dateOfBirth: '',
        phone: '',
      },
      vitals: {
        temperature: 36.5,
        heartRate: 70,
        bloodPressureSystolic: 120,
        bloodPressureDiastolic: 80,
        oxygenSaturation: 98,
        weight: 70,
      },
      medicalHistory: {
        chronicDiseases: [],
        allergies: [],
        currentMedications: '',
        symptoms: '',
        emergencyContact: '',
      },
    },
  });

  // Auto-save to localStorage
  useEffect(() => {
    const subscription = watch((value) => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    });
    return () => subscription.unsubscribe();
  }, [watch]);

  // Restore from localStorage on mount
  useEffect(() => {
    const savedData = localStorage.getItem(STORAGE_KEY);
    if (savedData) {
      try {
        const parsed = JSON.parse(savedData) as Partial<AdmissionData>;
        Object.keys(parsed).forEach((key) => {
          setValue(key as keyof AdmissionData, parsed[key as keyof AdmissionData] as never);
        });
      } catch (e) {
        console.error('Failed to restore form data:', e);
      }
    }
  }, [setValue]);

  const onSubmit: SubmitHandler<AdmissionData> = (data) => {
    console.log('Admission Form Data:', JSON.stringify(data, null, 2));
    localStorage.removeItem(STORAGE_KEY);
    alert('Formulario enviado exitosamente! Revisa la consola para ver los datos.');
  };

  const handleSave = () => {
    const currentData = watch();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(currentData));
    alert('Borrador guardado exitosamente!');
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="w-full">
      <WizardProgressBar className="mb-8" />

      <WizardStep
        step={0}
        title="Identificación del Paciente"
        description="Ingrese los datos personales del paciente"
      >
        <IdentificationStep register={register} errors={errors} watch={watch} />
      </WizardStep>

      <WizardStep
        step={1}
        title="Signos Vitales"
        description="Registre los signos vitales del paciente"
      >
        <VitalsStep register={register} errors={errors} watch={watch} />
      </WizardStep>

      <WizardStep
        step={2}
        title="Historia Médica"
        description="Complete la información médica del paciente"
      >
        <MedicalHistoryStep
          register={register}
          errors={errors}
          watch={watch}
          setValue={setValue}
        />
      </WizardStep>

      <WizardNavigation onSave={handleSave} className="mt-8" />
    </form>
  );
};

// Wrapper Component
const AdmissionForm: React.FC = () => {
  const handleComplete = () => {
    // This function intentionally left empty as form submission is handled via handleSubmit
    // The Wizard component calls this when the user clicks the final "Enviar" button
    // which triggers the form's onSubmit handler
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-blue-100 p-3 rounded-full">
              <HeartPulse className="h-10 w-10 text-blue-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 text-center mb-2">
            Triaje Digital
          </h1>
          <p className="text-gray-600 text-center mb-8">
            Complete el formulario de admisión del paciente
          </p>

          <Wizard totalSteps={3} onComplete={handleComplete}>
            <AdmissionFormContent />
          </Wizard>
        </div>
      </div>
    </div>
  );
};

export default AdmissionForm;
