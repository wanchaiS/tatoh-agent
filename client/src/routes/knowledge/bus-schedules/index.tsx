import { createFileRoute } from '@tanstack/react-router'
import { BusSchedulesPane } from '../../../pages/knowledge/bus-schedules/BusSchedulesPane'

export const Route = createFileRoute('/knowledge/bus-schedules/')({
  component: BusSchedulesPane,
})
