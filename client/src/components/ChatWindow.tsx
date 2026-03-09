import { useEffect, useRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useChat } from "@/context/ChatContext"

export function ChatWindow() {
  const { messages, isLoading } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const visibleMessages = messages.filter(
    (m) =>
      (m.type === "human" || m.type === "ai") &&
      typeof m.content === "string" &&
      m.content.trim() !== ""
  )

  if (visibleMessages.length === 0) {
    return (
      <ScrollArea className="flex-1">
        <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center px-4 py-8">
          <h1 className="text-2xl font-semibold text-foreground">
            Agent Chat
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Start a conversation with the hotel booking agent
          </p>
        </div>
      </ScrollArea>
    )
  }

  return (
    <ScrollArea className="flex-1">
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-8">
        {visibleMessages.map((m, i) => (
          <div
            key={m.id ?? i}
            className={`flex ${m.type === "human" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-xl px-4 py-2 text-sm whitespace-pre-wrap ${
                m.type === "human"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground"
              }`}
            >
              {m.content as string}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-xl bg-muted px-4 py-2 text-sm text-muted-foreground">
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}
