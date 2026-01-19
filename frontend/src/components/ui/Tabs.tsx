import { type ReactNode } from 'react'
import { cn } from '../../lib/utils'

export interface Tab {
  id: string
  label: string
  icon?: ReactNode
}

export interface TabsProps {
  tabs: Tab[]
  activeTab: string
  onTabChange: (tabId: string) => void
  className?: string
}

export default function Tabs({ tabs, activeTab, onTabChange, className }: TabsProps) {
  return (
    <div
      className={cn(
        'relative flex gap-1 rounded-2xl p-1.5 bg-slate-200/50 backdrop-blur-sm border border-white/60 shadow-inner',
        className
      )}
      role="tablist"
    >
      {tabs.map((tab, index) => {
        const isActive = tab.id === activeTab
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              'relative flex-1 rounded-xl px-6 py-3 text-sm font-semibold transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2',
              isActive
                ? 'bg-white text-primary shadow-lg shadow-slate-300/50'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/40',
              isActive && (index === 0 ? 'animate-fade-in-left' : 'animate-fade-in-right')
            )}
            role="tab"
            aria-selected={isActive}
            aria-controls={`tabpanel-${tab.id}`}
            tabIndex={isActive ? 0 : -1}
          >
            <span className="flex items-center justify-center gap-2">
              {tab.icon && <span className="flex-shrink-0">{tab.icon}</span>}
              <span>{tab.label}</span>
            </span>
          </button>
        )
      })}
    </div>
  )
}
