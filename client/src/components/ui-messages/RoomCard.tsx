export interface RoomData {
  room_name: string
  room_type: string
  summary: string
  beds: string
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
}

function getRoomEmoji(roomType: string): string {
  const lower = roomType.toLowerCase()
  if (lower.includes("sea")) return "🏖️"
  if (lower.includes("garden")) return "🌿"
  if (lower.includes("suite")) return "🌊"
  return "🏠"
}

export function RoomCard({ room }: { room: RoomData }) {
  return (
    <div className="relative h-[280px] w-[200px] flex-shrink-0 cursor-pointer overflow-hidden rounded-2xl transition-transform hover:-translate-y-1 snap-start">
      {/* Background */}
      <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-[#2a3a4a] via-[#1a2a3a] to-[#0f1a2a] text-4xl">
        {getRoomEmoji(room.room_type)}
      </div>
      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/30 to-black/85" />
      {/* Content */}
      <div className="absolute bottom-0 left-0 right-0 z-10 p-3.5">
        <div className="text-lg font-extrabold text-white drop-shadow-md">
          {room.room_name}
        </div>
        <div className="mb-2 text-[11px] font-medium text-white/70">
          {room.room_type}
        </div>
        <div className="mb-2 flex gap-2">
          <span className="rounded-md bg-white/15 px-2 py-0.5 text-[10px] font-semibold text-white/90 backdrop-blur-sm">
            👥 {room.max_guests} ท่าน
          </span>
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-base font-bold text-white">
            ฿{room.price_weekdays.toLocaleString()}
          </span>
          <span className="text-[10px] text-white/50">เริ่มต้น /คืน</span>
        </div>
      </div>
    </div>
  )
}
