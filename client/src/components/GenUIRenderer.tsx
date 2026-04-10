import { memo } from "react"
import type { RoomData } from "./gen-ui-compopnents/RoomCard"
import { SearchResultsList } from "./gen-ui-compopnents/SearchResultsList"

type GenUIMessage =
   { type: "ui"; id: string; name: "search_results";  props: { rooms: RoomData[] } }


interface GenUIRendererProps {
  message: GenUIMessage
  onSubmitMessage: (text: string) => void
  isLoading: boolean
}

export type { GenUIMessage }

export const GenUIRenderer = memo(function GenUIRenderer({
  message,
  onSubmitMessage,
  isLoading,
}: GenUIRendererProps) {
  switch (message.name) {
    case "search_results":
      return (
        <SearchResultsList rooms={message.props.rooms} />
      )
    default:
      return null
  }
})
