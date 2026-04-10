import { useState } from "react"
import type { RoomData } from "@/components/gen-ui-compopnents/RoomCard"
import { useListPhotos } from "@/hooks/usePhotos"

interface RoomCardCompactProps {
  room: RoomData
  onSelect: (room: RoomData) => void
  isSelected?: boolean
}

export function RoomCardCompact({ room, onSelect, isSelected }: RoomCardCompactProps) {
  const [imgLoaded, setImgLoaded] = useState(false)
  const { data: photos } = useListPhotos(room.id)
  const photoSrc = photos?.[0]?.thumbnail_url ?? photos?.[0]?.url ?? room.thumbnail_url ?? null

  return (
    <div
      onClick={() => onSelect(room)}
      className={`w-[200px] shrink-0 rounded-xl overflow-hidden bg-card cursor-pointer transition-all duration-300 hover:-translate-y-0.5 ${
        isSelected
          ? "ring-2 ring-tropical-coral shadow-lg"
          : "border border-border/50 hover:border-border hover:shadow-md"
      }`}
    >
      {/* Photo */}
      <div className="h-[130px] overflow-hidden relative">
        {photoSrc ? (
          <>
            {!imgLoaded && <div className="absolute inset-0 animate-shimmer" />}
            <img
              src={photoSrc}
              alt={room.room_name}
              onLoad={() => setImgLoaded(true)}
              className={`h-full w-full object-cover transition-all duration-500 ${imgLoaded ? "opacity-100" : "opacity-0"}`}
            />
          </>
        ) : (
          <div className="h-full w-full animate-shimmer" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent pointer-events-none" />
        {/* Price badge */}
        <div className="absolute bottom-2 left-2 rounded-lg bg-white/90 backdrop-blur-sm px-2 py-0.5 shadow-sm">
          <span className="font-bold text-sm text-tropical-coral">฿{room.price_weekdays.toLocaleString()}</span>
          <span className="text-[10px] text-muted-foreground">/night</span>
        </div>
      </div>

      {/* Info */}
      <div className="p-2.5">
        <h3 className="font-semibold text-sm text-foreground leading-tight truncate">{room.room_name}</h3>
        <p className="text-[11px] text-muted-foreground mt-0.5">{room.room_type}</p>
        <div className="flex gap-1 mt-1.5">
          {room.sea_view >= 7 && (
            <span className="rounded-full bg-tropical-ocean/10 text-tropical-ocean px-1.5 py-0.5 text-[9px] font-medium">Sea view</span>
          )}
          <span className="rounded-full bg-muted text-muted-foreground px-1.5 py-0.5 text-[9px] font-medium">
            {room.max_guests}p · {room.size}m²
          </span>
        </div>
      </div>
    </div>
  )
}
