import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../lib/api'

export interface PhotoResponse {
  id: number
  filename: string
  sort_order: number
  url: string
  thumbnails: Record<number, string>  // { 240: "...", 480: "...", 960: "..." }
}

export interface PhotoReorderItem {
  id: number
  sort_order: number
}

export function useListPhotos(roomId: number | null) {
  return useQuery({
    queryKey: ['photos', roomId],
    queryFn: async () => {
      const res = await apiFetch(`/api/rooms/${roomId}/photos`)
      return res.json() as Promise<PhotoResponse[]>
    },
    enabled: roomId !== null,
  })
}

export function useUploadPhoto(roomId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (file: Blob) => {
      const formData = new FormData()
      formData.append('file', file, 'photo.jpg')

      const res = await apiFetch(`/api/rooms/${roomId}/photos`, {
        method: 'POST',
        body: formData,
      })
      return res.json() as Promise<PhotoResponse>
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['photos', roomId] })
    },
  })
}

export function useDeletePhoto(roomId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (photoId: number) => {
      await apiFetch(`/api/rooms/${roomId}/photos/${photoId}`, {
        method: 'DELETE',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['photos', roomId] })
    },
  })
}

export function useReorderPhotos(roomId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (items: PhotoReorderItem[]) => {
      const res = await apiFetch(`/api/rooms/${roomId}/photos/reorder`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(items),
      })
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['photos', roomId] })
    },
  })
}
