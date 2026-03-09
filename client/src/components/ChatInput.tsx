import { useState, type FormEvent } from "react"
import { SendHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"

export function ChatInput() {
  const [message, setMessage] = useState("")

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return
    // TODO: send message to agent
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
        />
        <Button
          type="submit"
          size="icon"
          variant="default"
          className="h-8 w-8 shrink-0 rounded-lg"
          disabled={!message.trim()}
        >
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </form>
    </div>
  )
}
