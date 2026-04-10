import { uiMessageReducer } from "@langchain/langgraph-sdk/react-ui";
import { useStream } from "@langchain/react";
import { useCallback } from "react";

import { ChatInput } from "@/components/ChatInput";
import { Conversation } from "@/components/Conversation";
import type { GenUIMessage } from "@/components/GenUIRenderer";

export function MainConversationPage() {
  const { messages, values, submit, isLoading } = useStream({
    apiUrl: window.location.origin,
    assistantId: "agent",
    messagesKey: "messages",
    
    onCustomEvent: (event, options) => {
      options.mutate((prev: any) => {
        const ui = uiMessageReducer((prev.ui as any[]) || [], event as any);
        return { ...prev, ui };
      });
    },
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
      <main className="grid grid-rows-[1fr_auto] min-h-0 bg-chat-bg">
        <Conversation
          messages={messages}
          uiMessages={uiMessages}
          isLoading={isLoading}
          onSubmitFromUI={handleSubmit}
        />
        <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
      </main>
    </div>
  );
}
