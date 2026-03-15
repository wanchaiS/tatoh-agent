import { useState } from "react"
import { RoomCard, type RoomData } from "./RoomCard"
import { RoomCardSkeleton } from "./RoomCardSkeleton"
import { RoomFocusView } from "./RoomFocusView"

export function RoomsList({
  rooms,
  loading,
  onAskAI,
}: {
  rooms: RoomData[]
  loading?: boolean
  onAskAI?: (room: RoomData) => void
}) {
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null)

  if (focusedIndex !== null && rooms[focusedIndex]) {
    return (
      <RoomFocusView
        room={rooms[focusedIndex]}
        hasPrev={focusedIndex > 0}
        hasNext={focusedIndex < rooms.length - 1}
        prevRoomName={focusedIndex > 0 ? rooms[focusedIndex - 1].room_name : undefined}
        nextRoomName={focusedIndex < rooms.length - 1 ? rooms[focusedIndex + 1].room_name : undefined}
        onPrev={() => setFocusedIndex((i) => Math.max(0, (i ?? 0) - 1))}
        onNext={() => setFocusedIndex((i) => Math.min(rooms.length - 1, (i ?? 0) + 1))}
        onBack={() => setFocusedIndex(null)}
        onAskAI={(room) => {
          setFocusedIndex(null)
          onAskAI?.(room)
        }}
      />
    )
  }

  if (loading) {
    return (
      <div className="w-full">
        <div className="overflow-hidden rounded"><div className="h-5 w-24 mb-2.5 rounded bg-muted animate-shimmer" /></div>
        <div className="overflow-x-auto flex gap-3 pb-2">
          <div className="w-[250px] shrink-0 snap-start"><RoomCardSkeleton /></div>
          <div className="w-[250px] shrink-0 snap-start"><RoomCardSkeleton /></div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="flex items-baseline gap-2 mb-2.5 px-0.5">
        <span className="font-bold text-lg text-foreground">{rooms.length}</span>
        <span className="font-semibold text-base text-foreground">{rooms.length === 1 ? "Room" : "Rooms"}</span>
        <span className="text-xs text-muted-foreground">— select to view more details</span>
      </div>
      <div className="relative">
        <div
          className="overflow-x-auto flex gap-3 pb-2 snap-x snap-mandatory"
        >
          {rooms.map((room, i) => (
            <div
              key={room.room_name}
              className="w-[250px] shrink-0 snap-start animate-card-enter"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <RoomCard room={room} onSelect={() => setFocusedIndex(i)} />
            </div>
          ))}
        </div>
        <div className="pointer-events-none absolute right-0 top-0 bottom-2 w-2 bg-gradient-to-l from-chat-bg to-transparent z-10" />
      </div>
    </div>
  )
}
