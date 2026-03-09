import { ScrollArea } from "@/components/ui/scroll-area"

export function ChatWindow() {
  return (
    <ScrollArea className="flex-1">
      <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center px-4 py-8">
        <h1 className="text-2xl font-semibold text-foreground">Agent Chat</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Start a conversation with the hotel booking agent
        </p>
      </div>
    </ScrollArea>
  )
}
