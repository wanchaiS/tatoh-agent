import { memo } from "react"

import type { RoomCardData } from "./gen-ui-compopnents/RoomCard"
import { SearchResults } from "./gen-ui-compopnents/SearchResults"

type MapData = {
  src: string
  pins: Record<number, { x: number; y: number }>
}

type SearchRange = {
  start: string
  end: string
}

type GenUIMessage =
  { type: "ui"; id: string; name: "search_results"; metadata: { message_id: string }; props: { rooms: RoomCardData[]; map: MapData; search_range: SearchRange } }


interface GenUIRendererProps {
  message: GenUIMessage
}

export type { GenUIMessage }

export const GenUIRenderer = memo(function GenUIRenderer({
  message,
}: GenUIRendererProps) {
  switch (message.name) {
    case "search_results":
      return (
        <SearchResults
          rooms={message.props.rooms}
          map={message.props.map}
          search_range={message.props.search_range}
        />
      )
    default:
      return null
  }
})
