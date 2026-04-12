import { Link, useRouter } from "@tanstack/react-router";
import { BookOpen, LogOut, Menu, Plus } from "lucide-react";
import { useState } from "react";

import type { GuestThread } from "@/hooks/useGuestThreads";
import { logout } from "@/lib/auth";
import { useAuthStore } from "@/stores/authStore";

import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

interface ThreadSidebarProps {
  threads: GuestThread[];
  activeThreadId: string | null;
  onSelectThread: (threadId: string) => void;
  onNewChat: () => void;
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function SidebarContent({
  threads,
  activeThreadId,
  onSelectThread,
  onNewChat,
  onItemClick,
}: ThreadSidebarProps & { onItemClick?: () => void }) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  console.log(user);
  async function handleLogout() {
    await logout();
    useAuthStore.getState().clearUser();
    router.navigate({ to: "/" });
  }

  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="border-b border-sidebar-border px-4 py-4">
        <button
          onClick={() => {
            onNewChat();
            onItemClick?.();
          }}
          className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-sidebar-accent"
        >
          <Plus className="h-4 w-4" />
          New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {threads.map((t) => (
          <button
            key={t.thread_id}
            onClick={() => {
              onSelectThread(t.thread_id);
              onItemClick?.();
            }}
            className={`flex w-full flex-col items-start rounded-md px-3 py-2 text-sm transition-colors text-left ${
              t.thread_id === activeThreadId
                ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                : "text-sidebar-foreground hover:bg-sidebar-accent/50"
            }`}
          >
            <span className="truncate w-full">
              {t.title || "New conversation"}
            </span>
            <span className="text-xs text-muted-foreground mt-0.5">
              {formatRelativeTime(t.created_at)}
            </span>
          </button>
        ))}
      </div>

        <div className="border-t border-sidebar-border p-2 space-y-0.5">
          <Link
            to="/knowledge"
            onClick={() => onItemClick?.()}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-sidebar-accent"
          >
            <BookOpen className="h-4 w-4" />
            Knowledge
          </Link>
          {user && <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-sidebar-accent"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>}
        </div>
    </div>
  );
}

export function ThreadSidebar(props: ThreadSidebarProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Desktop: always visible */}
      <aside className="hidden md:block w-70 border-r border-sidebar-border shrink-0">
        <SidebarContent {...props} />
      </aside>

      {/* Mobile: sheet trigger + drawer */}
      <div className="md:hidden absolute top-3 left-3 z-10">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <button className="rounded-md p-2 text-muted-foreground hover:text-foreground transition-colors">
              <Menu className="h-5 w-5" />
            </button>
          </SheetTrigger>
          <SheetContent side="left" className="w-72 p-0">
            <SheetTitle className="sr-only">Chats</SheetTitle>
            <SidebarContent {...props} onItemClick={() => setOpen(false)} />
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
