import { Conversation } from '@/components/Conversation'
import type { GenUIMessage } from '@/components/GenUIRenderer'
import { useConversations } from '@/hooks/useConversations'
import { useThreadState } from '@/hooks/useThreadState'
import type { BaseMessage } from '@langchain/core/messages'
import { Copy } from 'lucide-react'
import { useState } from 'react'

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function ConversationsPage() {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const { data, isLoading: threadsLoading } = useConversations()
  const { data: threadState, isLoading: stateLoading } = useThreadState(selectedThreadId)

  const messages: BaseMessage[] = (threadState?.values?.messages ?? []) as BaseMessage[]
  const uiMessages = (threadState?.values?.ui ?? []) as (GenUIMessage & { message?: { id?: string } })[]

  function handleCopy() {
    if (!selectedThreadId) return
    navigator.clipboard.writeText(selectedThreadId)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left: thread list */}
      <div className="w-72 shrink-0 border-r flex flex-col overflow-hidden">
        <div className="px-4 py-3 border-b shrink-0">
          <h2 className="text-sm font-semibold">Conversations</h2>
          {data && (
            <p className="text-xs text-muted-foreground mt-0.5">{data.total} total</p>
          )}
        </div>
        <div className="flex-1 overflow-y-auto">
          {threadsLoading && (
            <p className="px-4 py-6 text-xs text-muted-foreground">Loading…</p>
          )}
          {data?.threads.map((t) => (
            <button
              key={t.thread_id}
              onClick={() => setSelectedThreadId(t.thread_id)}
              className={`w-full text-left px-4 py-3 border-b transition-colors ${
                selectedThreadId === t.thread_id
                  ? 'bg-primary/10 border-l-2 border-l-primary'
                  : 'hover:bg-muted/50'
              }`}
            >
              <p className="text-sm font-medium truncate">
                {t.title ?? 'Untitled'}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatRelativeTime(t.created_at)}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Right: message view */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selectedThreadId ? (
          <>
            {/* Header with thread ID chip */}
            <div className="px-4 py-3 border-b shrink-0 flex items-center gap-3">
              <span className="text-sm font-medium">
                {data?.threads.find((t) => t.thread_id === selectedThreadId)?.title ?? 'Untitled'}
              </span>
              <button
                onClick={handleCopy}
                title="Copy thread ID"
                className="flex items-center gap-1.5 rounded-md bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                <span>{selectedThreadId}</span>
                <Copy className="h-3 w-3 shrink-0" />
              </button>
              {copied && (
                <span className="text-xs text-muted-foreground">Copied</span>
              )}
            </div>
            <div className="flex-1 min-h-0 grid">
              {stateLoading ? (
                <p className="px-4 py-6 text-xs text-muted-foreground">Loading messages…</p>
              ) : (
                <Conversation
                  messages={messages}
                  uiMessages={uiMessages}
                  isAiLoading={false}
                />
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">Select a conversation</p>
          </div>
        )}
      </div>
    </div>
  )
}
