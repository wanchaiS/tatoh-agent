import { Link } from '@tanstack/react-router'
import { BedDouble, Waves, Bus } from 'lucide-react'
import { useLocation } from '@tanstack/react-router'

export function KnowledgeNav() {
  const location = useLocation()

  const navItems = [
    {
      icon: BedDouble,
      label: 'Rooms',
      to: '/knowledge/rooms' as const,
    },
    {
      icon: Waves,
      label: 'Boat Schedules',
      to: '/knowledge/boat-schedules' as const,
    },
    {
      icon: Bus,
      label: 'Bus Schedules',
      to: '/knowledge/bus-schedules' as const,
    },
  ]

  const isActive = (to: string) => {
    const path = location.pathname
    return path === to || (to === '/knowledge/rooms' && path.startsWith('/knowledge/rooms'))
  }

  return (
    <nav className="w-48 border-r bg-muted/30 flex flex-col">
      {/* Header */}
      <div className="border-b px-4 py-4">
        <h1 className="text-sm font-semibold">Knowledge Base</h1>
        <p className="text-xs text-muted-foreground mt-1">Agent Resources</p>
      </div>

      {/* Navigation items */}
      <div className="flex-1 p-2 space-y-1 overflow-auto">
        {navItems.map(({ icon: Icon, label, to }) => (
          <Link
            key={to}
            to={to}
            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              isActive(to)
                ? 'bg-primary text-primary-foreground'
                : 'text-foreground hover:bg-muted'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </div>
    </nav>
  )
}
