import { useEffect, useRef, useState } from "react"

import type { RoomCardData } from "./RoomCard"

interface ResortMapProps {
  rooms: RoomCardData[]
  mapSrc: string
  pinPositions: Record<number, { x: number; y: number }>
  selectedRoomId?: number | null
  onSelectRoom?: (room: RoomCardData) => void
  onMapClick?: () => void
}

export function ResortMap({ rooms, mapSrc, pinPositions, selectedRoomId, onSelectRoom, onMapClick }: ResortMapProps) {
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
        loading="lazy"
        width={1200}
        height={900}
        className="w-full h-auto rounded-xl"
      />

      {onMapClick && (
        <button
          onClick={onMapClick}
          aria-label="Expand map"
          className="absolute top-2 right-2 z-20 flex items-center gap-1.5 px-3 py-1.5 bg-card rounded-lg shadow-lg hover:bg-muted transition-colors text-sm font-medium text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
          </svg>
        </button>
      )}

      {imgRect && rooms.map((room) => {
        const pos = pinPositions[room.id]
        if (!pos) return null
        const isSelected = selectedRoomId === room.id
        const pinLeft = imgRect.left + (pos.x / 100) * imgRect.width
        const pinTop = imgRect.top + (pos.y / 100) * imgRect.height
        return (
          <button
            key={room.id}
            onClick={(e) => { e.stopPropagation(); onSelectRoom?.(room) }}
            className="absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer group z-10 focus-visible:outline-none"
            style={{ left: pinLeft, top: pinTop }}
            aria-label={room.room_name}
          >
            <div
              className={`w-7 h-7 rounded-full transition-[background-color,box-shadow,transform] duration-200 flex items-center justify-center
                ${isSelected
                  ? "bg-tropical-coral ring-2 ring-white shadow-lg scale-110"
                  : "bg-white ring-2 ring-tropical-coral shadow-md group-hover:bg-tropical-coral group-hover:ring-white group-hover:shadow-lg group-hover:scale-110 group-focus-visible:ring-ring"
                }
              `}
            >
              <span className={`text-[0.625rem] font-bold leading-none
                ${isSelected ? "text-white" : "text-tropical-coral group-hover:text-white"}
              `}>
                {room.id}
              </span>
            </div>
          </button>
        )
      })}
    </div>
  )
}
