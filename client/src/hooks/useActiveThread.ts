import { useCallback, useState } from "react";

const STORAGE_KEY = "tatoh_active_thread";

export function useActiveThread() {
  const [threadId, setThreadIdState] = useState<string | null>(
    () => localStorage.getItem(STORAGE_KEY)
  );

  const setThreadId = useCallback((id: string | null) => {
    if (id) {
      localStorage.setItem(STORAGE_KEY, id);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
    setThreadIdState(id);
  }, []);

  return { threadId, setThreadId };
}
