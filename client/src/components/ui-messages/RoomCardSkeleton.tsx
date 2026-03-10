export function RoomCardSkeleton() {
  return (
    <div className="relative h-[280px] w-[200px] flex-shrink-0 overflow-hidden rounded-2xl snap-start">
      <div className="absolute inset-0 bg-gradient-to-br from-[#2a3a4a] via-[#1a2a3a] to-[#0f1a2a]" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/30 to-black/85" />
      <div className="absolute bottom-0 left-0 right-0 z-10 space-y-2 p-3.5">
        <div className="h-5 w-24 animate-pulse rounded bg-white/20" />
        <div className="h-3 w-16 animate-pulse rounded bg-white/15" />
        <div className="h-5 w-14 animate-pulse rounded-md bg-white/15" />
        <div className="h-5 w-20 animate-pulse rounded bg-white/20" />
      </div>
    </div>
  )
}
