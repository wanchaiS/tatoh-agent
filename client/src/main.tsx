import { QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AppToaster } from './components/Toaster'
import './index.css'
import { queryClient } from './lib/queryClient'
import { routeTree } from './routeTree.gen'

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
        <RouterProvider router={router} context={{ queryClient }} />
        <AppToaster />
    </QueryClientProvider>
  </StrictMode>,
)
