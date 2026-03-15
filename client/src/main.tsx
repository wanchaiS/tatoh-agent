import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import './index.css'
import { routeTree } from './routeTree.gen'
import { queryClient } from './lib/queryClient'
import { ChatProvider } from './context/ChatContext'
import { AppToaster } from './components/Toaster'

const router = createRouter({
  routeTree,
  context: { queryClient },
  defaultPreload: 'intent',
  defaultPreloadDelay: 100,
  defaultErrorComponent: ({ error }) => (
    <div className="p-8 text-destructive">Error: {(error as Error).message}</div>
  ),
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ChatProvider>
        <RouterProvider router={router} context={{ queryClient }} />
        <AppToaster />
      </ChatProvider>
    </QueryClientProvider>
  </StrictMode>,
)
