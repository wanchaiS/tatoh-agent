import { RoomsList } from "./ui-messages/RoomsList"
import { RoomDetail } from "./ui-messages/RoomDetail"
import { SuggestedAnswers } from "./ui-messages/SuggestedAnswers"
import type { RoomData } from "./ui-messages/RoomCard"

interface UIMessage {
  type: "ui"
  id: string
  name: string
  props: Record<string, unknown>
}

interface UIMessageRendererProps {
  message: UIMessage
  onSubmitMessage: (text: string) => void
  isLoading: boolean
}

export function UIMessageRenderer({
  message,
  onSubmitMessage,
  isLoading,
}: UIMessageRendererProps) {
  const props = message.props as Record<string, unknown>
  const loading = props.loading as boolean | undefined

  switch (message.name) {
    case "rooms_list":
      return (
        <RoomsList
          rooms={(props.rooms as never[]) ?? []}
          loading={loading}
          onAskAI={(room: RoomData) => onSubmitMessage(`ดูรายละเอียดห้อง ${room.room_name}`)}
        />
      )
    case "room_detail":
      return (
        <RoomDetail
          room={(props.room as never) ?? null}
          loading={loading}
        />
      )
    case "suggested_answers":
      return (
        <SuggestedAnswers
          options={(props.options as string[]) ?? []}
          onSelect={onSubmitMessage}
          disabled={isLoading}
        />
      )
    default:
      return null
  }
}
