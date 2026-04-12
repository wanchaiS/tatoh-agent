import { SendHorizontal } from "lucide-react";
import { useState, type SubmitEvent } from "react";

import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSubmit: (message: string) => void;
  isLoading: boolean;
}

export function ChatInput({ onSubmit, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;
    onSubmit(message);
    setMessage("");
  };

  return (
    <div
      className="mx-auto w-full max-w-3xl px-4"
      style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}
    >
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 rounded-xl border bg-tropical-sand/20 px-4 py-2"
      >
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask away..."
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
    </div>
  );
}
