import { Button } from '@/components/ui/button'
import { roomsQueryOptions } from '@/hooks/useRooms'
import { useSuspenseQuery } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { Plus } from 'lucide-react'

export function RoomsPane() {
  const navigate = useNavigate()
  const { data: rooms } = useSuspenseQuery(roomsQueryOptions())

  return (
    <div className="flex-1 p-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="w-1 h-8 rounded-full" style={{ backgroundColor: 'var(--tropical-coral)' }}></div>
          <h1 className="text-3xl font-bold">Rooms</h1>
        </div>
        <Button
          onClick={() => navigate({ to: '/knowledge/rooms/new' })}
          className="gap-2"
          style={{
            backgroundColor: 'var(--tropical-coral)',
            color: 'white',
          }}
        >
          <Plus className="h-4 w-4" />
          Add Room
        </Button>
      </div>

      {/* Rooms table */}
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-muted border-b">
              <th className="px-6 py-3 text-left text-sm font-semibold">Room</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Type</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Guests</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Price (฿)</th>
            </tr>
          </thead>
          <tbody>
            {rooms.map((room, index) => (
              <tr
                key={room.id}
                className="border-b cursor-pointer transition-colors animate-in fade-in slide-in-from-bottom-2 duration-300"
                style={{
                  '--hover-bg': 'oklch(0.97 0.02 63.4 / 0.4)',
                  animationDelay: `${index * 40}ms`,
                  animationFillMode: 'both',
                } as React.CSSProperties}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--hover-bg)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }}
                onClick={() => navigate({ to: `/knowledge/rooms/${room.id}` })}
              >
                <td className="px-6 py-4 font-medium flex items-center gap-2">
                  <div className="w-1 h-6 rounded-full" style={{ backgroundColor: 'var(--tropical-coral)' }}></div>
                  {room.room_name}
                </td>
                <td className="px-6 py-4 text-muted-foreground">{room.room_type}</td>
                <td className="px-6 py-4">{room.max_guests}</td>
                <td className="px-6 py-4 text-sm">
                  <div className="font-medium">
                    ฿{Math.min(room.price_weekdays, room.price_weekends_holidays, room.price_ny_songkran).toLocaleString()}–{Math.max(room.price_weekdays, room.price_weekends_holidays, room.price_ny_songkran).toLocaleString()}
                  </div>
                  <div className="text-xs text-muted-foreground">per night</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {rooms.length === 0 && (
          <div className="p-8 text-center text-muted-foreground">
            No rooms yet. Create one to get started.
          </div>
        )}
      </div>
    </div>
  )
}
