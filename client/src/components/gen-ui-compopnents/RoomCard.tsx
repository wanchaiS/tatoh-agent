import { ChevronDown } from "lucide-react"
import { useRef, useState } from "react"
import type { Slide } from "yet-another-react-lightbox"

import { PhotoLightbox } from "@/components/PhotoLightbox"

export interface DateRange {
  start: string
  end: string
}

export interface EmbeddedPhoto {
  url: string
  thumbnails: Record<number, string>
}

export interface RoomCardData {
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
  photos?: EmbeddedPhoto[]
  date_ranges?: DateRange[]
}
interface RoomCardProps {
  room: RoomCardData
  isExpanded?: boolean
  isHighlighted?: boolean
  onToggleExpand?: () => void
  priority?: boolean
}

function formatDateRange(start: string, end: string): string {
  const s = new Date(start + "T00:00:00")
  const e = new Date(end + "T00:00:00")
  const sMonth = s.toLocaleDateString("en-US", { month: "short" })
  const eMonth = e.toLocaleDateString("en-US", { month: "short" })
  if (sMonth === eMonth) return `${sMonth} ${s.getDate()}–${e.getDate()}`
  return `${sMonth} ${s.getDate()} – ${eMonth} ${e.getDate()}`
}

function nightsBetween(start: string, end: string): number {
  const s = new Date(start + "T00:00:00")
  const e = new Date(end + "T00:00:00")
  return Math.round((e.getTime() - s.getTime()) / (1000 * 60 * 60 * 24))
}

export function RoomCard({ room, isExpanded, isHighlighted, onToggleExpand, priority }: RoomCardProps) {
  const [thumbLoaded, setThumbLoaded] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [activePhotoIndex, setActivePhotoIndex] = useState(0)
  const [loadedImages, setLoadedImages] = useState<Record<number, boolean>>({})
  const carouselRef = useRef<HTMLDivElement>(null)

  const photoList = room.photos ?? []
  const photoSrc = photoList[0]?.thumbnails[240] ?? photoList[0]?.url ?? room.thumbnail_url ?? null

  const lightboxPhotos: Slide[] = photoList.map(p => ({
    src: p.url,
    srcSet: [
      { src: p.thumbnails[480], width: 480, height: 320 },
      { src: p.thumbnails[960], width: 960, height: 640 },
    ],
  }))

  function handleCarouselScroll() {
    const el = carouselRef.current
    if (!el) return
    setActivePhotoIndex(Math.round(el.scrollLeft / el.clientWidth))
  }

  return (
    <>
      <div
        className={`rounded-xl bg-card border overflow-hidden transition-all duration-300 ${
          isHighlighted
            ? "border-tropical-coral/50 shadow-md ring-1 ring-tropical-coral/20"
            : "border-border/50 hover:border-border hover:shadow-md"
        }`}
      >
        {/* Collapsed card */}
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 p-3">
          {/* Thumbnail — click opens lightbox */}
          <div
            className="h-[160px] sm:h-[130px] w-full sm:w-[160px] shrink-0 overflow-hidden rounded-lg relative cursor-pointer group"
            onClick={() => setLightboxIndex(0)}
          >
            {photoSrc ? (
              <>
                {!thumbLoaded && <div className="absolute inset-0 animate-shimmer rounded-lg" />}
                <img
                  src={photoSrc}
                  srcSet={photoList[0]
                    ? `${photoList[0].thumbnails[240]} 240w, ${photoList[0].thumbnails[480]} 480w, ${photoList[0].thumbnails[960]} 960w`
                    : undefined}
                  sizes="(min-width: 640px) 160px, 100vw"
                  loading={priority ? "eager" : "lazy"}
                  fetchPriority={priority ? "high" : undefined}
                  decoding="async"
                  width={600}
                  height={400}
                  alt={room.room_name}
                  onLoad={() => setThumbLoaded(true)}
                  className={`h-full w-full object-cover transition-all duration-500 group-hover:scale-105 ${thumbLoaded ? "opacity-100" : "opacity-0"}`}
                />
              </>
            ) : (
              <div className="h-full w-full animate-shimmer rounded-lg" />
            )}
            {/* Photo count badge */}
            {photoList.length > 1 && (
              <div className="absolute bottom-1.5 right-1.5 rounded-md bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white">
                {photoList.length} photos
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex flex-col justify-between min-w-0 flex-1">
            <div>
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold text-base text-foreground leading-tight truncate">{room.room_name}</h3>
                {/* Expand toggle */}
                <button
                  onClick={onToggleExpand}
                  className="shrink-0 rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors cursor-pointer"
                  aria-label={isExpanded ? "Collapse details" : "Expand details"}
                >
                  <ChevronDown className={`h-4 w-4 transition-transform duration-300 ${isExpanded ? "rotate-180" : ""}`} />
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">{room.room_type}</p>
              <div className="flex flex-wrap gap-1 mt-2">
                <span className="rounded-full border border-border bg-muted/40 px-2 py-0.5 text-[11px] font-medium text-muted-foreground [font-variant-numeric:tabular-nums]">
                  {room.max_guests} guests · {room.size}m²
                </span>
              </div>
            </div>

            <div className="mt-3 flex flex-col gap-2">
              {room.date_ranges && room.date_ranges.length > 0 && (
                <div className="flex flex-wrap items-center gap-1 [font-variant-numeric:tabular-nums]">
                  {room.date_ranges.slice(0, 2).map((d, i) => (
                    <span
                      key={i}
                      className="rounded-full border border-border bg-accent/60 px-2 py-0.5 text-[11px] font-medium text-foreground"
                    >
                      {formatDateRange(d.start, d.end)}
                    </span>
                  ))}
                  {room.date_ranges.length > 2 && (
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); onToggleExpand?.() }}
                      className="rounded-full border border-border px-2 py-0.5 text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-accent/60 transition-colors cursor-pointer"
                    >
                      +{room.date_ranges.length - 2} more
                    </button>
                  )}
                </div>
              )}

              <div>
                <span className="text-xs text-muted-foreground">From </span>
                <span className="font-semibold text-lg text-tropical-coral [font-variant-numeric:tabular-nums]">฿{room.price_weekdays.toLocaleString()}</span>
                <span className="text-xs text-muted-foreground ml-1">/night</span>
              </div>
            </div>
          </div>
        </div>

        {/* Expandable details */}
        <div
          className={`grid transition-all duration-300 ease-in-out ${
            isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
          }`}
        >
          <div className="overflow-hidden">
            <div className="border-t border-border/50 px-3 pb-4 pt-3 flex flex-col gap-4">
              {/* Photo carousel — only mounted when expanded */}
              {isExpanded && photoList.length > 0 && (
                <div>
                  <div
                    ref={carouselRef}
                    onScroll={handleCarouselScroll}
                    className="flex overflow-x-auto snap-x snap-mandatory scrollbar-hide rounded-xl gap-2"
                  >
                    {photoList.map((p, i) => (
                      <div
                        key={i}
                        className="flex-[0_0_100%] snap-center shrink-0 cursor-pointer relative h-44 sm:h-56"
                        onClick={() => setLightboxIndex(i)}
                      >
                        {!loadedImages[i] && <div className="absolute inset-0 animate-shimmer rounded-xl" />}
                        <img
                          src={p.thumbnails[480] ?? p.url}
                          srcSet={`${p.thumbnails[240]} 240w, ${p.thumbnails[480]} 480w, ${p.thumbnails[960]} 960w`}
                          sizes="(min-width: 640px) 400px, 90vw"
                          loading="lazy"
                          decoding="async"
                          width={960}
                          height={640}
                          alt={`${room.room_name} photo ${i + 1}`}
                          onLoad={() => setLoadedImages(prev => ({ ...prev, [i]: true }))}
                          className={`h-full w-full object-cover rounded-xl transition-opacity duration-500 ${loadedImages[i] ? "opacity-100" : "opacity-0"}`}
                        />
                      </div>
                    ))}
                  </div>
                  {photoList.length > 1 && (
                    <div className="flex justify-center gap-1 pt-2">
                      {photoList.map((_, i) => (
                        <div key={i} className={`h-1.5 rounded-full transition-all duration-300 ${i === activePhotoIndex ? "w-3 bg-foreground" : "w-1.5 bg-muted-foreground/40"}`} />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Summary */}
              {room.summary && (
                <p className="text-sm text-muted-foreground leading-relaxed">{room.summary}</p>
              )}

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

              {/* Pricing grid */}
              <div className="grid grid-cols-3 gap-px rounded-xl overflow-hidden border border-border">
                {[
                  { label: "Weekday", price: room.price_weekdays },
                  { label: "Weekend", price: room.price_weekends_holidays },
                  { label: "Holiday", price: room.price_ny_songkran },
                ].map(({ label, price }) => (
                  <div key={label} className="bg-muted/30 p-2.5 text-center">
                    <div className="text-[10px] text-muted-foreground mb-0.5">{label}</div>
                    <div className="text-base font-bold text-foreground">฿{price.toLocaleString()}</div>
                  </div>
                ))}
              </div>

              {/* Availability windows — informational, with Select action */}
              {room.date_ranges && room.date_ranges.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-foreground mb-1.5">When you can stay</h4>
                  <div className="flex flex-wrap gap-1.5 [font-variant-numeric:tabular-nums]">
                    {room.date_ranges.map((d, i) => (
                      <div
                        key={i}
                        className="rounded-lg border border-border bg-muted/30 px-3 py-1.5"
                      >
                        <div className="text-sm font-medium text-foreground leading-tight">
                          {formatDateRange(d.start, d.end)}
                        </div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">
                          {nightsBetween(d.start, d.end)} nights available
                        </div>
                      </div>
                    ))}
                  </div>

                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Lightbox */}
      <PhotoLightbox
        slides={lightboxPhotos}
        initialIndex={lightboxIndex ?? 0}
        open={lightboxIndex !== null}
        onOpenChange={(open) => { if (!open) setLightboxIndex(null) }}
      />
    </>
  )
}
