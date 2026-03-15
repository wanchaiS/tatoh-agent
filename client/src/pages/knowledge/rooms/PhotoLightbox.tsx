import { useState, useEffect } from 'react'
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

  if (!photos.length) return null
  const photo = photos[currentIndex]

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        {/* Backdrop */}
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/90 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />

        {/* Content — raw fullscreen, no shadcn defaults */}
        <DialogPrimitive.Content className="fixed inset-0 z-50 flex items-center justify-center outline-none">
          {/* Close */}
          <DialogPrimitive.Close className="cursor-pointer absolute top-4 right-4 z-10 p-2 rounded-full bg-black/40 hover:bg-black/70 text-white transition-colors">
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>

          {/* Prev */}
          {photos.length > 1 && (
            <button
              onClick={prev}
              className="cursor-pointer absolute left-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-black/40 hover:bg-black/70 text-white transition-colors"
              aria-label="Previous photo"
            >
              <ChevronLeft className="h-6 w-6" />
            </button>
          )}

          {/* Image */}
          <img
            key={photo.id}
            src={photo.url}
            alt="Room photo"
            className={`max-h-[90vh] max-w-[90vw] object-contain animate-in fade-in duration-200 ${
              direction === 'right' ? 'slide-in-from-right-8' : 'slide-in-from-left-8'
            }`}
          />

          {/* Next */}
          {photos.length > 1 && (
            <button
              onClick={next}
              className="cursor-pointer absolute right-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-black/40 hover:bg-black/70 text-white transition-colors"
              aria-label="Next photo"
            >
              <ChevronRight className="h-6 w-6" />
            </button>
          )}

          {/* Counter */}
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
