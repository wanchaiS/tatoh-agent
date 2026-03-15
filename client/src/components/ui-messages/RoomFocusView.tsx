import { useState, useEffect, useRef } from "react"
import { ArrowRight, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useListPhotos } from "@/hooks/usePhotos"
import type { PhotoResponse } from "@/hooks/usePhotos"
import type { RoomData } from "./RoomCard"
import { PhotoLightbox } from "@/components/PhotoLightbox"

interface RoomFocusViewProps {
  room: RoomData
  hasPrev: boolean
  hasNext: boolean
  prevRoomName?: string
  nextRoomName?: string
  onPrev: () => void
  onNext: () => void
  onBack: () => void
  onAskAI: (room: RoomData) => void
}

export function RoomFocusView({ room, hasPrev, hasNext, prevRoomName, nextRoomName, onPrev, onNext, onBack, onAskAI }: RoomFocusViewProps) {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [activeIndex, setActiveIndex] = useState(0)
  const [loadedImages, setLoadedImages] = useState<Record<number, boolean>>({})
  const scrollRef = useRef<HTMLDivElement>(null)
  const { data: photos, isLoading: photosLoading } = useListPhotos(room.id)
  const photoList = photos ?? []

  const photoSources: string[] = photoList.length > 0
    ? photoList.map((p) => p.url)
    : room.thumbnail_url ? [room.thumbnail_url] : []

  const lightboxPhotos: PhotoResponse[] = photoList.length > 0
    ? photoList
    : room.thumbnail_url
      ? [{ id: "thumbnail", url: room.thumbnail_url } as PhotoResponse]
      : []

  useEffect(() => {
    setLoadedImages({})
    setActiveIndex(0)
    scrollRef.current?.scrollTo({ left: 0 })
  }, [room.id])

  function handleScroll() {
    const el = scrollRef.current
    if (!el) return
    const index = Math.round(el.scrollLeft / el.clientWidth)
    setActiveIndex(index)
  }

  return (
    <div className="animate-in fade-in duration-300">
      {/* Header row */}
      <div className="flex items-center justify-between gap-2 px-1 pb-2">
        <Button variant="ghost" size="sm" onClick={onBack} className="-ml-1 gap-1 text-muted-foreground hover:text-foreground">
          <ChevronLeft className="h-4 w-4" />
          All rooms
        </Button>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onPrev} disabled={!hasPrev} className="gap-1 text-muted-foreground hover:text-foreground px-2">
            <ChevronLeft className="h-4 w-4 shrink-0" />
            <span className="max-w-[60px] truncate text-xs">{prevRoomName ?? ""}</span>
          </Button>
          <Button variant="ghost" size="sm" onClick={onNext} disabled={!hasNext} className="gap-1 text-muted-foreground hover:text-foreground px-2">
            <span className="max-w-[60px] truncate text-xs">{nextRoomName ?? ""}</span>
            <ChevronRight className="h-4 w-4 shrink-0" />
          </Button>
        </div>
      </div>

      {/* Photo strip */}
      {photosLoading ? (
        <div className="overflow-hidden rounded-xl">
          <div className="h-44 sm:h-64 w-full animate-shimmer bg-muted" />
        </div>
      ) : photoSources.length > 0 ? (
        <div>
          <div ref={scrollRef} onScroll={handleScroll} className="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide rounded-xl gap-2">
            {photoSources.map((src, i) => (
              <div key={i} className="flex-[0_0_100%] snap-center shrink-0 cursor-pointer relative h-44 sm:h-64" onClick={() => setLightboxIndex(i)}>
                {!loadedImages[i] && (
                  <div className="absolute inset-0 animate-shimmer rounded-xl" />
                )}
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
        <div className="h-44 sm:h-64 w-full rounded-xl bg-muted" />
      )}

      <PhotoLightbox
        photos={lightboxPhotos}
        initialIndex={lightboxIndex ?? 0}
        open={lightboxIndex !== null}
        onOpenChange={(open) => { if (!open) setLightboxIndex(null) }}
      />

      {/* Details */}
      <div className="flex flex-col gap-4 pt-3">
        {/* Name + badges */}
        <div>
          <div className="flex items-start justify-between gap-2">
            <h2 className="leading-tight text-2xl font-bold text-foreground">{room.room_name}</h2>
            <div className="flex flex-wrap gap-1 justify-end shrink-0">
              {room.sea_view >= 7 && (
                <span className="rounded-full border border-border bg-muted/60 text-foreground px-2 py-0.5 text-xs font-medium">
                  Sea view
                </span>
              )}
              {room.privacy >= 7 && (
                <span className="rounded-full border border-border bg-muted/60 text-foreground px-2 py-0.5 text-xs font-medium">
                  Private
                </span>
              )}
            </div>
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">{room.room_type}</p>
        </div>

        {/* Specs row */}
        <div className="flex flex-wrap gap-1.5">
          {(["👥 " + room.max_guests,
            ...(room.bed_queen > 0 ? ["🛏 " + room.bed_queen + "Q"] : []),
            ...(room.bed_single > 0 ? ["🛏 " + room.bed_single + "S"] : []),
            "🚿 " + room.baths,
            "📐 " + room.size + "m²",
            "🏖 " + room.steps_to_beach + " steps",
          ]).map((label) => (
            <span key={label} className="rounded-md border border-border bg-muted/60 px-1.5 py-0.5 text-xs font-semibold text-foreground">{label}</span>
          ))}
        </div>

        {/* Summary */}
        {room.summary && (
          <p className="text-sm text-muted-foreground leading-relaxed">{room.summary}</p>
        )}

        {/* Pricing */}
        <div className="grid grid-cols-3 gap-px rounded-xl overflow-hidden border border-border">
          <div className="bg-muted/30 p-3 text-center">
            <div className="text-xs text-muted-foreground mb-0.5">Weekday</div>
            <div className="text-lg font-bold text-foreground">฿{room.price_weekdays.toLocaleString()}</div>
          </div>
          <div className="bg-muted/40 p-3 text-center border-x border-border">
            <div className="text-xs text-muted-foreground mb-0.5">Weekend</div>
            <div className="text-lg font-bold text-foreground">฿{room.price_weekends_holidays.toLocaleString()}</div>
          </div>
          <div className="bg-muted/30 p-3 text-center">
            <div className="text-xs text-muted-foreground mb-0.5">Holiday</div>
            <div className="text-lg font-bold text-foreground">฿{room.price_ny_songkran.toLocaleString()}</div>
          </div>
        </div>

        {/* Tags */}
        {room.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {room.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-border bg-muted/40 text-muted-foreground px-2.5 py-0.5 text-xs"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* CTA */}
        <Button
          className="w-full h-12 bg-tropical-coral hover:bg-tropical-coral/85 text-white border-0"
          onClick={() => onAskAI(room)}
        >
          Ask about this room
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
