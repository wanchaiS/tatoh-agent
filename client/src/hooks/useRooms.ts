import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export const roomsQueryOptions = () => ({
  queryKey: ['rooms'] as const,
  queryFn: async (): Promise<RoomResponse[]> => {
    const res = await fetch('/api/rooms')
    if (!res.ok) throw new Error('Failed to fetch rooms')
    return res.json()
  },
})

export const roomQueryOptions = (id: number) => ({
  queryKey: ['rooms', id] as const,
  queryFn: async (): Promise<RoomResponse> => {
    const res = await fetch(`/api/rooms/${id}`)
    if (!res.ok) throw new Error('Failed to fetch room')
    return res.json()
  },
})

export interface RoomResponse {
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
  tags?: string
}

export interface RoomCreate {
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
  tags?: string
}

export function useListRooms() {
  return useQuery(roomsQueryOptions())
}

export function useGetRoom(id: number) {
  return useQuery(roomQueryOptions(id))
}

export function useCreateRoom() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: RoomCreate) => {
      const res = await fetch('/api/rooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Failed to create room')
      return res.json() as Promise<RoomResponse>
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] })
    },
  })
}

export function useUpdateRoom() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<RoomCreate> }) => {
      const res = await fetch(`/api/rooms/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Failed to update room')
      return res.json() as Promise<RoomResponse>
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] })
      queryClient.invalidateQueries({ queryKey: ['rooms', id] })
    },
  })
}

export function useDeleteRoom() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`/api/rooms/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete room')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rooms'] })
    },
  })
}
