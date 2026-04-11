import { useRef, useState } from "react"

import { PhotoLightbox } from "@/components/PhotoLightbox"
import { ResortMap } from "@/components/gen-ui-compopnents/ResortMap"

import type { RoomCardData } from "./RoomCard"
import { RoomCard } from "./RoomCard"


function formatSearchWindow(start: string, end: string): string {
  const s = new Date(start + "T00:00:00")
  const e = new Date(end + "T00:00:00")
  const fmt = (dt: Date) => dt.toLocaleDateString("en-US", { month: "short", day: "numeric" })
  return `${fmt(s)} – ${fmt(e)}`
}

export function SearchResults({
  rooms,
  map,
  search_range,
}: {
  rooms: RoomCardData[]
  map: { src: string; pins: Record<number, { x: number; y: number }> }
  search_range: { start: string; end: string }
}) {
  const [expandedRoomId, setExpandedRoomId] = useState<number | null>(null)
  const [highlightedRoomId, setHighlightedRoomId] = useState<number | null>(null)
  const [mapLightboxOpen, setMapLightboxOpen] = useState(false)
  const cardRefs = useRef<Record<number, HTMLDivElement | null>>({})
  
  function handleToggleExpand(roomId: number) {
    setExpandedRoomId(prev => prev === roomId ? null : roomId)
    setHighlightedRoomId(roomId)
  }

  function handlePinClick(room: RoomCardData) {
    setHighlightedRoomId(room.id)
    if (expandedRoomId !== room.id) {
      setExpandedRoomId(null)
    }
    const cardEl = cardRefs.current[room.id]
    if (cardEl) {
      cardEl.scrollIntoView({ behavior: "smooth", block: "nearest" })
    }
  }

  if (rooms.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-muted/30 px-4 py-6 text-center text-sm text-muted-foreground">
        No rooms match your dates
      </div>
    )
  }

  return (
    <>
      <div className="rounded-2xl border border-border/60 bg-card p-3 sm:p-4">
        <div className="flex flex-col gap-3 w-full">
          {/* Header */}
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="font-bold text-lg text-foreground">{rooms.length}</span>
            <span className="font-semibold text-base text-foreground">
              {rooms.length === 1 ? "room" : "rooms"} available
            </span>
            {search_range?.start && search_range?.end && (
              <>
                <span className="text-muted-foreground text-sm">·</span>
                <span className="text-sm text-muted-foreground [font-variant-numeric:tabular-nums]">
                  {formatSearchWindow(search_range.start, search_range.end)}
                </span>
              </>
            )}
          </div>

          {/* Mobile: stacked. Desktop: side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-[44%_1fr] gap-3 lg:gap-4 lg:items-start">
            {/* Map */}
            <div>
              <div className="lg:sticky lg:top-4">
                <ResortMap
                  rooms={rooms}
                  mapSrc={map.src}
                  pinPositions={map.pins}
                  selectedRoomId={highlightedRoomId ?? expandedRoomId}
                  onSelectRoom={handlePinClick}
                  onMapClick={() => setMapLightboxOpen(true)}
                />
              </div>
            </div>

            {/* Card list */}
            <div className="mt-3 lg:mt-0 flex flex-col">
              <div className="flex flex-col gap-2.5 max-h-[480px] lg:max-h-[600px] overflow-y-auto pr-1 scrollbar-hide">
                {rooms.map((room, i) => (
                  <div
                    key={room.id}
                    ref={(el) => { cardRefs.current[room.id] = el }}
                    className="animate-card-enter"
                    style={{ animationDelay: `${i * 60}ms` }}
                  >
                    <RoomCard
                      room={room}
                      isExpanded={expandedRoomId === room.id}
                      isHighlighted={highlightedRoomId === room.id}
                      onToggleExpand={() => handleToggleExpand(room.id)}
                      priority={i === 0}
                    />
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground text-center mt-1.5 lg:hidden">
                Click map to enlarge · Scroll for more rooms
              </p>
            </div>
          </div>
        </div>
      </div>

      <PhotoLightbox
        slides={[{ src: map.src }]}
        initialIndex={0}
        open={mapLightboxOpen}
        onOpenChange={setMapLightboxOpen}
      />
    </>
  )
}
