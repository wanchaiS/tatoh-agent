import { useState, useEffect, useRef } from 'react'
import { ChevronLeft, ChevronRight, X } from 'lucide-react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import type { PhotoResponse } from '@/hooks/usePhotos'

interface PhotoLightboxProps {
  photos: PhotoResponse[]
  initialIndex: number
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function PhotoLightbox({ photos, initialIndex, open, onOpenChange }: PhotoLightboxProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex)
  const [direction, setDirection] = useState<'left' | 'right'>('right')

  useEffect(() => {
    if (open) setCurrentIndex(initialIndex)
  }, [open, initialIndex])

  const prev = () => {
    setDirection('left')
    setCurrentIndex((i) => (i - 1 + photos.length) % photos.length)
  }
  const next = () => {
    setDirection('right')
    setCurrentIndex((i) => (i + 1) % photos.length)
  }

  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') prev()
      else if (e.key === 'ArrowRight') next()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, photos.length])

  const lastWheelTime = useRef(0)

  const handleWheel = (e: React.WheelEvent) => {
    const now = Date.now()
    if (now - lastWheelTime.current < 300) return
    lastWheelTime.current = now
    const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
    if (delta > 0) next()
    else if (delta < 0) prev()
  }

  const touchStartX = useRef<number | null>(null)

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return
    const delta = touchStartX.current - e.changedTouches[0].clientX
    if (Math.abs(delta) > 40) delta > 0 ? next() : prev()
    touchStartX.current = null
  }

  if (!photos.length) return null
  const photo = photos[currentIndex]

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/90 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className="fixed inset-0 z-50 flex items-center justify-center outline-none"
          onClick={() => onOpenChange(false)}
          onWheel={handleWheel}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          <DialogPrimitive.Close className="cursor-pointer absolute top-4 right-4 z-10 p-2 rounded-full bg-black/40 hover:bg-black/70 text-white transition-colors">
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>

          {photos.length > 1 && (
            <button
              onClick={(e) => { e.stopPropagation(); prev() }}
              className="cursor-pointer absolute left-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-black/40 hover:bg-black/70 text-white transition-colors"
              aria-label="Previous photo"
            >
              <ChevronLeft className="h-6 w-6" />
            </button>
          )}

          <img
            key={photo.id}
            src={photo.url}
            alt="Room photo"
            onClick={(e) => e.stopPropagation()}
            className={`max-h-[90vh] max-w-[90vw] object-contain animate-in fade-in duration-200 ${
              direction === 'right' ? 'slide-in-from-right-8' : 'slide-in-from-left-8'
            }`}
          />

          {photos.length > 1 && (
            <button
              onClick={(e) => { e.stopPropagation(); next() }}
              className="cursor-pointer absolute right-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-black/40 hover:bg-black/70 text-white transition-colors"
              aria-label="Next photo"
            >
              <ChevronRight className="h-6 w-6" />
            </button>
          )}

          {photos.length > 1 && (
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-white/80 text-sm bg-black/40 px-3 py-1 rounded-full">
              {currentIndex + 1} / {photos.length}
            </div>
          )}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
