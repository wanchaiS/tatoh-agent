import { createContext, useContext } from "react"
import { useStream } from "@langchain/langgraph-sdk/react"

const ChatContext = createContext<ReturnType<typeof useStream> | null>(null)

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const stream = useStream({
    apiUrl: "http://localhost:8000",
    assistantId: "agent",
    messagesKey: "messages",
  })

  return <ChatContext.Provider value={stream}>{children}</ChatContext.Provider>
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error("useChat must be used within ChatProvider")
  return ctx
}
