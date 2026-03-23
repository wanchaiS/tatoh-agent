import { useState } from "react"
import { RoomCard, type RoomData } from "./RoomCard"
import { RoomCardSkeleton } from "./RoomCardSkeleton"
import { RoomCardFocusView } from "./RoomFocusView"

export function SearchResultsList({
  rooms,
  loading,
  label,
}: {
  rooms: RoomData[]
  loading?: boolean
  label?: string
}) {
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null)

  if (focusedIndex !== null && rooms[focusedIndex]) {
    return (
      <RoomCardFocusView
        room={rooms[focusedIndex]}
        hasPrev={focusedIndex > 0}
        hasNext={focusedIndex < rooms.length - 1}
        prevRoomName={focusedIndex > 0 ? rooms[focusedIndex - 1].room_name : undefined}
        nextRoomName={focusedIndex < rooms.length - 1 ? rooms[focusedIndex + 1].room_name : undefined}
        onPrev={() => setFocusedIndex((i) => Math.max(0, (i ?? 0) - 1))}
        onNext={() => setFocusedIndex((i) => Math.min(rooms.length - 1, (i ?? 0) + 1))}
        onBack={() => setFocusedIndex(null)}
      />
    )
  }

  if (loading) {
    return (
      <div className="w-full">
        <div className="overflow-hidden rounded"><div className="h-5 w-32 mb-2.5 rounded bg-muted animate-shimmer" /></div>
        <div className="overflow-x-auto flex gap-3 pb-2">
          <div className="w-[250px] shrink-0 snap-start"><RoomCardSkeleton /></div>
          <div className="w-[250px] shrink-0 snap-start"><RoomCardSkeleton /></div>
        </div>
      </div>
    )
  }

  if (rooms.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-muted/30 px-4 py-6 text-center text-sm text-muted-foreground">
        No rooms match your dates
      </div>
    )
  }

  return (
    <div className="w-full">
      {label && (
        <div className="text-xs font-medium text-muted-foreground mb-1 px-0.5">{label}</div>
      )}
      <div className="flex items-baseline gap-2 mb-2.5 px-0.5">
        <span className="font-bold text-lg text-foreground">{rooms.length}</span>
        <span className="font-semibold text-base text-foreground">{rooms.length === 1 ? "room" : "rooms"} available</span>
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
