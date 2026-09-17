import { create } from "zustand";
import { defaultSession, type Role, type Session } from "./api";

type SessionState = Session & { setRole: (role: Role) => void; setTenant: (tenantId: string) => void; setAccessToken: (accessToken: string | null) => void; signOut: () => void };
export const useSessionStore = create<SessionState>((set) => ({ ...defaultSession, setRole: (role) => set({ role }), setTenant: (tenantId) => set({ tenantId }), setAccessToken: (accessToken) => set({ accessToken }), signOut: () => set(defaultSession) }));
