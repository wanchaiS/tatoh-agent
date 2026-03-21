import { Fragment, useEffect, useRef } from "react";

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
  );
}

interface ConversationProps {
  messages: any[];
  uiMessages: (GenUIMessage & { message?: { id?: string } })[];
  isLoading: boolean;
  onSubmitFromUI: (text: string) => void;
}

export function Conversation({
  messages,
  uiMessages,
  isLoading,
  onSubmitFromUI,
}: ConversationProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, uiMessages.length]);

  if (messages.length === 0 && uiMessages.length === 0) {
    return (
      <ScrollArea className="min-h-0">
        <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center px-4 py-8">
          <h1 className="text-2xl font-semibold text-foreground">
            Welcome to Tatoh Resort
          </h1>
        </div>
      </ScrollArea>
    );
  }

  return (
    <ScrollArea className="min-h-0">
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-8">
        {messages
          .filter(
            (msg: any) =>
              msg.type === "human" || (msg.type === "ai" && msg.content)
          )
          .map((message: any) => (
            <Fragment key={message.id}>
              <div
                className={`flex animate-in fade-in duration-300 ${message.type === "human" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-xl px-4 py-2 text-sm whitespace-pre-wrap break-words min-w-0 ${message.type === "human" ? "bg-tropical-ocean text-white" : "bg-tropical-sand/40 text-foreground"}`}
                >
                  {message.content as string}
                </div>
              </div>
              {uiMessages
                .filter((ui) => ui.metadata?.message_id === message.id)
                .map((ui: any) => (
                  <GenUIRenderer
                    key={ui.id}
                    message={ui}
                    onSubmitMessage={onSubmitFromUI}
                    isLoading={isLoading}
                  />
                ))}
            </Fragment>
          ))}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
