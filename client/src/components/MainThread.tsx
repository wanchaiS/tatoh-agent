import { useStream } from "@langchain/langgraph-sdk/react";
import { uiMessageReducer } from "@langchain/langgraph-sdk/react-ui";
import { SendHorizontal } from "lucide-react";
import { Fragment, useEffect, useRef, useState, type SubmitEvent } from "react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

import { GenUIRenderer, type GenUIMessage } from "./GenUIRenderer";

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

export function MainThread() {
    const [message, setMessage] = useState("")
    const {messages, values, submit, isLoading} = useStream({
    apiUrl: window.location.origin,
    assistantId: "agent",
    messagesKey: "messages",
    onCustomEvent: (event, options) => {
      options.mutate((prev: any) => {
        const ui = uiMessageReducer((prev.ui as any[]) || [], event as any);
        return { ...prev, ui };
      });
    },
  })
  
  const bottomRef = useRef<HTMLDivElement>(null)
  const uiMessages = (values?.ui ?? []) as (GenUIMessage & { message?: { id?: string } })[]

  const handleSubmitFromUI = (text: string) => {
    if (!text.trim() || isLoading) return
    submit(
      { messages: [{ type: "human", content: text }] },
      {
        streamMode: ["values", "messages"],
        streamSubgraphs: true,
      }
    )
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages.length, uiMessages.length])

  const handleSubmitMessage = (e: SubmitEvent<HTMLFormElement>) => {
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

  function getConversation() {
    if (messages.length === 0 && uiMessages.length === 0) {
    return (
      <ScrollArea className="min-h-0">
        <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center px-4 py-8">
          <h1 className="text-2xl font-semibold text-foreground">
            Welcome to Tatoh Resort
          </h1>
        </div>
      </ScrollArea>
    )
  }

    console.log("messages", messages)
    console.log("uiMessages", uiMessages)

    return (
    <ScrollArea className="min-h-0">
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-8">
        {messages
          .filter((msg: any) => msg.type === "human" || (msg.type === "ai" && msg.content))
          .map((message: any) => (
          <Fragment key={message.id}>

              <div className={`flex animate-in fade-in duration-300 ${message.type === "human" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-xl px-4 py-2 text-sm whitespace-pre-wrap break-words min-w-0 ${message.type === "human" ? "bg-tropical-ocean text-white" : "bg-tropical-sand/40 text-foreground"}`}>
                  {message.content as string}
                </div>
              </div>
               {uiMessages.filter(ui => ui.metadata?.message_id === message.id).map((ui: any) => (
              <GenUIRenderer key={ui.id} message={ui} onSubmitMessage={handleSubmitFromUI} isLoading={isLoading} />
            ))}
          </Fragment>
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
  }

  return <>
  {getConversation()}
  {/* Chat input */}
  <div
      className="mx-auto w-full max-w-3xl px-4"
      style={{ paddingBottom: 'max(1rem, env(safe-area-inset-bottom))' }}
    >
      <form
        onSubmit={handleSubmitMessage}
        className="flex items-center gap-2 rounded-xl border bg-tropical-sand/20 px-4 py-2"
      >
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about rooms, views, availability..."
          className="flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground"
          disabled={isLoading}
        />
        <Button
          type="submit"
          size="icon"
          variant="default"
          className="h-11 w-11 shrink-0 rounded-lg"
          disabled={!message.trim() || isLoading}
        >
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </form>
    </div></>



  
}
