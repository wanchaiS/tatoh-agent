import { createFileRoute } from '@tanstack/react-router'
import { useSuspenseQuery } from '@tanstack/react-query'
import { roomQueryOptions } from '../../../hooks/useRooms'
import { RoomDetail } from '../../../pages/knowledge/rooms/RoomDetail'

const VALID_TABS = ['details', 'attributes', 'photos'] as const
type Tab = (typeof VALID_TABS)[number]

export const Route = createFileRoute('/knowledge/rooms/$id')({
  validateSearch: (search: Record<string, unknown>) => ({
    tab: (VALID_TABS.includes(search.tab as Tab) ? search.tab : 'details') as Tab,
  }),
  loader: ({ context: { queryClient }, params }) =>
    queryClient.ensureQueryData(roomQueryOptions(Number(params.id))),
  pendingComponent: RoomDetailPending,
  errorComponent: RoomDetailError,
  component: RoomDetailWrapper,
})

function RoomDetailPending() {
  return <div className="p-8 text-muted-foreground">Loading room...</div>
}

function RoomDetailError({ error }: { error: Error }) {
  return <div className="p-8 text-destructive">Failed to load room: {error.message}</div>
}

function RoomDetailWrapper() {
  const { id } = Route.useParams()
  const { tab } = Route.useSearch()
  const navigate = Route.useNavigate()
  const { data: room } = useSuspenseQuery(roomQueryOptions(Number(id)))

  return (
    <RoomDetail
      room={room}
      isNew={false}
      tab={tab}
      onTabChange={(t) => navigate({ search: (prev) => ({ ...prev, tab: t as Tab }) })}
    />
  )
}
