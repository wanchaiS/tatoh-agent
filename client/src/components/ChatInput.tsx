import { useState, type FormEvent } from "react"
import { SendHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useChat } from "@/context/ChatContext"

export function ChatInput() {
  const [message, setMessage] = useState("")
  const { submit, isLoading } = useChat()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!message.trim() || isLoading) return
    submit(
      { messages: [{ type: "human", content: message }] },
      { 
        streamMode: ["values", "messages"],
        streamSubgraphs: true
      }
    )
    setMessage("")
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-4">
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 rounded-xl border bg-muted/50 px-4 py-2"
      >
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          disabled={isLoading}
        />
        <Button
          type="submit"
          size="icon"
          variant="default"
          className="h-8 w-8 shrink-0 rounded-lg"
          disabled={!message.trim() || isLoading}
        >
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </form>
    </div>
  )
}
