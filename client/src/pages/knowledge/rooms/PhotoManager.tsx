import { useState, useEffect, useRef } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import type { DragEndEvent } from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
} from '@dnd-kit/sortable'
import { Plus, Image, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useListPhotos, useDeletePhoto, useReorderPhotos, useUploadPhoto } from '@/hooks/usePhotos'
import { SortablePhotoCard } from './SortablePhotoCard'
import { PhotoLightbox } from '@/components/PhotoLightbox'
import { toast } from 'sonner'

interface PhotoManagerProps {
  roomId: number
}

const MAX_BYTES = 5 * 1024 * 1024
const MAX_PX = 2400

async function resizeIfNeeded(file: File): Promise<File> {
  if (file.size <= MAX_BYTES) return file

  return new Promise((resolve) => {
    const img = new window.Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      let { naturalWidth: w, naturalHeight: h } = img
      const scale = Math.min(1, MAX_PX / Math.max(w, h))
      w = Math.round(w * scale)
      h = Math.round(h * scale)
      const canvas = document.createElement('canvas')
      canvas.width = w
      canvas.height = h
      canvas.getContext('2d')!.drawImage(img, 0, 0, w, h)
      const tryEncode = (quality: number) => {
        canvas.toBlob((blob) => {
          if (!blob) { resolve(file); return }
          if (blob.size <= MAX_BYTES || quality <= 0.5) {
            resolve(new File([blob], file.name, { type: 'image/jpeg' }))
          } else {
            tryEncode(quality - 0.15)
          }
        }, 'image/jpeg', quality)
      }
      tryEncode(0.85)
    }
    img.src = url
  })
}

export function PhotoManager({ roomId }: PhotoManagerProps) {
  const { data: photos = [] } = useListPhotos(roomId)
  const deletePhoto = useDeletePhoto(roomId)
  const reorderPhotos = useReorderPhotos(roomId)
  const uploadPhoto = useUploadPhoto(roomId)

  const [photoItems, setPhotoItems] = useState(photos)
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [stagedFiles, setStagedFiles] = useState<File[]>([])
  const [processing, setProcessing] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setPhotoItems(photos)
  }, [photos])

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  )

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = photoItems.findIndex((p) => p.id === active.id)
      const newIndex = photoItems.findIndex((p) => p.id === over.id)

      const newItems = arrayMove(photoItems, oldIndex, newIndex)
      setPhotoItems(newItems)

      const reorderItems = newItems.map((photo, index) => ({
        id: photo.id,
        sort_order: index,
      }))

      try {
        await reorderPhotos.mutateAsync(reorderItems)
        toast.success('Photos reordered')
      } catch {
        toast.error('Failed to reorder photos')
        setPhotoItems(photos)
      }
    }
  }

  const handleDeletePhoto = async (photoId: number) => {
    try {
      await deletePhoto.mutateAsync(photoId)
      toast.success('Photo deleted')
    } catch {
      toast.error('Failed to delete photo')
    }
  }

  const addFiles = async (incoming: FileList | File[]) => {
    setProcessing(true)
    try {
      const results: File[] = []
      for (const f of Array.from(incoming)) {
        if (!f.type.startsWith('image/')) {
          toast.error(`${f.name}: not an image`)
          continue
        }
        const out = await resizeIfNeeded(f)
        if (out !== f) toast.info(`${f.name}: resized to fit 5 MB limit`)
        results.push(out)
      }
      setStagedFiles((prev) => [
        ...prev,
        ...results.filter((f) => !prev.find((p) => p.name === f.name)),
      ])
    } finally {
      setProcessing(false)
    }
  }

  const handleUpload = async () => {
    if (!stagedFiles.length) return
    setUploading(true)
    try {
      await Promise.all(stagedFiles.map((f) => uploadPhoto.mutateAsync(f)))
      toast.success(`${stagedFiles.length} photo${stagedFiles.length > 1 ? 's' : ''} uploaded`)
      setStagedFiles([])
    } catch {
      toast.error('Some photos failed to upload')
    } finally {
      setUploading(false)
    }
  }

  const stagingStrip = stagedFiles.length > 0 && (
    <div className="mt-4 rounded-lg p-3 space-y-3" style={{ backgroundColor: 'oklch(from var(--tropical-sand) l c h / 0.25)' }}>
      <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto">
        {stagedFiles.map((f, i) => (
          <div key={f.name} className="relative group animate-in fade-in zoom-in-95 duration-150">
            <img
              src={URL.createObjectURL(f)}
              className="aspect-square object-cover rounded-md w-full"
              alt={f.name}
            />
            <button
              onClick={() => setStagedFiles((prev) => prev.filter((_, j) => j !== i))}
              className="cursor-pointer absolute top-0.5 right-0.5 p-0.5 rounded-full bg-black/60 text-white opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <Button
          onClick={handleUpload}
          disabled={uploading || processing}
          style={{ backgroundColor: 'var(--tropical-coral)', color: 'white' }}
          className="hover:opacity-90 transition-opacity"
        >
          {uploading ? 'Uploading…' : `Upload ${stagedFiles.length} photo${stagedFiles.length !== 1 ? 's' : ''}`}
        </Button>
        <Button variant="outline" onClick={() => setStagedFiles([])}>
          Clear
        </Button>
      </div>
    </div>
  )

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={(e) => e.target.files && addFiles(e.target.files)}
      />

      {photos.length === 0 ? (
        <div className="w-full max-w-2xl mx-auto">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files) }}
            onClick={() => inputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              dragOver
                ? 'border-[var(--tropical-coral)] bg-[var(--tropical-coral)]/5'
                : 'border-muted-foreground/50 hover:border-[var(--tropical-coral)]/50'
            }`}
          >
            {processing ? (
              <Loader2 className="h-12 w-12 mx-auto mb-4 animate-spin" style={{ color: 'oklch(from var(--tropical-coral) l c h / 0.55)' }} />
            ) : (
              <Image className="h-12 w-12 mx-auto mb-4" style={{ color: 'oklch(from var(--tropical-coral) l c h / 0.55)' }} />
            )}
            <h3 className="text-lg font-semibold mb-2">
              {processing ? 'Processing…' : 'No photos yet'}
            </h3>
            <p className="text-sm text-muted-foreground">
              Drop photos here or click to browse
            </p>
          </div>
          {stagingStrip}
        </div>
      ) : (
        <div>
          <div className="grid grid-cols-3 gap-2">
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext items={photoItems.map((p) => p.id)} strategy={rectSortingStrategy}>
                {photoItems.map((photo, index) => (
                  <SortablePhotoCard
                    key={photo.id}
                    photo={photo}
                    onDelete={() => handleDeletePhoto(photo.id)}
                    onOpen={() => setLightboxIndex(index)}
                  />
                ))}
              </SortableContext>
            </DndContext>
            <div
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files) }}
              className={`aspect-video border-2 border-dashed rounded-md flex items-center justify-center cursor-pointer transition-colors ${
                dragOver
                  ? 'border-[var(--tropical-coral)] bg-[var(--tropical-coral)]/5'
                  : 'border-[var(--tropical-coral)]/20 hover:border-[var(--tropical-coral)]/60'
              }`}
            >
              <Plus className="h-6 w-6" style={{ color: 'oklch(from var(--tropical-coral) l c h / 0.45)' }} />
            </div>
          </div>
          {stagingStrip}
        </div>
      )}

      <PhotoLightbox
        photos={photoItems}
        initialIndex={lightboxIndex ?? 0}
        open={lightboxIndex !== null}
        onOpenChange={(open) => !open && setLightboxIndex(null)}
      />
    </div>
  )
}
