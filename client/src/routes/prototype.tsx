import { createFileRoute } from "@tanstack/react-router"
import { MOCK_ROOMS } from "@/components/prototype/mockData"
import { DesignC } from "@/components/prototype/DesignC"

export const Route = createFileRoute("/prototype")({
  component: PrototypePage,
})

function PrototypePage() {
  return (
    <div className="min-h-screen bg-chat-bg overflow-y-auto h-screen">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-foreground mb-1">Room Search — Map Explorer</h1>
          <p className="text-sm text-muted-foreground">Map-first design with in-place card expansion.</p>
        </div>

        <div className="rounded-2xl border border-border bg-card/50 p-4 sm:p-6">
          <DesignC rooms={MOCK_ROOMS} />
        </div>
      </div>
    </div>
  )
}
