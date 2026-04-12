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
  
  // if it's one day
  if (s.getTime() === e.getTime()) return `${sMonth} ${s.getDate()}`

  // same month
  if (sMonth === eMonth) return `${sMonth} ${s.getDate()}–${e.getDate()}`

  return `${sMonth} ${s.getDate()} – ${eMonth} ${e.getDate()}`
}

const EASE_OUT_QUART = "cubic-bezier(0.25, 1, 0.5, 1)"

export function RoomCard({ room, isExpanded, isHighlighted, onToggleExpand, priority }: RoomCardProps) {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [activePhotoIndex, setActivePhotoIndex] = useState(0)
  const [loadedImages, setLoadedImages] = useState<Record<number, boolean>>({})
  const carouselRef = useRef<HTMLDivElement>(null)

  const photoList = room.photos ?? []
  const thumbSrc = photoList[0]?.thumbnails[480] ?? photoList[0]?.url ?? room.thumbnail_url ?? null

  const lightboxPhotos: Slide[] = photoList.map(p => ({
    src: p.url,
    srcSet: [
      { src: p.thumbnails[480], width: 480, height: 320 },
      { src: p.thumbnails[960], width: 960, height: 640 },
    ],
  }))

  // useEffect(() => {
  //   if (!isExpanded && carouselRef.current) {
  //     carouselRef.current.scrollTo({ left: 0, behavior: "instant" as ScrollBehavior })
  //     setActivePhotoIndex(0)
  //   }
  // }, [isExpanded])

  function handleCarouselScroll() {
    const el = carouselRef.current
    if (!el) return
    setActivePhotoIndex(Math.round(el.scrollLeft / el.clientWidth))
  }

  const specLabels = [
    ...(room.bed_queen > 0 ? [`${room.bed_queen} queen`] : []),
    ...(room.bed_single > 0 ? [`${room.bed_single} single`] : []),
    `${room.baths} bath`,
    `${room.size}m\u00B2`,
    ...(room.sea_view > 0 ? ["Sea view"] : []),
    `${room.steps_to_beach} steps to beach`,
  ]

  return (
    <>
      <div
        className={`room-card rounded-xl bg-card border overflow-hidden transition-shadow duration-300 ${
          isHighlighted
            ? "border-tropical-coral/50 shadow-md ring-1 ring-tropical-coral/20"
            : "border-border/50 hover:border-border hover:shadow-md"
        }`}
      >
        {/* === COLLAPSED: horizontal thumbnail + info === */}
        <div
          className={`transition-opacity duration-150 ${isExpanded ? "opacity-0 h-0 overflow-hidden" : "opacity-100"}`}
        >
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 p-3">
            {/* Thumbnail */}
            <button
              type="button"
              aria-label={`View ${room.room_name} photos`}
              className="h-[160px] sm:h-[120px] w-full sm:w-[140px] shrink-0 overflow-hidden rounded-lg relative cursor-pointer group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              onClick={() => setLightboxIndex(0)}
            >
              {thumbSrc ? (
                <img
                  src={thumbSrc}
                  srcSet={photoList[0]
                    ? `${photoList[0].thumbnails[240]} 240w, ${photoList[0].thumbnails[480]} 480w, ${photoList[0].thumbnails[960]} 960w`
                    : undefined}
                  sizes="(min-width: 640px) 140px, 100vw"
                  loading={priority ? "eager" : "lazy"}
                  fetchPriority={priority ? "high" : undefined}
                  decoding="async"
                  width={480}
                  height={320}
                  alt={room.room_name}
                  className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
              ) : (
                <div className="h-full w-full animate-shimmer rounded-lg" />
              )}
              {photoList.length > 1 && (
                <div className="absolute bottom-1.5 right-1.5 rounded-md bg-foreground/60 px-1.5 py-0.5 text-[0.625rem] font-medium text-white">
                  {photoList.length} photos
                </div>
              )}
            </button>

            {/* Info */}
            <div className="flex flex-col justify-between min-w-0 flex-1">
              <div>
                <div
                  className="flex items-start justify-between gap-2 cursor-pointer"
                  onClick={onToggleExpand}
                >
                  <h3 className="font-semibold text-base text-foreground leading-tight tracking-tight truncate">{room.room_name}</h3>
                  <div className="shrink-0 rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
                    <ChevronDown className="h-4 w-4" />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">{room.room_type}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  <span className="rounded-full border border-border bg-muted/40 px-2 py-0.5 text-xs font-medium text-muted-foreground [font-variant-numeric:tabular-nums]">
                    {room.max_guests} guests · {room.size}m²
                  </span>
                </div>
              </div>

              <div className="mt-2 flex flex-col gap-1.5">
                {room.date_ranges && room.date_ranges.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1 [font-variant-numeric:tabular-nums]">
                    {room.date_ranges.slice(0, 2).map((d, i) => (
                      <span
                        key={i}
                        className="rounded-full border border-border bg-accent/60 px-2 py-0.5 text-xs font-medium text-foreground"
                      >
                        {formatDateRange(d.start, d.end)}
                      </span>
                    ))}
                    {room.date_ranges.length > 2 && (
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); onToggleExpand?.() }}
                        className="rounded-full border border-border px-2 py-0.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent/60 transition-colors cursor-pointer"
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
        </div>

        {/* === EXPANDED: carousel + info + details === */}
        <div
          className={`transition-opacity duration-300 ${isExpanded ? "opacity-100" : "opacity-0 h-0 overflow-hidden"}`}
          style={{ transitionDelay: isExpanded ? "50ms" : "0ms", transitionTimingFunction: EASE_OUT_QUART }}
        >
          {/* Full-width carousel */}
          <div className="relative">
            <div
              ref={carouselRef}
              onScroll={handleCarouselScroll}
              className="flex h-[200px] sm:h-[220px] overflow-x-auto snap-x snap-mandatory scrollbar-hide"
            >
              {photoList.length > 0 ? (
                photoList.map((p, i) => (
                  <div
                    key={i}
                    className="flex-[0_0_100%] snap-center shrink-0 cursor-pointer relative"
                    onClick={() => setLightboxIndex(i)}
                  >
                    {!loadedImages[i] && <div className="absolute inset-0 animate-shimmer" />}
                    <img
                      src={p.thumbnails[480] ?? p.url}
                      srcSet={`${p.thumbnails[240]} 240w, ${p.thumbnails[480]} 480w, ${p.thumbnails[960]} 960w`}
                      sizes="(min-width: 640px) 500px, 100vw"
                      loading={i === 0 ? "eager" : "lazy"}
                      decoding="async"
                      width={960}
                      height={640}
                      alt={`${room.room_name} photo ${i + 1}`}
                      onLoad={() => setLoadedImages(prev => ({ ...prev, [i]: true }))}
                      className={`h-full w-full object-cover transition-opacity duration-500 ${loadedImages[i] ? "opacity-100" : "opacity-0"}`}
                    />
                  </div>
                ))
              ) : (
                <div className="flex-[0_0_100%] animate-shimmer" />
              )}
            </div>

            {/* Dot indicators */}
            {photoList.length > 1 && (
              <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-1">
                {photoList.map((_, i) => (
                  <div
                    key={i}
                    className={`h-1.5 rounded-full transition-[width,background-color] duration-300 ${
                      i === activePhotoIndex ? "w-3 bg-white" : "w-1.5 bg-white/50"
                    }`}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Info + details below carousel */}
          <div className="p-3 flex flex-col gap-3">
            {/* Header row */}
            <div>
              <div
                className="flex items-start justify-between gap-2 cursor-pointer"
                onClick={onToggleExpand}
              >
                <h3 className="font-semibold text-base text-foreground leading-tight tracking-tight truncate">{room.room_name}</h3>
                <div className="shrink-0 rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
                  <ChevronDown
                    className="h-4 w-4 transition-transform duration-300"
                    style={{ transform: "rotate(180deg)", transitionTimingFunction: EASE_OUT_QUART }}
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">{room.room_type}</p>
            </div>

            {/* Summary */}
            {room.summary && (
              <div
                className="transition-[opacity,transform] duration-250 ease-out"
                style={{
                  transitionDelay: isExpanded ? "100ms" : "0ms",
                  opacity: isExpanded ? 1 : 0,
                  transform: isExpanded ? "translateY(0)" : "translateY(8px)",
                }}
              >
                <p className="text-sm text-muted-foreground leading-relaxed">{room.summary}</p>
              </div>
            )}

            {/* Specs */}
            <div
              className="transition-[opacity,transform] duration-250 ease-out"
              style={{
                transitionDelay: isExpanded ? "160ms" : "0ms",
                opacity: isExpanded ? 1 : 0,
                transform: isExpanded ? "translateY(0)" : "translateY(8px)",
              }}
            >
              <div className="flex flex-wrap gap-1.5">
                {specLabels.map((label) => (
                  <span key={label} className="rounded-md border border-border bg-muted/60 px-2 py-0.5 text-xs font-medium text-foreground">{label}</span>
                ))}
              </div>
            </div>

            {/* Date ranges */}
            {room.date_ranges && room.date_ranges.length > 0 && (
              <div
                className="transition-[opacity,transform] duration-250 ease-out"
                style={{
                  transitionDelay: isExpanded ? "220ms" : "0ms",
                  opacity: isExpanded ? 1 : 0,
                  transform: isExpanded ? "translateY(0)" : "translateY(8px)",
                }}
              >
                <div className="flex flex-wrap items-center gap-1 [font-variant-numeric:tabular-nums]">
                  {room.date_ranges.map((d, i) => (
                    <span
                      key={i}
                      className="rounded-full border border-border bg-accent/60 px-2 py-0.5 text-xs font-medium text-foreground"
                    >
                      {formatDateRange(d.start, d.end)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Inline pricing */}
            <div
              className="transition-[opacity,transform] duration-250 ease-out"
              style={{
                transitionDelay: isExpanded ? "280ms" : "0ms",
                opacity: isExpanded ? 1 : 0,
                transform: isExpanded ? "translateY(0)" : "translateY(8px)",
              }}
            >
              <div className="flex gap-4 [font-variant-numeric:tabular-nums]">
                <div>
                  <p className="text-xs text-muted-foreground">Weekday</p>
                  <p className="font-medium text-sm text-foreground">฿{room.price_weekdays.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Weekend</p>
                  <p className="font-medium text-sm text-foreground">฿{room.price_weekends_holidays.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">New Year / Songkran</p>
                  <p className="font-medium text-sm text-foreground">฿{room.price_ny_songkran.toLocaleString()}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <PhotoLightbox
        slides={lightboxPhotos}
        initialIndex={lightboxIndex ?? 0}
        open={lightboxIndex !== null}
        onOpenChange={(open) => { if (!open) setLightboxIndex(null) }}
      />
    </>
  )
}
