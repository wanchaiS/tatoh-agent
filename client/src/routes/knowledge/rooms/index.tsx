import { createFileRoute } from '@tanstack/react-router'
import { roomsQueryOptions } from '../../../hooks/useRooms'
import { RoomsPane } from '../../../pages/knowledge/rooms/RoomsPane'

export const Route = createFileRoute('/knowledge/rooms/')({
  loader: ({ context: { queryClient } }) =>
    queryClient.ensureQueryData(roomsQueryOptions()),
  component: RoomsPane,
})
