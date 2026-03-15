import { createFileRoute } from '@tanstack/react-router'
import { RoomDetail } from '../../../pages/knowledge/rooms/RoomDetail'

export const Route = createFileRoute('/knowledge/rooms/new')({
  component: () => <RoomDetail isNew={true} />,
})
