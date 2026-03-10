import { useEffect, useRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useChat } from "@/context/ChatContext"
import { UIMessageRenderer } from "./UIMessageRenderer"

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-1 rounded-xl bg-muted px-4 py-3">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="inline-block h-2 w-2 rounded-full bg-muted-foreground/60 animate-bounce"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  )
}

export function ChatWindow() {
  const { messages, isLoading, values, submit } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)

  const uiMessages = (values?.ui ?? []) as Array<{
    type: "ui"
    id: string
    name: string
    props: Record<string, unknown>
  }>

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading, uiMessages.length])

  const handleSubmitMessage = (text: string) => {
    submit(
      { messages: [{ type: "human", content: text }] },
      { 
        streamMode: ["values", "messages"],
        streamSubgraphs: true
      }
    )
  }

  const visibleMessages = messages.filter(
    (m) =>
      (m.type === "human" || m.type === "ai") &&
      typeof m.content === "string" &&
      m.content.trim() !== ""
  )

  if (visibleMessages.length === 0 && uiMessages.length === 0) {
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
            className={`flex animate-in fade-in duration-300 ${m.type === "human" ? "justify-end" : "justify-start"}`}
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
        {uiMessages.map((uiMsg) => (
          <div key={uiMsg.id} className="flex justify-start animate-in fade-in duration-300">
            <div className="w-full max-w-[90%]">
              <UIMessageRenderer
                message={uiMsg}
                onSubmitMessage={handleSubmitMessage}
                isLoading={isLoading}
              />
            </div>
          </div>
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}
