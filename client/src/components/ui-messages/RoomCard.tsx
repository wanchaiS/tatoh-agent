import { useState } from "react"

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
        <div className="text-xs text-muted-foreground mt-1">
          {room.max_guests} guests
          {room.bed_queen > 0 ? ` · ${room.bed_queen}Q` : ""}
          {room.bed_single > 0 ? ` ${room.bed_single}S` : ""}
        </div>
        <div className="mt-2">
          <span className="text-xs text-muted-foreground">Starting </span>
          <span className="font-bold text-tropical-coral">฿{room.price_weekdays.toLocaleString()}</span>
          <span className="text-xs font-normal text-muted-foreground ml-1">/ night</span>
        </div>
      </div>
    </div>
  )
}
