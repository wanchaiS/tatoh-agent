import type { RoomData } from "@/components/gen-ui-compopnents/RoomCard"
import { useEffect, useRef, useState } from "react"
import { ROOM_PIN_POSITIONS } from "./mockData"

interface ResortMapProps {
  rooms: RoomData[]
  mapSrc: string
  selectedRoomId?: number | null
  onSelectRoom?: (room: RoomData) => void
  onMapClick?: () => void
}

export function ResortMap({ rooms, mapSrc, selectedRoomId, onSelectRoom, onMapClick }: ResortMapProps) {
  const imgRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [imgRect, setImgRect] = useState<{ left: number; top: number; width: number; height: number } | null>(null)

  function updateImgRect() {
    const img = imgRef.current
    const container = containerRef.current
    if (!img || !container || !img.naturalWidth) return

    const cW = container.clientWidth
    const cH = container.clientHeight
    const iW = img.naturalWidth
    const iH = img.naturalHeight
    const scale = Math.min(cW / iW, cH / iH)
    const renderedW = iW * scale
    const renderedH = iH * scale
    const offsetX = (cW - renderedW) / 2
    const offsetY = (cH - renderedH) / 2

    setImgRect({ left: offsetX, top: offsetY, width: renderedW, height: renderedH })
  }

  useEffect(() => {
    updateImgRect()
    window.addEventListener("resize", updateImgRect)
    return () => window.removeEventListener("resize", updateImgRect)
  }, [])

  return (
    <div ref={containerRef} className="relative w-full rounded-xl overflow-hidden bg-muted/30">
      <img
        ref={imgRef}
        src={mapSrc}
        alt="Resort map"
        onLoad={updateImgRect}
        className="w-full h-auto rounded-xl"
      />

      {/* Expand map button */}
      {onMapClick && (
        <button
          onClick={onMapClick}
          className="absolute top-2 right-2 z-20 flex items-center gap-1.5 px-3 py-1.5 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
          </svg>
        </button>
      )}

      {imgRect && rooms.map((room) => {
        const pos = ROOM_PIN_POSITIONS[room.id]
        if (!pos) return null
        const isSelected = selectedRoomId === room.id
        const pinLeft = imgRect.left + (pos.x / 100) * imgRect.width
        const pinTop = imgRect.top + (pos.y / 100) * imgRect.height
        return (
          <button
            key={room.id}
            onClick={(e) => { e.stopPropagation(); onSelectRoom?.(room) }}
            className="absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer group z-10"
            style={{ left: pinLeft, top: pinTop }}
            title={room.room_name}
          >
            <div
              className={`w-7 h-7 rounded-full transition-all duration-200 flex items-center justify-center
                ${isSelected
                  ? "bg-tropical-coral ring-2 ring-white shadow-[0_0_14px_rgba(var(--tropical-coral),0.6)] scale-110"
                  : "bg-white ring-2 ring-tropical-coral shadow-md group-hover:bg-tropical-coral group-hover:ring-white group-hover:shadow-lg group-hover:scale-110"
                }
              `}
            >
              <span className={`text-[8px] font-bold leading-none
                ${isSelected ? "text-white" : "text-tropical-coral group-hover:text-white"}
              `}>
                {room.room_name}
              </span>
            </div>
          </button>
        )
      })}
    </div>
  )
}
