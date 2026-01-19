import { useState } from 'react'
import { Settings, Stethoscope, FlaskConical } from 'lucide-react'
import Tabs from '../components/ui/Tabs'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

// Types
interface DaySchedule {
  enabled: boolean
  start_time: string
  duration: number
  rotation: string
}

interface ScheduleConfig {
  [key: string]: DaySchedule
}

const DAYS = [
  { id: 'monday', label: 'Lunes' },
  { id: 'tuesday', label: 'Martes' },
  { id: 'wednesday', label: 'Miércoles' },
  { id: 'thursday', label: 'Jueves' },
  { id: 'friday', label: 'Viernes' },
  { id: 'saturday', label: 'Sábado' },
  { id: 'sunday', label: 'Domingo' },
]

const ROTATION_OPTIONS = [
  { value: 'fixed', label: 'Fijo' },
  { value: 'every_2_weeks', label: 'Cada 2 semanas' },
  { value: 'every_4_weeks', label: 'Cada 4 semanas' },
  { value: 'monthly', label: 'Mensual' },
]

const DEFAULT_SCHEDULE: DaySchedule = {
  enabled: false,
  start_time: '08:00',
  duration: 30,
  rotation: 'fixed',
}

export default function AdminSettings() {
  const [specialtySchedule, setSpecialtySchedule] = useState<ScheduleConfig>(
    DAYS.reduce((acc, day) => ({
      ...acc,
      [day.id]: { ...DEFAULT_SCHEDULE },
    }), {})
  )

  const [laboratorySchedule, setLaboratorySchedule] = useState<ScheduleConfig>(
    DAYS.reduce((acc, day) => ({
      ...acc,
      [day.id]: { ...DEFAULT_SCHEDULE },
    }), {})
  )

  const updateSchedule = (
    type: 'specialty' | 'laboratory',
    dayId: string,
    field: keyof DaySchedule,
    value: boolean | string | number
  ) => {
    const setter = type === 'specialty' ? setSpecialtySchedule : setLaboratorySchedule
    setter((prev) => ({
      ...prev,
      [dayId]: {
        ...prev[dayId],
        [field]: value,
      },
    }))
  }

  const handleSave = () => {
    console.log('Specialty Schedule:', specialtySchedule)
    console.log('Laboratory Schedule:', laboratorySchedule)
    // TODO: Implement API call to save settings
  }

  const handleCancel = () => {
    // Reset to default or navigate away
    console.log('Cancelling changes')
    // TODO: Implement navigation or reset functionality
  }

  const renderScheduleConfig = (type: 'specialty' | 'laboratory') => {
    const schedule = type === 'specialty' ? specialtySchedule : laboratorySchedule

    return (
      <div className="space-y-4">
        {DAYS.map((day) => {
          const config = schedule[day.id]
          return (
            <div
              key={day.id}
              className="premium-card hover:shadow-xl transition-all duration-300"
            >
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-end">
                {/* Day Name and Enable Checkbox */}
                <div className="md:col-span-3 flex items-center gap-4">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id={`${type}-${day.id}-enabled`}
                      checked={config.enabled}
                      onChange={(e) =>
                        updateSchedule(type, day.id, 'enabled', e.target.checked)
                      }
                      className="h-5 w-5 rounded-lg border-2 border-slate-300 text-primary focus:ring-2 focus:ring-primary/20 focus:ring-offset-2 transition-all cursor-pointer"
                    />
                    <label
                      htmlFor={`${type}-${day.id}-enabled`}
                      className="text-sm font-bold text-slate-700 cursor-pointer select-none"
                    >
                      {day.label}
                    </label>
                  </div>
                </div>

                {/* Start Time */}
                <div className="md:col-span-3">
                  <Input
                    type="time"
                    label="Hora de inicio"
                    value={config.start_time}
                    onChange={(e) =>
                      updateSchedule(type, day.id, 'start_time', e.target.value)
                    }
                    disabled={!config.enabled}
                  />
                </div>

                {/* Duration */}
                <div className="md:col-span-3">
                  <Input
                    type="number"
                    label="Duración (min)"
                    value={config.duration}
                    onChange={(e) =>
                      updateSchedule(type, day.id, 'duration', parseInt(e.target.value) || 0)
                    }
                    disabled={!config.enabled}
                    min="5"
                    step="5"
                  />
                </div>

                {/* Rotation */}
                <div className="md:col-span-3">
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2 ml-1">
                    Rotación
                  </label>
                  <select
                    value={config.rotation}
                    onChange={(e) =>
                      updateSchedule(type, day.id, 'rotation', e.target.value)
                    }
                    disabled={!config.enabled}
                    className="flex h-12 w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3 text-sm transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-primary/10 focus:border-primary focus:bg-white disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {ROTATION_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <h1 className="text-4xl font-black tracking-tight text-slate-900">
            <Settings className="inline-block h-10 w-10 mr-3 text-primary" />
            Configuración <span className="text-primary">Administrativa</span>
          </h1>
          <p className="text-slate-500 font-medium">
            Configure horarios y disponibilidad para especialidades y laboratorio.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleCancel}>
            Cancelar
          </Button>
          <Button onClick={handleSave}>
            Guardar Cambios
          </Button>
        </div>
      </div>

      {/* Tabs Content */}
      <div className="premium-card !p-8 border-none shadow-2xl">
        <Tabs
          tabs={[
            {
              id: 'specialties',
              label: 'Especialidades',
              icon: <Stethoscope className="h-5 w-5" />,
            },
            {
              id: 'laboratory',
              label: 'Laboratorio',
              icon: <FlaskConical className="h-5 w-5" />,
            },
          ]}
          defaultTab="specialties"
        >
          {(activeTab) => (
            <div className="mt-6">
              {activeTab === 'specialties' && (
                <div className="space-y-6">
                  <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                    <Stethoscope className="h-6 w-6 text-primary" />
                    <div>
                      <h3 className="text-lg font-bold text-slate-900">
                        Configuración de Especialidades
                      </h3>
                      <p className="text-sm text-slate-500">
                        Configure los horarios de atención para cada día de la semana.
                      </p>
                    </div>
                  </div>
                  {renderScheduleConfig('specialty')}
                </div>
              )}
              {activeTab === 'laboratory' && (
                <div className="space-y-6">
                  <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                    <FlaskConical className="h-6 w-6 text-primary" />
                    <div>
                      <h3 className="text-lg font-bold text-slate-900">
                        Configuración de Laboratorio
                      </h3>
                      <p className="text-sm text-slate-500">
                        Configure los horarios de disponibilidad del laboratorio.
                      </p>
                    </div>
                  </div>
                  {renderScheduleConfig('laboratory')}
                </div>
              )}
            </div>
          )}
        </Tabs>
      </div>
    </div>
  )
}
