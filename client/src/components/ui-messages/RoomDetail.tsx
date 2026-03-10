import type { RoomData } from "./RoomCard"
import { RoomDetailSkeleton } from "./RoomDetailSkeleton"

function getRoomEmoji(roomType: string): string {
  const lower = roomType.toLowerCase()
  if (lower.includes("sea")) return "🏖️"
  if (lower.includes("garden")) return "🌿"
  if (lower.includes("suite")) return "🌊"
  return "🏠"
}

export function RoomDetail({ room, loading }: { room: RoomData | null; loading?: boolean }) {
  if (loading || !room) {
    return <RoomDetailSkeleton />
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card">
      {/* Image header */}
      <div className="flex h-[200px] items-center justify-center bg-gradient-to-br from-[#2a3a4a] to-[#0f1a2a] text-5xl">
        {getRoomEmoji(room.room_type)}
      </div>

      {/* Body */}
      <div className="p-4">
        <div className="text-xl font-extrabold text-foreground">
          {room.room_name}
        </div>
        <div className="mb-3 text-[13px] text-muted-foreground">
          {room.room_type}
        </div>

        {/* Meta pills */}
        <div className="mb-4 flex flex-wrap gap-2">
          <span className="rounded-lg bg-muted px-3 py-1 text-xs font-medium text-foreground">
            👥 รองรับ {room.max_guests} ท่าน
          </span>
          <span className="rounded-lg bg-muted px-3 py-1 text-xs font-medium text-foreground">
            🛏️ {room.beds}
          </span>
          <span className="rounded-lg bg-muted px-3 py-1 text-xs font-medium text-foreground">
            🚿 {room.baths} ห้องน้ำ
          </span>
          {room.size > 0 && (
            <span className="rounded-lg bg-muted px-3 py-1 text-xs font-medium text-foreground">
              📐 {room.size} ตร.ม.
            </span>
          )}
        </div>

        {/* Price grid */}
        <div className="mb-4 grid grid-cols-3 gap-2">
          <div className="rounded-lg bg-muted p-2.5 text-center">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Weekday
            </div>
            <div className="text-base font-bold text-foreground">
              ฿{room.price_weekdays.toLocaleString()}
            </div>
          </div>
          <div className="rounded-lg bg-muted p-2.5 text-center">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-blue-400">
              Weekend
            </div>
            <div className="text-base font-bold text-blue-400">
              ฿{room.price_weekends_holidays.toLocaleString()}
            </div>
          </div>
          <div className="rounded-lg bg-muted p-2.5 text-center">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-amber-400">
              Holiday
            </div>
            <div className="text-base font-bold text-amber-400">
              ฿{room.price_ny_songkran.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Tags */}
        {room.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {room.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-md bg-blue-500/10 px-2 py-0.5 text-[11px] font-medium text-blue-400"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
