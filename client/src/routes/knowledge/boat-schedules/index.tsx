import { createFileRoute } from '@tanstack/react-router'
import { BoatSchedulesPane } from '../../../pages/knowledge/boat-schedules/BoatSchedulesPane'

export const Route = createFileRoute('/knowledge/boat-schedules/')({
  component: BoatSchedulesPane,
})
