import { useStream } from "@langchain/react";
import { useCallback } from "react";

import { ChatInput } from "@/components/ChatInput";
import { Conversation } from "@/components/Conversation";
import type { GenUIMessage } from "@/components/GenUIRenderer";
import { ThreadSidebar } from "@/components/ThreadSidebar";
import { useActiveThread } from "@/hooks/useActiveThread";
import { useGuestThreads } from "@/hooks/useGuestThreads";

export function MainConversationPage() {
  const { threadId, setThreadId } = useActiveThread();
  const { threads, refetch } = useGuestThreads();
  const { messages, values, submit, isLoading, switchThread } = useStream({
    apiUrl: window.location.origin,
    assistantId: "agent",
    messagesKey: "messages",
    threadId: threadId ?? undefined,
    onThreadId: (newThreadId) => {
      setThreadId(newThreadId);
      refetch();
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

  const handleSelectThread = useCallback(
    (id: string) => {
      setThreadId(id);
      switchThread(id);
    },
    [setThreadId, switchThread]
  );

  const handleNewChat = useCallback(async () => {
    const res = await fetch("/threads", {
      method: "POST",
      credentials: "include",
    });
    const { thread_id } = await res.json();
    setThreadId(thread_id);
    switchThread(thread_id);
    refetch();
  }, [setThreadId, switchThread, refetch]);

  return (
    <div className="flex h-[100dvh]">
      <ThreadSidebar
        threads={threads}
        activeThreadId={threadId}
        onSelectThread={handleSelectThread}
        onNewChat={handleNewChat}
      />
      <main className="flex-1 grid grid-rows-[1fr_auto] min-h-0 bg-chat-bg relative">
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
