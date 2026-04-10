import { useState } from "react"
import type { RoomData } from "@/components/gen-ui-compopnents/RoomCard"
import { RoomCardVertical } from "./RoomCardVertical"
import { RoomDetailView } from "./RoomDetailView"
import { ResortMap } from "./ResortMap"
import { MAP_LARGE } from "./mockData"
import { List, MapPin } from "lucide-react"

interface DesignAProps {
  rooms: RoomData[]
}

type View = "list" | "map" | "detail"

export function DesignA({ rooms }: DesignAProps) {
  const [view, setView] = useState<View>("list")
  const [selectedRoom, setSelectedRoom] = useState<RoomData | null>(null)
  const [mapHighlight, setMapHighlight] = useState<number | null>(null)

  function handleSelectRoom(room: RoomData) {
    setSelectedRoom(room)
    setView("detail")
  }

  function handleMapPinClick(room: RoomData) {
    setMapHighlight(room.id)
    setSelectedRoom(room)
    setView("detail")
  }

  if (view === "detail" && selectedRoom) {
    return (
      <RoomDetailView
        room={selectedRoom}
        allRooms={rooms}
        onBack={() => {
          setView("list")
          setSelectedRoom(null)
        }}
      />
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="font-bold text-lg text-foreground">{rooms.length}</span>
          <span className="font-semibold text-base text-foreground ml-1.5">rooms available</span>
        </div>
        {/* Tab toggle */}
        <div className="flex rounded-lg border border-border bg-muted/50 p-0.5">
          <button
            onClick={() => setView("list")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all cursor-pointer ${
              view === "list"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <List className="h-3.5 w-3.5" />
            List
          </button>
          <button
            onClick={() => setView("map")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-all cursor-pointer ${
              view === "map"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <MapPin className="h-3.5 w-3.5" />
            Map
          </button>
        </div>
      </div>

      {view === "list" ? (
        /* Vertical card stack */
        <div className="flex flex-col gap-2.5">
          {rooms.map((room, i) => (
            <div key={room.id} className="animate-card-enter" style={{ animationDelay: `${i * 60}ms` }}>
              <RoomCardVertical room={room} onSelect={handleSelectRoom} />
            </div>
          ))}
        </div>
      ) : (
        /* Map view */
        <div className="flex flex-col gap-3">
          <ResortMap
            rooms={rooms}
            mapSrc={MAP_LARGE}
            selectedRoomId={mapHighlight}
            onSelectRoom={handleMapPinClick}
          />
          <p className="text-xs text-muted-foreground text-center">Tap a pin to view room details</p>
        </div>
      )}
    </div>
  )
}
