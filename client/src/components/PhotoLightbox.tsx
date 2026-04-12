import type { Slide } from 'yet-another-react-lightbox'
import Lightbox from 'yet-another-react-lightbox'
import 'yet-another-react-lightbox/styles.css'

interface PhotoLightboxProps {
  slides: Slide[]
  initialIndex: number
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function PhotoLightbox({ slides, initialIndex, open, onOpenChange }: PhotoLightboxProps) {
  return (
    <Lightbox
      open={open}
      close={() => onOpenChange(false)}
      slides={slides}
      index={initialIndex}
    />
  )
}
