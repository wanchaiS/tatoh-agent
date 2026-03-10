export function RoomDetailSkeleton() {
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card">
      {/* Image header */}
      <div className="h-[200px] animate-pulse bg-gradient-to-br from-[#2a3a4a] to-[#0f1a2a]" />

      {/* Body */}
      <div className="p-4">
        <div className="mb-1 h-6 w-32 animate-pulse rounded bg-muted" />
        <div className="mb-3 h-4 w-20 animate-pulse rounded bg-muted" />

        {/* Meta pills */}
        <div className="mb-4 flex flex-wrap gap-2">
          <div className="h-6 w-24 animate-pulse rounded-lg bg-muted" />
          <div className="h-6 w-20 animate-pulse rounded-lg bg-muted" />
          <div className="h-6 w-22 animate-pulse rounded-lg bg-muted" />
        </div>

        {/* Price grid */}
        <div className="mb-4 grid grid-cols-3 gap-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="rounded-lg bg-muted p-2.5">
              <div className="mx-auto mb-1 h-3 w-12 animate-pulse rounded bg-muted-foreground/20" />
              <div className="mx-auto h-5 w-16 animate-pulse rounded bg-muted-foreground/20" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
