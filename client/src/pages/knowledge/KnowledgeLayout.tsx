import { Outlet } from '@tanstack/react-router'
import { KnowledgeNav } from './KnowledgeNav'

export function KnowledgeLayout() {
  return (
    <div className="flex h-screen bg-background">
      {/* Left sidebar navigation */}
      <KnowledgeNav />

      {/* Right pane - content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
