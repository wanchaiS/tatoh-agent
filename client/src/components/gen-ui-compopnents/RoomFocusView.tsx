import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight } from "lucide-react"
import type { RoomData } from "./RoomCard"
import { RoomDetail } from "./RoomDetail"

interface RoomCardFocusViewProps {
  room: RoomData
  hasPrev: boolean
  hasNext: boolean
  prevRoomName?: string
  nextRoomName?: string
  onPrev: () => void
  onNext: () => void
  onBack: () => void
}

export function RoomCardFocusView({ room, hasPrev, hasNext, prevRoomName, nextRoomName, onPrev, onNext, onBack }: RoomCardFocusViewProps) {
  return (
    <div className="animate-in fade-in duration-300">
      {/* Header row */}
      <div className="flex items-center justify-between gap-2 px-1 pb-2">
        <Button variant="ghost" size="sm" onClick={onBack} className="-ml-1 gap-1 text-muted-foreground hover:text-foreground">
          <ChevronLeft className="h-4 w-4" />
          All rooms
        </Button>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onPrev} disabled={!hasPrev} className="gap-1 text-muted-foreground hover:text-foreground px-2">
            <ChevronLeft className="h-4 w-4 shrink-0" />
            <span className="max-w-[60px] truncate text-xs">{prevRoomName ?? ""}</span>
          </Button>
          <Button variant="ghost" size="sm" onClick={onNext} disabled={!hasNext} className="gap-1 text-muted-foreground hover:text-foreground px-2">
            <span className="max-w-[60px] truncate text-xs">{nextRoomName ?? ""}</span>
            <ChevronRight className="h-4 w-4 shrink-0" />
          </Button>
        </div>
      </div>

      <RoomDetail room={room} />
    </div>
  )
}
