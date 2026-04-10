import { X } from "lucide-react"
import * as DialogPrimitive from "@radix-ui/react-dialog"

interface MapLightboxProps {
  mapSrc: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function MapLightbox({ mapSrc, open, onOpenChange }: MapLightboxProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/90 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className="fixed inset-0 z-50 flex items-center justify-center outline-none overflow-auto p-4"
          onClick={() => onOpenChange(false)}
        >
          <DialogPrimitive.Close className="cursor-pointer fixed top-4 right-4 z-10 p-2 rounded-full bg-black/40 hover:bg-black/70 text-white transition-colors">
            <X className="h-5 w-5" />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>

          <img
            src={mapSrc}
            alt="Resort map"
            onClick={(e) => e.stopPropagation()}
            className="max-h-[90vh] max-w-[90vw] object-contain rounded-xl animate-in fade-in duration-200"
          />
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
