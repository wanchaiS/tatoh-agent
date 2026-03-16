import { MainThread } from "@/components/MainThread"

function App() {

  return (
    <div className="grid h-[100dvh] grid-cols-1">
      <main className="grid grid-rows-[1fr_auto] min-h-0 bg-chat-bg">
        <MainThread />
      </main>
    </div>
  )
}

export default App
