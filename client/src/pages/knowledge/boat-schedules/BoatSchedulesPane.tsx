import { Waves } from 'lucide-react'

export function BoatSchedulesPane() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center space-y-4">
        <Waves className="h-12 w-12 text-muted-foreground mx-auto" />
        <h2 className="text-2xl font-semibold">Boat Schedules</h2>
        <p className="text-muted-foreground max-w-sm">
          Coming soon — this knowledge domain is not yet configured.
        </p>
      </div>
    </div>
  )
}
