import { type ReactNode, useState } from 'react'
import { cn } from '../../lib/utils'

export interface Tab {
  id: string
  label: string
  icon?: ReactNode
}

export interface TabsProps {
  tabs: Tab[]
  defaultTab?: string
  onTabChange?: (tabId: string) => void
  children: (activeTab: string) => ReactNode
  className?: string
}

export default function Tabs({ tabs, defaultTab, onTabChange, children, className }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id || '')

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId)
    onTabChange?.(tabId)
  }

  const activeIndex = tabs.findIndex(tab => tab.id === activeTab)

  return (
    <div className={cn('w-full', className)}>
      {/* Tab Headers */}
      <div className="relative mb-6">
        <div className="glass rounded-xl p-1.5 shadow-lg">
          <div className="grid grid-cols-2 gap-1.5 relative">
            {/* Sliding Background Indicator */}
            <div
              className="absolute inset-y-1.5 bg-primary rounded-lg shadow-lg transition-all duration-300 ease-out"
              style={{
                width: `calc(50% - 0.375rem)`,
                transform: `translateX(calc(${activeIndex * 100}% + ${activeIndex * 0.375}rem))`,
              }}
            />
            
            {/* Tab Buttons */}
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={cn(
                  'relative z-10 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-semibold text-sm transition-all duration-300',
                  activeTab === tab.id
                    ? 'text-white'
                    : 'text-slate-600 hover:text-slate-800'
                )}
                type="button"
              >
                {tab.icon && <span className="text-lg">{tab.icon}</span>}
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content with Animation */}
      <div className="relative">
        <div
          key={activeTab}
          className="animate-fade-in-up"
        >
          {children(activeTab)}
        </div>
      </div>
    </div>
  )
}
