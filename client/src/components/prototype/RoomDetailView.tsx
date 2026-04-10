import { PhotoLightbox } from "@/components/PhotoLightbox"
import { useListPhotos } from "@/hooks/usePhotos"
import { useRef, useState } from "react"
import type { RoomData } from "@/components/gen-ui-compopnents/RoomCard"
import { ResortMap } from "./ResortMap"
import { MAP_SMALL } from "./mockData"
import { ChevronLeft } from "lucide-react"
import { Button } from "@/components/ui/button"

interface RoomDetailViewProps {
  room: RoomData
  allRooms: RoomData[]
  onBack: () => void
}

export function RoomDetailView({ room, allRooms, onBack }: RoomDetailViewProps) {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [activeIndex, setActiveIndex] = useState(0)
  const [loadedImages, setLoadedImages] = useState<Record<number, boolean>>({})
  const scrollRef = useRef<HTMLDivElement>(null)
  const { data: photos, isLoading: photosLoading } = useListPhotos(room.id)
  const photoList = photos ?? []

  const photoSources = photoList.length > 0
    ? photoList.map((p) => p.url)
    : room.thumbnail_url ? [room.thumbnail_url] : []

  const lightboxPhotos = photoList.length > 0
    ? photoList
    : room.thumbnail_url
      ? [{ id: 0, url: room.thumbnail_url, filename: "thumbnail.jpg", sort_order: 0, thumbnail_url: room.thumbnail_url }]
      : []

  function handleScroll() {
    const el = scrollRef.current
    if (!el) return
    setActiveIndex(Math.round(el.scrollLeft / el.clientWidth))
  }

  return (
    <div className="animate-in fade-in duration-300">
      {/* Back button */}
      <div className="pb-3">
        <Button variant="ghost" size="sm" onClick={onBack} className="-ml-2 gap-1 text-muted-foreground hover:text-foreground">
          <ChevronLeft className="h-4 w-4" />
          Back to results
        </Button>
      </div>

      {/* Photo carousel */}
      {photosLoading ? (
        <div className="h-52 sm:h-72 w-full animate-shimmer rounded-xl" />
      ) : photoSources.length > 0 ? (
        <div>
          <div ref={scrollRef} onScroll={handleScroll} className="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide rounded-xl gap-2">
            {photoSources.map((src, i) => (
              <div key={i} className="flex-[0_0_100%] snap-center shrink-0 cursor-pointer relative h-52 sm:h-72" onClick={() => setLightboxIndex(i)}>
                {!loadedImages[i] && <div className="absolute inset-0 animate-shimmer rounded-xl" />}
                <img
                  src={src}
                  alt={`${room.room_name} photo ${i + 1}`}
                  onLoad={() => setLoadedImages(prev => ({ ...prev, [i]: true }))}
                  className={`h-full w-full object-cover rounded-xl transition-opacity duration-500 ${loadedImages[i] ? "opacity-100" : "opacity-0"}`}
                />
              </div>
            ))}
          </div>
          {photoSources.length > 1 && (
            <div className="flex justify-center gap-1 pt-2">
              {photoSources.map((_, i) => (
                <div key={i} className={`h-1.5 rounded-full transition-all duration-300 ${i === activeIndex ? "w-3 bg-foreground" : "w-1.5 bg-muted-foreground/40"}`} />
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="h-52 sm:h-72 w-full rounded-xl bg-muted" />
      )}

      <PhotoLightbox
        photos={lightboxPhotos}
        initialIndex={lightboxIndex ?? 0}
        open={lightboxIndex !== null}
        onOpenChange={(open) => { if (!open) setLightboxIndex(null) }}
      />

      {/* Room info */}
      <div className="flex flex-col gap-4 pt-4">
        <div>
          <div className="flex items-start justify-between gap-2">
            <h2 className="text-2xl font-bold text-foreground leading-tight">{room.room_name}</h2>
            <div className="flex gap-1 shrink-0">
              {room.sea_view >= 7 && (
                <span className="rounded-full border border-border bg-muted/60 text-foreground px-2 py-0.5 text-xs font-medium">Sea view</span>
              )}
              {room.privacy >= 7 && (
                <span className="rounded-full border border-border bg-muted/60 text-foreground px-2 py-0.5 text-xs font-medium">Private</span>
              )}
            </div>
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">{room.room_type}</p>
        </div>

        {/* Specs */}
        <div className="flex flex-wrap gap-1.5">
          {[
            `${room.max_guests} guests`,
            ...(room.bed_queen > 0 ? [`${room.bed_queen} queen`] : []),
            ...(room.bed_single > 0 ? [`${room.bed_single} single`] : []),
            `${room.baths} bath`,
            `${room.size}m\u00B2`,
            `${room.steps_to_beach} steps to beach`,
          ].map((label) => (
            <span key={label} className="rounded-md border border-border bg-muted/60 px-2 py-0.5 text-xs font-medium text-foreground">{label}</span>
          ))}
        </div>

        {/* Summary */}
        {room.summary && (
          <p className="text-sm text-muted-foreground leading-relaxed">{room.summary}</p>
        )}

        {/* Pricing grid */}
        <div className="grid grid-cols-3 gap-px rounded-xl overflow-hidden border border-border">
          {[
            { label: "Weekday", price: room.price_weekdays },
            { label: "Weekend", price: room.price_weekends_holidays },
            { label: "Holiday", price: room.price_ny_songkran },
          ].map(({ label, price }) => (
            <div key={label} className="bg-muted/30 p-3 text-center">
              <div className="text-xs text-muted-foreground mb-0.5">{label}</div>
              <div className="text-lg font-bold text-foreground">฿{price.toLocaleString()}</div>
            </div>
          ))}
        </div>

        {/* Date ranges */}
        {room.date_ranges && room.date_ranges.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-2">Available Dates</h3>
            <div className="flex flex-col gap-1.5">
              {room.date_ranges.map((d, i) => {
                const start = new Date(d.start + "T00:00:00")
                const end = new Date(d.end + "T00:00:00")
                const nights = Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
                const fmt = (dt: Date) => dt.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })
                return (
                  <div key={i} className="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
                    <span className="text-foreground">{fmt(start)} — {fmt(end)}</span>
                    <span className="text-xs text-muted-foreground">{nights} nights</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Mini map */}
        <div>
          <h3 className="text-sm font-semibold text-foreground mb-2">Location on Resort</h3>
          <ResortMap
            rooms={allRooms}
            mapSrc={MAP_SMALL}
            selectedRoomId={room.id}
            compact
          />
        </div>
      </div>
    </div>
  )
}
