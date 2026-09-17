export type Role = "HR Admin" | "Recruiter" | "Viewer";
export type Session = { tenantId: string; role: Role; accessToken: string | null };
export const defaultSession: Session = { tenantId: "default", role: "HR Admin", accessToken: null };

export async function request<T>(path: string, session: Session = defaultSession, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("X-Tenant-ID", session.tenantId);
  headers.set("X-Role", session.role);
  if (session.accessToken) headers.set("Authorization", `Bearer ${session.accessToken}`);
  const response = await fetch(path, { ...init, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Request failed");
  return body as T;
}

export function validateUpload(file: File | null): string | null {
  if (!file) return "Choose a PDF, DOCX, or TXT file.";
  const extensions = ["pdf", "docx", "txt"];
  const extension = file.name.toLowerCase().split(".").pop();
  if (!extensions.includes(extension ?? "")) return "Only PDF, DOCX, and TXT files are supported.";
  if (file.size === 0 || file.size > 10 * 1024 * 1024) return "Files must be between 1 byte and 10 MB.";
  return null;
}

export function dashboardMetrics(resumes: Array<{ status?: string }>, jobs: unknown[], matches: unknown[]) {
  return { employees: resumes.filter((resume) => resume.status === "ready").length, jobs: jobs.length, matches: matches.length, processing: resumes.filter((resume) => resume.status === "processing" || resume.status === "queued").length };
}