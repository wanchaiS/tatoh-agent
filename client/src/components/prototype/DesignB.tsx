import { useState, useRef, useEffect } from "react"
import type { RoomData } from "@/components/gen-ui-compopnents/RoomCard"
import { RoomCardCompact } from "./RoomCardCompact"
import { RoomDetailView } from "./RoomDetailView"
import { ResortMap } from "./ResortMap"
import { MAP_SMALL } from "./mockData"

interface DesignBProps {
  rooms: RoomData[]
}

export function DesignB({ rooms }: DesignBProps) {
  const [selectedRoom, setSelectedRoom] = useState<RoomData | null>(null)
  const [detailRoom, setDetailRoom] = useState<RoomData | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  function handleSelectCard(room: RoomData) {
    setSelectedRoom(room)
  }

  function handleMapPin(room: RoomData) {
    setSelectedRoom(room)
    // Scroll card strip to show this room
    const idx = rooms.findIndex(r => r.id === room.id)
    if (idx >= 0 && scrollRef.current) {
      const card = scrollRef.current.children[idx] as HTMLElement
      card?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" })
    }
  }

  function handleViewDetails() {
    if (selectedRoom) setDetailRoom(selectedRoom)
  }

  // Auto-scroll to selected card
  useEffect(() => {
    if (!selectedRoom || !scrollRef.current) return
    const idx = rooms.findIndex(r => r.id === selectedRoom.id)
    if (idx >= 0) {
      const card = scrollRef.current.children[idx] as HTMLElement
      card?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" })
    }
  }, [selectedRoom, rooms])

  if (detailRoom) {
    return (
      <RoomDetailView
        room={detailRoom}
        allRooms={rooms}
        onBack={() => setDetailRoom(null)}
      />
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-baseline gap-2">
        <span className="font-bold text-lg text-foreground">{rooms.length}</span>
        <span className="font-semibold text-base text-foreground">rooms available</span>
      </div>

      {/* Horizontal card strip */}
      <div className="relative">
        <div ref={scrollRef} className="flex gap-2.5 overflow-x-auto pb-2 snap-x snap-mandatory scrollbar-hide">
          {rooms.map((room, i) => (
            <div key={room.id} className="snap-start animate-card-enter" style={{ animationDelay: `${i * 60}ms` }}>
              <RoomCardCompact
                room={room}
                onSelect={handleSelectCard}
                isSelected={selectedRoom?.id === room.id}
              />
            </div>
          ))}
        </div>
        <div className="pointer-events-none absolute right-0 top-0 bottom-2 w-4 bg-gradient-to-l from-chat-bg to-transparent z-10" />
      </div>

      {/* Persistent mini map */}
      <ResortMap
        rooms={rooms}
        mapSrc={MAP_SMALL}
        selectedRoomId={selectedRoom?.id}
        onSelectRoom={handleMapPin}
        compact
      />

      {/* Selected room action */}
      {selectedRoom && (
        <div className="flex items-center justify-between rounded-xl border border-border bg-card p-3 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="min-w-0">
            <p className="font-semibold text-sm text-foreground truncate">{selectedRoom.room_name}</p>
            <p className="text-xs text-muted-foreground">{selectedRoom.room_type} · ฿{selectedRoom.price_weekdays.toLocaleString()}/night</p>
          </div>
          <button
            onClick={handleViewDetails}
            className="shrink-0 rounded-lg bg-tropical-coral px-4 py-2 text-sm font-semibold text-white hover:opacity-90 transition-opacity cursor-pointer"
          >
            View Details
          </button>
        </div>
      )}
    </div>
  )
}
