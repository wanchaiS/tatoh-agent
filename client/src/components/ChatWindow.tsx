import { useEffect, useRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useChat } from "@/context/ChatContext"
import { UIMessageRenderer } from "./UIMessageRenderer"

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-1 rounded-xl bg-tropical-sand/40 px-4 py-3">
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

  // Build unified timeline: UI messages are appended after the last AI message
  type TimelineItem =
    | { kind: "message"; message: (typeof visibleMessages)[number]; index: number }
    | { kind: "ui"; uiMsg: (typeof uiMessages)[number] }

  const timelineItems: TimelineItem[] = visibleMessages.map((m, i) => ({
    kind: "message",
    message: m,
    index: i,
  }))

  // Find the index of the last AI message and insert UI messages after it
  const lastAiIdx = [...visibleMessages].reverse().findIndex((m) => m.type === "ai")
  const insertAfter = lastAiIdx === -1 ? visibleMessages.length - 1 : visibleMessages.length - 1 - lastAiIdx

  if (uiMessages.length > 0 && timelineItems.length > 0) {
    timelineItems.splice(
      insertAfter + 1,
      0,
      ...uiMessages.map((uiMsg) => ({ kind: "ui" as const, uiMsg }))
    )
  } else if (uiMessages.length > 0) {
    uiMessages.forEach((uiMsg) => timelineItems.push({ kind: "ui", uiMsg }))
  }

  if (visibleMessages.length === 0 && uiMessages.length === 0) {
    return (
      <ScrollArea className="min-h-0">
        <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center px-4 py-8">
          <h1 className="text-2xl font-semibold text-foreground">
            How can I help you?
          </h1>
        </div>
      </ScrollArea>
    )
  }

  return (
    <>
    <ScrollArea className="min-h-0">
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-8">
        {timelineItems.map((item) => {
          if (item.kind === "message") {
            const m = item.message
            return (
              <div
                key={m.id ?? item.index}
                className={`flex animate-in fade-in duration-300 ${m.type === "human" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-xl px-4 py-2 text-sm whitespace-pre-wrap break-words min-w-0 ${
                    m.type === "human"
                      ? "bg-tropical-ocean text-white"
                      : "bg-tropical-sand/40 text-foreground"
                  }`}
                >
                  {m.content as string}
                </div>
              </div>
            )
          } else {
            const uiMsg = item.uiMsg
            return (
              <div key={uiMsg.id} className="flex justify-start animate-in fade-in duration-300">
                <div className="w-full">
                  <UIMessageRenderer
                    message={uiMsg}
                    onSubmitMessage={handleSubmitMessage}
                    isLoading={isLoading}
                  />
                </div>
              </div>
            )
          }
        })}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
    </>
  )
}
