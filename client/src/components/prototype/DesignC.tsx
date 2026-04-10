import { useState, useRef, useEffect } from "react"
import type { RoomData } from "@/components/gen-ui-compopnents/RoomCard"
import { RoomCardVertical } from "./RoomCardVertical"
import { ResortMap } from "./ResortMap"
import { MapLightbox } from "./MapLightbox"
import { MAP_LARGE } from "./mockData"

interface DesignCProps {
  rooms: RoomData[]
}

// Prototype-only: mock the user's search window. Real version will come from a search form.
const SEARCH_WINDOW = { start: "2026-04-10", end: "2026-05-15" }

function formatSearchWindow(start: string, end: string): string {
  const s = new Date(start + "T00:00:00")
  const e = new Date(end + "T00:00:00")
  const fmt = (dt: Date) => dt.toLocaleDateString("en-US", { month: "short", day: "numeric" })
  return `${fmt(s)} – ${fmt(e)}`
}

export function DesignC({ rooms }: DesignCProps) {
  const [expandedRoomId, setExpandedRoomId] = useState<number | null>(null)
  const [highlightedRoomId, setHighlightedRoomId] = useState<number | null>(null)
  const [mapLightboxOpen, setMapLightboxOpen] = useState(false)
  const cardListRef = useRef<HTMLDivElement>(null)
  const cardRefs = useRef<Record<number, HTMLDivElement | null>>({})

  function handleToggleExpand(roomId: number) {
    setExpandedRoomId(prev => prev === roomId ? null : roomId)
    setHighlightedRoomId(roomId)
  }

  function handlePinClick(room: RoomData) {
    setHighlightedRoomId(room.id)
    // Scroll card into view
    const cardEl = cardRefs.current[room.id]
    if (cardEl) {
      cardEl.scrollIntoView({ behavior: "smooth", block: "nearest" })
    }
  }

  // Clear highlight after a delay when not expanded
  useEffect(() => {
    if (highlightedRoomId && highlightedRoomId !== expandedRoomId) {
      const timer = setTimeout(() => setHighlightedRoomId(null), 2000)
      return () => clearTimeout(timer)
    }
  }, [highlightedRoomId, expandedRoomId])

  return (
    <>
      <div className="flex flex-col gap-3">
        {/* Header */}
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="font-bold text-lg text-foreground">{rooms.length}</span>
          <span className="font-semibold text-base text-foreground">rooms available</span>
          <span className="text-muted-foreground text-sm">·</span>
          <span className="text-sm text-muted-foreground [font-variant-numeric:tabular-nums]">
            {formatSearchWindow(SEARCH_WINDOW.start, SEARCH_WINDOW.end)}
          </span>
        </div>

        {/* Mobile: stacked. Desktop: side by side */}
        <div className="flex flex-col lg:flex-row lg:gap-4">
          {/* Map */}
          <div className="lg:w-[45%] lg:shrink-0">
            <div className="lg:sticky lg:top-4">
              <ResortMap
                rooms={rooms}
                mapSrc={MAP_LARGE}
                selectedRoomId={highlightedRoomId ?? expandedRoomId}
                onSelectRoom={handlePinClick}
                onMapClick={() => setMapLightboxOpen(true)}
              />
              <p className="text-[10px] text-muted-foreground text-center mt-1.5 hidden lg:block">Click map to enlarge</p>
            </div>
          </div>

          {/* Card list — scrollable with max height showing ~2.5 cards */}
          <div className="flex-1 mt-3 lg:mt-0">
            <div
              ref={cardListRef}
              className="flex flex-col gap-2.5 max-h-[420px] lg:max-h-[520px] overflow-y-auto pr-1 scrollbar-hide"
            >
              {rooms.map((room, i) => (
                <div
                  key={room.id}
                  ref={(el) => { cardRefs.current[room.id] = el }}
                  className="animate-card-enter"
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <RoomCardVertical
                    room={room}
                    isExpanded={expandedRoomId === room.id}
                    isHighlighted={highlightedRoomId === room.id}
                    onToggleExpand={() => handleToggleExpand(room.id)}
                  />
                </div>
              ))}
            </div>
            <p className="text-[10px] text-muted-foreground text-center mt-1.5 lg:hidden">Click map to enlarge · Scroll for more rooms</p>
          </div>
        </div>
      </div>

      {/* Map lightbox */}
      <MapLightbox
        mapSrc={MAP_LARGE}
        open={mapLightboxOpen}
        onOpenChange={setMapLightboxOpen}
      />
    </>
  )
}
