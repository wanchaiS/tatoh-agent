import { useEffect, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

interface DateRange {
  start: string
  end: string
}

interface RoomDatePickerProps {
  windows: DateRange[]
  open: boolean
  onOpenChange: (open: boolean) => void
  initialStart?: string | null
  initialEnd?: string | null
  onConfirm: (start: string, end: string) => void
}

function enumerateDays(start: string, end: string): string[] {
  const out: string[] = []
  const s = new Date(start + "T00:00:00")
  const e = new Date(end + "T00:00:00")
  for (const d = new Date(s); d <= e; d.setDate(d.getDate() + 1)) {
    out.push(d.toISOString().slice(0, 10))
  }
  return out
}

function findWindowIndex(windows: DateRange[], day: string): number {
  return windows.findIndex((w) => day >= w.start && day <= w.end)
}

function nightsBetween(start: string, end: string): number {
  const s = new Date(start + "T00:00:00")
  const e = new Date(end + "T00:00:00")
  return Math.round((e.getTime() - s.getTime()) / (1000 * 60 * 60 * 24))
}

function formatLongRange(start: string, end: string): string {
  const s = new Date(start + "T00:00:00")
  const e = new Date(end + "T00:00:00")
  const fmt = (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
  return `${fmt(s)} – ${fmt(e)}`
}

export function RoomDatePicker({ windows, open, onOpenChange, initialStart, initialEnd, onConfirm }: RoomDatePickerProps) {
  const [start, setStart] = useState<string | null>(null)
  const [end, setEnd] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setStart(initialStart ?? null)
      setEnd(initialEnd ?? null)
    }
  }, [open, initialStart, initialEnd])

  function handleDayClick(day: string) {
    const windowIdx = findWindowIndex(windows, day)
    if (windowIdx === -1) return

    if (!start || (start && end)) {
      setStart(day)
      setEnd(null)
      return
    }
    if (day === start) {
      setStart(null)
      return
    }
    if (day < start) {
      setStart(day)
      return
    }
    const startWindowIdx = findWindowIndex(windows, start)
    if (windowIdx !== startWindowIdx) {
      setStart(day)
      setEnd(null)
      return
    }
    setEnd(day)
  }

  const nights = start && end ? nightsBetween(start, end) : 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Select your stay dates</DialogTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Pick a check-in and check-out within one of the available windows.
          </p>
        </DialogHeader>

        <div className="flex flex-col gap-4 mt-2 max-h-[55vh] overflow-y-auto pr-1">
          {windows.map((w, i) => {
            const days = enumerateDays(w.start, w.end)
            return (
              <div key={i}>
                <div className="text-xs font-semibold text-muted-foreground mb-2 [font-variant-numeric:tabular-nums]">
                  Window {i + 1} · {formatLongRange(w.start, w.end)}
                </div>
                <div className="flex flex-wrap gap-1">
                  {days.map((day) => {
                    const d = new Date(day + "T00:00:00")
                    const isStart = start === day
                    const isEnd = end === day
                    const inRange = !!(start && end && day > start && day < end)
                    const isEdge = isStart || isEnd
                    return (
                      <button
                        key={day}
                        type="button"
                        onClick={() => handleDayClick(day)}
                        className={`w-10 h-12 rounded-md flex flex-col items-center justify-center transition-colors cursor-pointer [font-variant-numeric:tabular-nums] ${
                          isEdge
                            ? "bg-tropical-coral text-white font-semibold"
                            : inRange
                              ? "bg-tropical-coral/15 text-foreground"
                              : "bg-muted/40 hover:bg-muted text-foreground"
                        }`}
                      >
                        <span className="text-[9px] opacity-70">
                          {d.toLocaleDateString("en-US", { weekday: "short" }).slice(0, 2)}
                        </span>
                        <span className="text-sm font-medium leading-tight">{d.getDate()}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>

        <DialogFooter className="mt-4 sm:items-center gap-2">
          <div className="flex-1 text-sm text-foreground [font-variant-numeric:tabular-nums] min-h-5">
            {start && end ? (
              <>
                <span className="font-semibold">{formatLongRange(start, end)}</span>
                <span className="text-muted-foreground ml-2">· {nights} {nights === 1 ? "night" : "nights"}</span>
              </>
            ) : start ? (
              <span className="text-muted-foreground">Pick your check-out date</span>
            ) : (
              <span className="text-muted-foreground">Pick your check-in date</span>
            )}
          </div>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            disabled={!start || !end}
            onClick={() => {
              if (start && end) {
                onConfirm(start, end)
                onOpenChange(false)
              }
            }}
          >
            Confirm
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
