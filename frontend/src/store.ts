import { create } from "zustand";

type SessionState = {
  accessToken: string | null;
  setAccessToken: (accessToken: string | null) => void;
};

export const useSessionStore = create<SessionState>((set) => ({
  accessToken: null,
  setAccessToken: (accessToken) => set({ accessToken }),
}));
