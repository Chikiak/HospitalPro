import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Filter } from 'lucide-react'
import api from '../../lib/api'

// Types
interface Appointment {
    id: number
    patient_id: number
    appointment_date: string
    status: 'scheduled' | 'confirmed' | 'cancelled' | 'completed'
    specialty: string
    notes?: string
}

const DAYS = ['DOM', 'LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB']
const MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

export default function StaffCalendar() {
    const [currentDate, setCurrentDate] = useState(new Date())
    const [selectedSpecialty, setSelectedSpecialty] = useState<string>('')

    // Helper to get start/end of month
    const monthStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1)
    const monthEnd = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0)

    // Helper for consistent date formatting (Local YYYY-MM-DD)
    const formatLocalYMD = (date: Date) => {
        const offset = date.getTimezoneOffset()
        const localDate = new Date(date.getTime() - (offset * 60 * 1000))
        return localDate.toISOString().split('T')[0]
    }

    // Fetch appointments
    const { data: appointments = [], isLoading } = useQuery<Appointment[]>({
        queryKey: ['appointments-all', currentDate.getMonth(), currentDate.getFullYear(), selectedSpecialty],
        queryFn: async () => {
            const startStr = formatLocalYMD(monthStart)
            const endStr = formatLocalYMD(monthEnd)

            const params: any = {
                start_date: startStr,
                end_date: endStr
            }
            if (selectedSpecialty) params.specialty = selectedSpecialty

            const response = await api.get('/appointments/all', { params })
            return Array.isArray(response.data) ? response.data : []
        }
    })

    // Also fetch categories to populate filter even if no appointments exist
    const { data: categories = [] } = useQuery({
        queryKey: ['categories'],
        queryFn: async () => {
            const res = await api.get('/admin/schedules')
            return Array.isArray(res.data) ? Array.from(new Set(res.data.map((c: any) => c.name))) : []
        }
    })

    // Calendar Logic
    const generateCalendarDays = () => {
        const startDay = monthStart.getDay() // 0-6
        const daysInMonth = monthEnd.getDate()

        // Previous month padding
        const prevMonthEnd = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0).getDate()
        const paddingDays = Array.from({ length: startDay }, (_, i) => ({
            day: prevMonthEnd - startDay + i + 1,
            isCurrentMonth: false,
            date: new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, prevMonthEnd - startDay + i + 1)
        }))

        // Current month days
        const currentDays = Array.from({ length: daysInMonth }, (_, i) => ({
            day: i + 1,
            isCurrentMonth: true,
            date: new Date(currentDate.getFullYear(), currentDate.getMonth(), i + 1)
        }))

        // Next month padding to fill 42 grid (6 rows)
        const totalDisplayed = paddingDays.length + currentDays.length
        const nextPadding = Array.from({ length: 42 - totalDisplayed }, (_, i) => ({
            day: i + 1,
            isCurrentMonth: false,
            date: new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, i + 1)
        }))

        return [...paddingDays, ...currentDays, ...nextPadding]
    }

    const calendarDays = generateCalendarDays()

    // Map appointments to days
    const getAppointmentsForDate = (date: Date) => {
        const dateStr = formatLocalYMD(date)
        return appointments.filter(a => a.appointment_date.startsWith(dateStr))
    }

    const navigateMonth = (direction: 'prev' | 'next') => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + (direction === 'next' ? 1 : -1), 1))
    }

    const formatTime = (isoString: string) => {
        // Parse as local time by extracting time components
        const timePart = isoString.split('T')[1] || '00:00:00'
        const [hours, minutes] = timePart.split(':').map(Number)
        const date = new Date()
        date.setHours(hours, minutes, 0, 0)
        return date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
    }

    return (
        <div className="space-y-8 pb-20">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-1">
                    <h1 className="text-4xl font-black tracking-tight text-slate-900">
                        Calendario <span className="text-primary">Staff</span>
                    </h1>
                    <p className="text-slate-500 font-medium">Gestión visual de turnos y disponibilidad.</p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-4">
                    <div className="relative group">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Filter className="h-4 w-4 text-slate-400 group-hover:text-primary transition-colors" />
                        </div>
                        <select
                            value={selectedSpecialty}
                            onChange={(e) => setSelectedSpecialty(e.target.value)}
                            className="pl-10 pr-4 py-2 bg-white border-2 border-slate-200 rounded-xl text-sm font-bold text-slate-700 outline-none focus:border-primary transition-all appearance-none cursor-pointer hover:border-primary/50"
                        >
                            <option value="">Todas las Especialidades</option>
                            {categories.map((cat: string) => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center bg-white border-2 border-slate-200 rounded-xl p-1">
                        <button onClick={() => navigateMonth('prev')} className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors">
                            <ChevronLeft size={20} />
                        </button>
                        <div className="px-4 font-black text-slate-800 min-w-[140px] text-center capitalize">
                            {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
                        </div>
                        <button onClick={() => navigateMonth('next')} className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors">
                            <ChevronRight size={20} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Calendar Grid */}
            <div className="premium-card !p-0 overflow-hidden bg-white shadow-xl">
                {/* Day Headers */}
                <div className="grid grid-cols-7 border-b border-slate-100">
                    {DAYS.map(day => (
                        <div key={day} className="py-4 text-center text-xs font-black text-slate-400 tracking-widest bg-slate-50/50">
                            {day}
                        </div>
                    ))}
                </div>

                {/* Days */}
                <div className="grid grid-cols-7">
                    {calendarDays.map((dayObj, idx) => {
                        const dayAppointments = getAppointmentsForDate(dayObj.date)
                        const isToday = dayObj.date.toDateString() === new Date().toDateString()

                        return (
                            <div
                                key={idx}
                                className={`
                            min-h-[140px] p-2 border-b border-r border-slate-50 transition-colors hover:bg-slate-50/30
                            ${!dayObj.isCurrentMonth ? 'bg-slate-50/80' : ''}
                        `}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <span className={`
                                  text-sm font-bold w-7 h-7 flex items-center justify-center rounded-full
                                  ${isToday ? 'bg-primary text-white shadow-lg shadow-primary/30' : 'text-slate-700'}
                                  ${!dayObj.isCurrentMonth ? 'text-slate-400' : ''}
                              `}>
                                        {dayObj.day}
                                    </span>
                                    {dayAppointments.length > 0 && (
                                        <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
                                            {dayAppointments.length}
                                        </span>
                                    )}
                                </div>

                                <div className="space-y-1.5">
                                    {dayAppointments.slice(0, 4).map(apt => (
                                        <div
                                            key={apt.id}
                                            title={`${apt.specialty} - ${formatTime(apt.appointment_date)}`}
                                            className={`
                                        text-[10px] px-2 py-1 rounded-md font-bold truncate cursor-help transition-all border-l-2
                                        ${apt.status === 'cancelled' ? 'bg-red-50 text-red-700 border-red-500 opacity-60 line-through' :
                                                    apt.status === 'confirmed' ? 'bg-emerald-50 text-emerald-700 border-emerald-500' :
                                                        'bg-blue-50 text-blue-700 border-blue-500'}
                                    `}
                                        >
                                            {formatTime(apt.appointment_date)} {apt.specialty === selectedSpecialty ? '' : apt.specialty}
                                        </div>
                                    ))}
                                    {dayAppointments.length > 4 && (
                                        <div className="text-[10px] text-center text-slate-400 font-bold hover:text-primary cursor-pointer">
                                            + {dayAppointments.length - 4} más
                                        </div>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {isLoading && (
                <div className="absolute inset-0 bg-white/50 backdrop-blur-sm flex items-center justify-center z-10">
                    <div className="h-12 w-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                </div>
            )}
        </div>
    )
}
