import { PhotoLightbox } from "@/components/PhotoLightbox"
import type { PhotoResponse } from "@/hooks/usePhotos"
import { useListPhotos } from "@/hooks/usePhotos"
import { useEffect, useRef, useState } from "react"
import type { RoomData } from "./RoomCard"
import { RoomDetailSkeleton } from "./RoomDetailSkeleton"

interface RoomInfoProps {
  room: RoomData | null
  loading?: boolean
}

export function RoomInfo({ room, loading }: RoomInfoProps) {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [activeIndex, setActiveIndex] = useState(0)
  const [loadedImages, setLoadedImages] = useState<Record<number, boolean>>({})
  const scrollRef = useRef<HTMLDivElement>(null)
  const { data: photos, isLoading: photosLoading } = useListPhotos(room?.id ?? null)
  const photoList = photos ?? []
  
  const photoSources: string[] = photoList.length > 0
    ? photoList.map((p) => p.url)
    : room?.thumbnail_url ? [room.thumbnail_url] : []

  const lightboxPhotos: PhotoResponse[] = photoList.length > 0
    ? photoList
    : room?.thumbnail_url
      ? [{ 
          id: 0, 
          url: room.thumbnail_url,
          filename: 'thumbnail.jpg',
          sort_order: 0,
          thumbnail_url: room.thumbnail_url
        }]
      : []

  useEffect(() => {
    setLoadedImages({})
    setActiveIndex(0)
    scrollRef.current?.scrollTo({ left: 0 })
  }, [room?.id])

  function handleScroll() {
    const el = scrollRef.current
    if (!el) return
    const index = Math.round(el.scrollLeft / el.clientWidth)
    setActiveIndex(index)
  }

  if (loading || !room) {
    return <RoomDetailSkeleton />
  }

  return (
    <div className="flex flex-col gap-0">
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

        {/* Available Dates (search results) */}
        {room.available_dates && room.available_dates.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-2">Available Dates</h3>
            <div className="flex flex-col gap-1.5">
              {room.available_dates.map((d, i) => {
                const start = new Date(d.start_date + "T00:00:00")
                const end = new Date(d.end_date + "T00:00:00")
                const nights = Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
                const fmt = (dt: Date) => dt.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })
                return (
                  <div key={i} className="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-teal-600 dark:text-teal-400">↗</span>
                      <span className="text-foreground">{fmt(start)}</span>
                      <span className="text-muted-foreground">→</span>
                      <span className="text-foreground">{fmt(end)}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">{nights} {nights === 1 ? "night" : "nights"}</span>
                  </div>
                )
              })}
            </div>
            {room.extra_bed_required && (
              <div className="mt-2 flex items-center gap-1.5 rounded-lg border border-amber-300/40 bg-amber-50 dark:bg-amber-950/30 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
                <span>🛏</span>
                <span>Extra bed needed (+฿500/night)</span>
              </div>
            )}
          </div>
        )}

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
      </div>
    </div>
  )
}
