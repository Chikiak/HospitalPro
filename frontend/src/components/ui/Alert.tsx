import { forwardRef, type HTMLAttributes } from 'react'
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'error' | 'success' | 'warning' | 'info'
  onClose?: () => void
}

const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'info', onClose, children, ...props }, ref) => {
    const variantStyles = {
      error: 'bg-red-50/80 border-red-200/60 text-red-800 backdrop-blur-sm',
      success: 'bg-emerald-50/80 border-emerald-200/60 text-emerald-800 backdrop-blur-sm',
      warning: 'bg-amber-50/80 border-amber-200/60 text-amber-800 backdrop-blur-sm',
      info: 'bg-blue-50/80 border-blue-200/60 text-blue-800 backdrop-blur-sm'
    }

    const icons = {
      error: <XCircle className="h-5 w-5 flex-shrink-0" />,
      success: <CheckCircle className="h-5 w-5 flex-shrink-0" />,
      warning: <AlertCircle className="h-5 w-5 flex-shrink-0" />,
      info: <Info className="h-5 w-5 flex-shrink-0" />
    }

    return (
      <div
        ref={ref}
        className={cn(
          'relative flex items-start gap-3 rounded-xl border px-4 py-3.5 shadow-lg transition-all duration-300 animate-fade-in-scale',
          variantStyles[variant],
          className
        )}
        role="alert"
        {...props}
      >
        <div className="mt-0.5">{icons[variant]}</div>
        <div className="flex-1 text-sm font-medium leading-relaxed">{children}</div>
        {onClose && (
          <button
            onClick={onClose}
            className="flex-shrink-0 rounded-lg p-1 transition-colors hover:bg-black/5"
            aria-label="Cerrar alerta"
          >
            <XCircle className="h-4 w-4" />
          </button>
        )}
      </div>
    )
  }
)

Alert.displayName = 'Alert'

export default Alert
