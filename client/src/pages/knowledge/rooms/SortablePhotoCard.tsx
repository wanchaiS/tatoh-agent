import { useState } from 'react'
import { Trash2, GripVertical } from 'lucide-react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Button } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import type { PhotoResponse } from '@/hooks/usePhotos'

interface SortablePhotoCardProps {
  photo: PhotoResponse
  onDelete: () => void
  onOpen: () => void
}

export function SortablePhotoCard({ photo, onDelete, onOpen }: SortablePhotoCardProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: photo.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <>
      <div
        ref={setNodeRef}
        style={style}
        className="relative group"
        {...attributes}
      >
        {/* Drag handle */}
        <div
          {...listeners}
          className="absolute top-1.5 left-1.5 z-10 p-1 rounded bg-black/40 cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <GripVertical className="h-3 w-3 text-white" />
        </div>

        <div
          className="aspect-video bg-muted rounded-md overflow-hidden border cursor-zoom-in"
          onClick={onOpen}
        >
          <img
            src={photo.thumbnail_url}
            alt="Room photo"
            className="w-full h-full object-cover"
            loading="lazy"
          />

          {/* Delete button overlay */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => {
                e.stopPropagation()
                setConfirmOpen(true)
              }}
              className="text-white hover:text-white hover:bg-destructive/80"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete photo</AlertDialogTitle>
            <AlertDialogDescription>
              This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={onDelete}
              className="bg-destructive text-white hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
