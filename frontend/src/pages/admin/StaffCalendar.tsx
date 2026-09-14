import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Filter, X, Download, User as UserIcon, Calendar as CalendarIcon, Clock, AlertCircle } from 'lucide-react'
import api from '../../lib/api'
import Button from '../../components/ui/Button'

// Types
interface Appointment {
    id: number
    patient_id: number
    patient_name?: string
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
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)

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

    // Also fetch categories to populate filter
    const { data: categories = [] } = useQuery({
        queryKey: ['categories'],
        queryFn: async () => {
            const res = await api.get('/admin/schedules')
            return Array.isArray(res.data) ? Array.from(new Set(res.data.map((c: any) => c.name))) : []
        }
    })

    // Calendar Logic
    const generateCalendarDays = () => {
        const startDay = monthStart.getDay()
        const daysInMonth = monthEnd.getDate()

        const prevMonthEnd = new Date(currentDate.getFullYear(), currentDate.getMonth(), 0).getDate()
        const paddingDays = Array.from({ length: startDay }, (_, i) => ({
            day: prevMonthEnd - startDay + i + 1,
            isCurrentMonth: false,
            date: new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, prevMonthEnd - startDay + i + 1)
        }))

        const currentDays = Array.from({ length: daysInMonth }, (_, i) => ({
            day: i + 1,
            isCurrentMonth: true,
            date: new Date(currentDate.getFullYear(), currentDate.getMonth(), i + 1)
        }))

        const totalDisplayed = paddingDays.length + currentDays.length
        const nextPadding = Array.from({ length: 42 - totalDisplayed }, (_, i) => ({
            day: i + 1,
            isCurrentMonth: false,
            date: new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, i + 1)
        }))

        return [...paddingDays, ...currentDays, ...nextPadding]
    }

    const calendarDays = generateCalendarDays()

    const getAppointmentsForDate = (date: Date) => {
        const dateStr = formatLocalYMD(date)
        return appointments.filter(a => a.appointment_date.startsWith(dateStr))
    }

    const navigateMonth = (direction: 'prev' | 'next') => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + (direction === 'next' ? 1 : -1), 1))
    }

    const formatTime = (isoString: string) => {
        const timePart = isoString.split('T')[1] || '00:00:00'
        const [hours, minutes] = timePart.split(':').map(Number)
        const date = new Date()
        date.setHours(hours, minutes, 0, 0)
        return date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
    }

    const getInitials = (specialty: string) => {
        if (specialty.toLowerCase().includes('laboratorio')) return 'L'
        return specialty.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'cancelled': return 'bg-red-500 text-white'
            case 'confirmed': return 'bg-emerald-500 text-white'
            case 'completed': return 'bg-indigo-500 text-white'
            default: return 'bg-blue-500 text-white'
        }
    }

    const handleDownload = async (appointmentId: number) => {
        try {
            const response = await api.get(`/appointments/${appointmentId}/export`, {
                responseType: 'blob'
            })
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `paciente_info_${appointmentId}.xlsx`)
            document.body.appendChild(link)
            link.click()
            link.remove()
        } catch (error) {
            console.error('Error downloading file:', error)
            alert('Error al descargar la información')
        }
    }

    return (
        <div className="space-y-8 pb-20 relative">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-1">
                    <h1 className="text-4xl font-black tracking-tight text-slate-900">
                        Calendario <span className="text-primary">Staff</span>
                    </h1>
                    <p className="text-slate-500 font-medium">Gestión visual de turnos y disponibilidad.</p>
                </div>

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
                <div className="grid grid-cols-7 border-b border-slate-100">
                    {DAYS.map(day => (
                        <div key={day} className="py-4 text-center text-xs font-black text-slate-400 tracking-widest bg-slate-50/50">
                            {day}
                        </div>
                    ))}
                </div>

                <div className="grid grid-cols-7">
                    {calendarDays.map((dayObj, idx) => {
                        const dayAppointments = getAppointmentsForDate(dayObj.date)
                        const isToday = dayObj.date.toDateString() === new Date().toDateString()

                        return (
                            <div
                                key={idx}
                                className={`
                                    min-h-[120px] p-2 border-b border-r border-slate-50 transition-colors hover:bg-slate-50/30
                                    ${!dayObj.isCurrentMonth ? 'bg-slate-50/80' : ''}
                                `}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <span className={`
                                        text-xs font-bold w-6 h-6 flex items-center justify-center rounded-full
                                        ${isToday ? 'bg-primary text-white' : 'text-slate-500'}
                                        ${!dayObj.isCurrentMonth ? 'opacity-30' : ''}
                                    `}>
                                        {dayObj.day}
                                    </span>
                                </div>

                                <div className="flex flex-wrap gap-1">
                                    {dayAppointments.map(apt => (
                                        <button
                                            key={apt.id}
                                            onClick={() => setSelectedAppointment(apt)}
                                            title={`${apt.specialty} - ${formatTime(apt.appointment_date)}`}
                                            className={`
                                                w-7 h-7 flex items-center justify-center rounded-lg text-[10px] font-black shadow-sm
                                                transition-transform hover:scale-110 active:scale-95
                                                ${getStatusColor(apt.status)}
                                                ${apt.status === 'cancelled' ? 'opacity-50' : ''}
                                            `}
                                        >
                                            {getInitials(apt.specialty)}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* Appointment Detail Modal */}
            {selectedAppointment && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
                    <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md overflow-hidden animate-scale-in">
                        {/* Modal Header */}
                        <div className={`p-6 text-white flex justify-between items-start ${getStatusColor(selectedAppointment.status)}`}>
                            <div className="space-y-1">
                                <p className="text-[10px] font-black uppercase tracking-widest opacity-80">Detalle del Turno</p>
                                <h3 className="text-2xl font-black tracking-tight">{selectedAppointment.specialty}</h3>
                            </div>
                            <button
                                onClick={() => setSelectedAppointment(null)}
                                className="p-2 hover:bg-white/20 rounded-xl transition-colors"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-8 space-y-6">
                            <div className="space-y-4">
                                <div className="flex items-center gap-4 p-3 bg-slate-50 rounded-2xl">
                                    <div className="h-10 w-10 rounded-xl bg-white shadow-sm flex items-center justify-center text-primary">
                                        <UserIcon size={20} />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Paciente</p>
                                        <p className="font-bold text-slate-900">{selectedAppointment.patient_name || 'Cargando...'}</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl">
                                        <CalendarIcon size={18} className="text-slate-400" />
                                        <div>
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Fecha</p>
                                            <p className="text-xs font-bold text-slate-900">{new Date(selectedAppointment.appointment_date).toLocaleDateString('es-AR')}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl">
                                        <Clock size={18} className="text-slate-400" />
                                        <div>
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Hora</p>
                                            <p className="text-xs font-bold text-slate-900">{formatTime(selectedAppointment.appointment_date)}</p>
                                        </div>
                                    </div>
                                </div>

                                {selectedAppointment.notes && (
                                    <div className="p-4 bg-blue-50 border border-blue-100 rounded-2xl flex gap-3">
                                        <AlertCircle size={18} className="text-blue-500 flex-shrink-0" />
                                        <p className="text-xs text-blue-700 font-medium">{selectedAppointment.notes}</p>
                                    </div>
                                )}
                            </div>

                            <div className="pt-2">
                                <Button
                                    className="w-full flex items-center justify-center gap-2"
                                    onClick={() => handleDownload(selectedAppointment.id)}
                                >
                                    <Download size={18} />
                                    Descargar Historial Clínico
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {isLoading && (
                <div className="absolute inset-0 bg-white/50 backdrop-blur-sm flex items-center justify-center z-10">
                    <div className="h-12 w-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                </div>
            )}
        </div>
    )
}
