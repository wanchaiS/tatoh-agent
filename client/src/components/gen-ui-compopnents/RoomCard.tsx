import { useState } from "react"
import { CalendarDays } from "lucide-react"

export interface DateRange {
  start: string
  end: string
}

export interface RoomAvailability {
  date_ranges: DateRange[]
  nightly_rates: { weekday: number; weekend: number; holiday: number }
  extra_bed_required: boolean
}

export interface RoomData {
  id: number
  room_name: string
  room_type: string
  summary: string
  bed_queen: number
  bed_single: number
  baths: number
  size: number
  price_weekdays: number
  price_weekends_holidays: number
  price_ny_songkran: number
  max_guests: number
  steps_to_beach: number
  sea_view: number
  privacy: number
  steps_to_restaurant: number
  room_design: number
  room_newness: number
  tags: string[]
  thumbnail_url?: string
  date_ranges?: DateRange[]
}

export function RoomCard({
  room,
  onSelect,
}: {
  room: RoomData
  onSelect?: (room: RoomData) => void
}) {
  const photoSrc = room.thumbnail_url ?? null
  const [imgLoaded, setImgLoaded] = useState(false)
  return (
    <div
      className="rounded-xl overflow-hidden bg-card cursor-pointer group hover:-translate-y-1 transition-all duration-300"
      onClick={() => onSelect?.(room)}
    >
      <div className="h-[190px] overflow-hidden relative">
        {photoSrc ? (
          <>
            {/* shimmer placeholder visible while image fetches */}
            {!imgLoaded && <div className="absolute inset-0 animate-shimmer" />}
            <img
              src={photoSrc}
              alt={room.room_name}
              onLoad={() => setImgLoaded(true)}
              className={`h-full w-full object-cover object-center transition-opacity duration-500 ${imgLoaded ? "opacity-100" : "opacity-0"}`}
            />
          </>
        ) : (
          <div className="h-full w-full animate-shimmer" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none" />
      </div>
      <div className="p-3">
        <div className="font-semibold text-base leading-tight text-foreground">{room.room_name}</div>
        <div className="text-xs text-muted-foreground mt-0.5">{room.room_type}</div>
        <div className="mt-2">
          <span className="text-xs text-muted-foreground">Starting </span>
          <span className="font-bold text-tropical-coral">฿{room.price_weekdays.toLocaleString()}</span>
          <span className="text-xs font-normal text-muted-foreground ml-1">/ night</span>
        </div>
        {room.date_ranges && room.date_ranges.length > 0 && (
          <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <CalendarDays size={12} className="shrink-0 opacity-70" />
            <span className="flex items-center gap-1.5 min-w-0 flex-wrap">
              {room.date_ranges.slice(0, 2).map((d, i) => (
                <span key={i} className="inline-flex items-center gap-1 whitespace-nowrap">
                  {i > 0 && <span className="text-muted-foreground/50">·</span>}
                  <span className="text-foreground/80 font-medium tabular-nums">
                    {formatDatePill(d.start, d.end)}
                  </span>
                  <span className="text-muted-foreground/70 tabular-nums">
                    · {calcNights(d.start, d.end)}n
                  </span>
                </span>
              ))}
              {room.date_ranges.length > 2 && (
                <span className="text-muted-foreground/70 whitespace-nowrap">
                  · +{room.date_ranges.length - 2} more
                </span>
              )}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

function calcNights(start: string, end: string): number {
  const s = new Date(start + "T00:00:00")
  const e = new Date(end + "T00:00:00")
  return Math.round((e.getTime() - s.getTime()) / 86_400_000)
}

function formatDatePill(start: string, end: string): string {
  const s = new Date(start + "T00:00:00")
  const e = new Date(end + "T00:00:00")
  const sMonth = s.toLocaleDateString("en-US", { month: "short" })
  const eMonth = e.toLocaleDateString("en-US", { month: "short" })
  if (sMonth === eMonth) {
    return `${sMonth} ${s.getDate()}-${e.getDate()}`
  }
  return `${sMonth} ${s.getDate()} - ${eMonth} ${e.getDate()}`
}
