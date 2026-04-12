import { useStream } from "@langchain/react";
import { useCallback } from "react";
import { Link } from "@tanstack/react-router";

import { ChatInput } from "@/components/ChatInput";
import { Conversation } from "@/components/Conversation";
import type { GenUIMessage } from "@/components/GenUIRenderer";

export function MainConversationPage() {
  const { messages, values, submit, isLoading } = useStream({
    apiUrl: window.location.origin,
    assistantId: "agent",
    messagesKey: "messages",
  });


  const uiMessages = (values?.ui ?? []) as (GenUIMessage & {
    message?: { id?: string };
  })[];

  const handleSubmit = useCallback(
    (text: string) => {
      if (!text.trim() || isLoading) return;
      submit({ messages: [{ type: "human", content: text }] });
    },
    [isLoading, submit]
  );

  return (
    <div className="grid h-[100dvh] grid-cols-1">
      <div className="absolute top-3 right-4 z-10">
        <Link
          to="/knowledge"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Staff →
        </Link>
      </div>
      <main className="grid grid-rows-[1fr_auto] min-h-0 bg-chat-bg">
        <Conversation
          messages={messages}
          uiMessages={uiMessages}
          isAiLoading={isLoading}
        />
        <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
      </main>
    </div>
  );
}
