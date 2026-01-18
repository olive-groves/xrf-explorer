import { appState } from "@/lib/appState";
import axios from "axios";

axios.defaults.withCredentials = true;

interface AuthResponse {
  authenticated: boolean;
  username: string;
  role: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  projects: any[];
}

/**
 * Attempts to log in the user using an existing session.
 */
export async function loginFromSession() {
  try {
    const response = await axios.get<AuthResponse>("/api/me");
    if (response.data.authenticated) {
      appState.user.username = response.data.username;
      appState.user.role = response.data.role;
      appState.user.projects = response.data.projects;
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {}
}
