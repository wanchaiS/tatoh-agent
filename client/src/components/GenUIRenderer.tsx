import type { RoomData } from "./gen-ui-compopnents/RoomCard"
import { RoomInfo } from "./gen-ui-compopnents/RoomInfo"
import { RoomsList } from "./gen-ui-compopnents/RoomsList"
import { SuggestedAnswers } from "./gen-ui-compopnents/SuggestedAnswers"

type GenUIMessage =
  | { type: "ui"; id: string; name: "rooms_list";        props: { loading?: boolean; rooms: RoomData[] } }
  | { type: "ui"; id: string; name: "room_detail";       props: { loading?: boolean; room: RoomData | null } }
  | { type: "ui"; id: string; name: "suggested_answers"; props: { options: string[] } }

interface GenUIRendererProps {
  message: GenUIMessage
  onSubmitMessage: (text: string) => void
  isLoading: boolean
}

export type { GenUIMessage }

export function GenUIRenderer({
  message,
  onSubmitMessage,
  isLoading,
}: GenUIRendererProps) {
  switch (message.name) {
    case "rooms_list":
      return (
        <RoomsList
          rooms={message.props.rooms}
          loading={message.props.loading}
        />
      )
    case "room_detail": {
      const { room, loading } = message.props
      if (!loading && !room) return null
      return (
        <RoomInfo
          room={room}
          loading={loading}
        />
      )
    }
    case "suggested_answers": {
      const { options } = message.props
      if (!isLoading && !options.length) return null
      return (
        <SuggestedAnswers
          options={options}
          onSelect={onSubmitMessage}
          disabled={isLoading}
        />
      )
    }
    default:
      return null
  }
}
