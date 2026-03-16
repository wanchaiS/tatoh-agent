export function RoomCardSkeleton() {
  return (
    <div className="relative h-[220px] w-full flex-shrink-0 overflow-hidden rounded-xl bg-muted">
      {/* full-card shimmer sweep */}
      <div className="absolute inset-0 animate-shimmer" />
      {/* text placeholder bars at bottom */}
      <div className="absolute bottom-0 left-0 right-0 z-10 space-y-2 p-3">
        <div className="h-5 w-24 rounded bg-muted-foreground/20" />
        <div className="h-3 w-16 rounded bg-muted-foreground/15" />
        <div className="h-5 w-14 rounded-md bg-muted-foreground/15" />
        <div className="h-5 w-20 rounded bg-muted-foreground/20" />
      </div>
    </div>
  )
}
