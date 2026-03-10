import { RoomCard, type RoomData } from "./RoomCard"
import { RoomCardSkeleton } from "./RoomCardSkeleton"

export function RoomsList({ rooms, loading }: { rooms: RoomData[]; loading?: boolean }) {
  return (
    <div className="flex gap-2.5 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-2 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-border">
      {loading
        ? Array.from({ length: 3 }).map((_, i) => <RoomCardSkeleton key={i} />)
        : rooms.map((room) => (
            <div key={room.room_name} className="animate-in fade-in duration-300">
              <RoomCard room={room} />
            </div>
          ))}
    </div>
  )
}
