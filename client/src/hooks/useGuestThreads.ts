import { useQuery, useQueryClient } from "@tanstack/react-query";

export interface GuestThread {
  thread_id: string;
  title: string | null;
  created_at: string;
}

export const guestThreadsKey = ["guest-threads"] as const;

export function useGuestThreads() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: guestThreadsKey,
    queryFn: async (): Promise<GuestThread[]> => {
      const res = await fetch("/api/threads", { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch threads");
      return res.json();
    },
  });

  return {
    threads: query.data ?? [],
    isLoading: query.isLoading,
    refetch: () =>
      queryClient.invalidateQueries({ queryKey: guestThreadsKey }),
  };
}
