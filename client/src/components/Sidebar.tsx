import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

export function Sidebar() {
  const handleNewChat = () => {
    window.location.reload()
  }

  return (
    <div className="flex h-full flex-col">
      <div className="p-4">
        <Button
          variant="outline"
          className="w-full justify-start gap-2"
          onClick={handleNewChat}
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>
      <Separator />
      <ScrollArea className="flex-1 px-4 py-2">
        <p className="text-sm text-muted-foreground py-4 text-center">
          No conversations yet
        </p>
      </ScrollArea>
    </div>
  )
}
