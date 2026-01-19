import { type ReactNode } from 'react'
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'error'
  children: ReactNode
  className?: string
}

const variantConfig = {
  info: {
    icon: Info,
    bgClass: 'bg-blue-50/80 border-blue-200/50',
    textClass: 'text-blue-800',
    iconClass: 'text-blue-600',
  },
  success: {
    icon: CheckCircle,
    bgClass: 'bg-emerald-50/80 border-emerald-200/50',
    textClass: 'text-emerald-800',
    iconClass: 'text-emerald-600',
  },
  warning: {
    icon: AlertCircle,
    bgClass: 'bg-amber-50/80 border-amber-200/50',
    textClass: 'text-amber-800',
    iconClass: 'text-amber-600',
  },
  error: {
    icon: XCircle,
    bgClass: 'bg-red-50/80 border-red-200/50',
    textClass: 'text-red-800',
    iconClass: 'text-red-600',
  },
}

export default function Alert({ variant = 'info', children, className }: AlertProps) {
  const config = variantConfig[variant]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm shadow-lg transition-all duration-300 animate-fade-in-scale',
        config.bgClass,
        config.textClass,
        className
      )}
      role="alert"
    >
      <Icon className={cn('h-5 w-5 mt-0.5 flex-shrink-0', config.iconClass)} />
      <div className="flex-1 text-sm font-medium">{children}</div>
    </div>
  )
}
