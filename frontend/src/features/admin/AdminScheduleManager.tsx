import { useState, useEffect } from 'react'
import { Plus, Clock, Save, ArrowLeft, AlertTriangle } from 'lucide-react'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import api from '../../lib/api'

// Types (Mirrors backend)
interface DaySchedule {
    id?: number
    enabled: boolean
    day_of_week: number
    start_time: string
    duration: number
    max_turns: number
    rotation_type: 'fixed' | 'alternated'
    rotation_weeks: number
    start_date?: string // New field for rotation anchor
    deadline_time?: string // Deadline time for sample collection (for labs)
    warning_message?: string // Warning message to display to patients
}

interface Category {
    name: string
    type: 'specialty' | 'laboratory'
    schedules: Record<number, DaySchedule>
}

const DAYS = [
    { id: 0, label: 'Lunes' },
    { id: 1, label: 'Martes' },
    { id: 2, label: 'Miércoles' },
    { id: 3, label: 'Jueves' },
    { id: 4, label: 'Viernes' },
    { id: 5, label: 'Sábado' },
    { id: 6, label: 'Domingo' },
]

interface AdminScheduleManagerProps {
    adminPasswordProvider: () => Promise<string>
}

export default function AdminScheduleManager({ adminPasswordProvider }: AdminScheduleManagerProps) {
    const [categories, setCategories] = useState<Category[]>([])
    const [selectedCategory, setSelectedCategory] = useState<Category | null>(null)
    const [newCategoryName, setNewCategoryName] = useState('')
    const [newCategoryType, setNewCategoryType] = useState<'specialty' | 'laboratory'>('specialty')

    useEffect(() => {
        fetchSchedules()
    }, [])

    const fetchSchedules = async () => {
        try {
            const response = await api.get('/admin/schedules')
            const data = response.data

            // Transform flat list to grouped structure
            const grouped: Record<string, Category> = {}
            data.forEach((item: any) => {
                if (!grouped[item.name]) {
                    grouped[item.name] = {
                        name: item.name,
                        type: item.category_type,
                        schedules: {}
                    }
                }
                grouped[item.name].schedules[item.day_of_week] = {
                    id: item.id,
                    enabled: true,
                    day_of_week: item.day_of_week,
                    start_time: item.start_time.substring(0, 5),
                    duration: item.turn_duration,
                    max_turns: item.max_turns_per_block,
                    rotation_type: item.rotation_type,
                    rotation_weeks: item.rotation_weeks,
                    start_date: item.start_date,
                    deadline_time: item.deadline_time?.substring(0, 5),
                    warning_message: item.warning_message
                }
            })

            setCategories(Object.values(grouped))
        } catch (error) {
            console.error("Error fetching schedules", error)
        }
    }

    const handleCreateCategory = async () => {
        if (!newCategoryName) return
        try {
            const pass = await adminPasswordProvider()
            await api.post('/admin/categories', {
                admin_password: pass,
                category_type: newCategoryType,
                name: newCategoryName
            })
            fetchSchedules()
            setNewCategoryName('')
        } catch (error) {
            console.error("Failed to create category", error)
        }
    }

    // ... Sub-component for editing specific category would go here

    if (selectedCategory) {
        return (
            <CategoryEditor
                category={selectedCategory}
                onBack={() => {
                    setSelectedCategory(null)
                    fetchSchedules()
                }}
                adminPasswordProvider={adminPasswordProvider}
            />
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex gap-4 items-end premium-card p-4">
                <div className="flex-1">
                    <label className="text-xs font-bold uppercase text-slate-500">Nombre</label>
                    <Input
                        value={newCategoryName}
                        onChange={(e) => setNewCategoryName(e.target.value)}
                        placeholder="Ej. Cardiología"
                    />
                </div>
                <div className="w-40">
                    <label className="text-xs font-bold uppercase text-slate-500">Tipo</label>
                    <select
                        className="w-full h-10 rounded-xl border-slate-200 bg-slate-50 text-sm font-medium"
                        value={newCategoryType}
                        onChange={(e: any) => setNewCategoryType(e.target.value)}
                    >
                        <option value="specialty">Especialidad</option>
                        <option value="laboratory">Laboratorio</option>
                    </select>
                </div>
                <Button onClick={handleCreateCategory}>
                    <Plus size={18} className="mr-2" />
                    Crear
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {categories.map(cat => (
                    <div
                        key={cat.name}
                        onClick={() => setSelectedCategory(cat)}
                        className="premium-card p-6 cursor-pointer hover:border-primary/50 transition-all group"
                    >
                        <div className="flex justify-between items-start">
                            <div>
                                <h3 className="text-xl font-black text-slate-800 group-hover:text-primary transition-colors">{cat.name}</h3>
                                <p className="text-xs font-bold uppercase text-slate-400 mt-1">{cat.type === 'specialty' ? 'Especialidad' : 'Laboratorio'}</p>
                            </div>
                            <div className="h-10 w-10 rounded-full bg-slate-50 flex items-center justify-center text-slate-400 group-hover:bg-primary group-hover:text-white transition-all">
                                <Clock size={20} />
                            </div>
                        </div>
                        <div className="mt-6 flex flex-wrap gap-2">
                            {DAYS.map(day => {
                                const hasSchedule = !!cat.schedules[day.id]
                                return (
                                    <span
                                        key={day.id}
                                        className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${hasSchedule
                                            ? 'bg-emerald-100 text-emerald-700'
                                            : 'bg-slate-50 text-slate-300'
                                            }`}
                                        title={day.label}
                                    >
                                        {day.label[0]}
                                    </span>
                                )
                            })}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

function CategoryEditor({ category, onBack, adminPasswordProvider }: { category: Category, onBack: () => void, adminPasswordProvider: () => Promise<string> }) {
    const [editedCategory, setEditedCategory] = useState<Category>(JSON.parse(JSON.stringify(category)))
    const [isSaving, setIsSaving] = useState(false)
    const isLaboratory = category.type === 'laboratory'

    const updateDay = (dayId: number, changes: Partial<DaySchedule>) => {
        setEditedCategory(prev => {
            const next = { ...prev }
            // Default values based on category type
            const defaultMaxTurns = isLaboratory ? 10 : 1
            const defaultDeadline = isLaboratory ? '09:00' : undefined
            const defaultWarning = isLaboratory ? '⚠️ IMPORTANTE: No recibimos muestras después de las 9:00 AM. Debe presentarse a las 7:30 AM.' : undefined
            
            const current = next.schedules[dayId] || {
                enabled: false,
                day_of_week: dayId,
                start_time: '08:00',
                duration: 30,
                max_turns: defaultMaxTurns,
                rotation_type: 'fixed',
                rotation_weeks: 1,
                start_date: new Date().toISOString().split('T')[0],
                deadline_time: defaultDeadline,
                warning_message: defaultWarning
            }
            // If we are enabling, ensure object exists. If disabling, we keep it but mark enabled=false
            next.schedules[dayId] = { ...current, ...changes }
            if (changes.enabled === true) next.schedules[dayId].enabled = true
            return next
        })
    }

    const handleSave = async () => {
        try {
            const pass = await adminPasswordProvider()
            setIsSaving(true)

            const promises = Object.values(editedCategory.schedules).map(sch => {
                if (!sch.enabled) return Promise.resolve()

                return api.post('/admin/schedules', {
                    admin_password: pass,
                    category_type: category.type,
                    name: category.name,
                    day_of_week: sch.day_of_week,
                    start_time: sch.start_time,
                    turn_duration: sch.duration,
                    max_turns_per_block: sch.max_turns || (isLaboratory ? 10 : 1),
                    rotation_type: sch.rotation_type,
                    rotation_weeks: sch.rotation_weeks,
                    start_date: sch.rotation_type === 'alternated' ? sch.start_date : null,
                    deadline_time: sch.deadline_time || null,
                    warning_message: sch.warning_message || null
                })
            })

            await Promise.all(promises)
            setIsSaving(false)
            onBack()
        } catch (e) {
            console.error(e)
            setIsSaving(false)
            alert("Error al guardar")
        }
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center gap-4">
                <Button variant="outline" onClick={onBack} className="text-sm py-1">
                    <ArrowLeft size={16} className="mr-2" /> Volver
                </Button>
                <h2 className="text-2xl font-black text-slate-800">
                    Editar: <span className="text-primary">{category.name}</span>
                </h2>
                <span className="text-xs font-bold uppercase text-slate-400 bg-slate-100 px-2 py-1 rounded">
                    {category.type === 'specialty' ? 'Especialidad' : 'Laboratorio'}
                </span>
                <div className="flex-1"></div>
                <Button onClick={handleSave} isLoading={isSaving} className="shadow-lg shadow-primary/20">
                    <Save size={18} className="mr-2" />
                    Guardar Cambios
                </Button>
            </div>

            {/* Info banner for laboratory */}
            {isLaboratory && (
                <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-4 flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                        <p className="font-bold text-amber-800">Configuración de Laboratorio</p>
                        <p className="text-sm text-amber-700">
                            Los laboratorios tienen límite de turnos diarios y hora límite de recepción de muestras. 
                            Configure estos parámetros según las necesidades del servicio.
                        </p>
                    </div>
                </div>
            )}

            <div className="grid gap-6">
                {DAYS.map(day => {
                    const defaultMaxTurns = isLaboratory ? 10 : 1
                    const schedule = editedCategory.schedules[day.id] || { 
                        enabled: false, 
                        start_time: '08:00', 
                        duration: 30, 
                        max_turns: defaultMaxTurns,
                        rotation_type: 'fixed', 
                        rotation_weeks: 1, 
                        start_date: new Date().toISOString().split('T')[0],
                        deadline_time: isLaboratory ? '09:00' : undefined,
                        warning_message: isLaboratory ? '⚠️ IMPORTANTE: No recibimos muestras después de las 9:00 AM. Debe presentarse a las 7:30 AM.' : undefined
                    }
                    const isAlternated = schedule.rotation_type === 'alternated'

                    return (
                        <div key={day.id} className={`premium-card p-4 transition-all ${schedule.enabled ? 'border-primary/20 bg-primary/5' : 'opacity-60 grayscale'}`}>
                            <div className="flex flex-col gap-4">
                                <div className="flex items-center gap-3">
                                    <input
                                        type="checkbox"
                                        className="w-5 h-5 rounded border-slate-300 text-primary focus:ring-primary"
                                        checked={schedule.enabled}
                                        onChange={(e) => updateDay(day.id, { enabled: e.target.checked })}
                                    />
                                    <span className="font-bold text-slate-700 min-w-[100px]">{day.label}</span>
                                </div>

                                {schedule.enabled && (
                                    <div className="space-y-4 pl-8">
                                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                                            <div>
                                                <label className="text-[10px] uppercase font-bold text-slate-400">Hora Inicio</label>
                                                <Input
                                                    type="time"
                                                    value={schedule.start_time}
                                                    onChange={(e) => updateDay(day.id, { start_time: e.target.value })}
                                                    className="h-9 text-xs"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-[10px] uppercase font-bold text-slate-400">Duración (min)</label>
                                                <Input
                                                    type="number"
                                                    value={schedule.duration}
                                                    onChange={(e) => updateDay(day.id, { duration: parseInt(e.target.value) })}
                                                    className="h-9 text-xs"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-[10px] uppercase font-bold text-slate-400">Turnos Máx.</label>
                                                <Input
                                                    type="number"
                                                    min={1}
                                                    value={schedule.max_turns || defaultMaxTurns}
                                                    onChange={(e) => updateDay(day.id, { max_turns: parseInt(e.target.value) })}
                                                    className="h-9 text-xs"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-[10px] uppercase font-bold text-slate-400">Rotación</label>
                                                <select
                                                    className="w-full h-9 rounded-xl border-slate-200 bg-white text-xs font-bold text-slate-700"
                                                    value={schedule.rotation_type}
                                                    onChange={(e) => updateDay(day.id, { rotation_type: e.target.value as any })}
                                                >
                                                    <option value="fixed">Semanal (Fijo)</option>
                                                    <option value="alternated">Alternado</option>
                                                </select>
                                            </div>

                                            {/* Alternated Specific Config */}
                                            {isAlternated && (
                                                <>
                                                    <div>
                                                        <label className="text-[10px] uppercase font-bold text-slate-400">Cada (sem)</label>
                                                        <Input
                                                            type="number"
                                                            min={2}
                                                            value={schedule.rotation_weeks}
                                                            onChange={(e) => updateDay(day.id, { rotation_weeks: parseInt(e.target.value) })}
                                                            className="h-9 text-xs"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label className="text-[10px] uppercase font-bold text-slate-400">Desde (Fecha)</label>
                                                        <Input
                                                            type="date"
                                                            value={schedule.start_date || ''}
                                                            onChange={(e) => updateDay(day.id, { start_date: e.target.value })}
                                                            className="h-9 text-xs"
                                                        />
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                        
                                        {/* Laboratory specific fields */}
                                        {isLaboratory && (
                                            <div className="bg-amber-50 rounded-xl p-3 border border-amber-100">
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                                    <div>
                                                        <label className="text-[10px] uppercase font-bold text-amber-700">Hora Límite Muestras</label>
                                                        <Input
                                                            type="time"
                                                            value={schedule.deadline_time || '09:00'}
                                                            onChange={(e) => updateDay(day.id, { deadline_time: e.target.value })}
                                                            className="h-9 text-xs border-amber-200"
                                                        />
                                                    </div>
                                                    <div className="sm:col-span-1">
                                                        <label className="text-[10px] uppercase font-bold text-amber-700">Mensaje de Aviso</label>
                                                        <Input
                                                            type="text"
                                                            value={schedule.warning_message || ''}
                                                            placeholder="Ej: Debe presentarse a las 7:30 AM"
                                                            onChange={(e) => updateDay(day.id, { warning_message: e.target.value })}
                                                            className="h-9 text-xs border-amber-200"
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
