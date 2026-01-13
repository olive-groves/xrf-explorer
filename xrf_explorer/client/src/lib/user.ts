import { appState } from "@/lib/appState";
import axios from "axios";

axios.defaults.withCredentials = true;

interface AuthResponse {
  authenticated: boolean
  username: string
  role: string
  projects: any[]
}

export async function loginFromSession() {
    try {
        const response = await axios.get<AuthResponse>("/api/me");
        if (response.data.authenticated) {
            appState.user.username = response.data.username;
            appState.user.role = response.data.role;
            appState.user.projects = response.data.projects;
        }
    } catch(error: any) {}
}

