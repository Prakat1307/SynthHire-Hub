import { create } from "zustand";
import api from "@/src/lib/api";
const { apiClient, getServiceUrl } = api;
export interface User {
    id: string;
    email: string;
    full_name: string;
    role: string;
    account_type?: string;
    company_id?: string;
    avatar_url?: string;
    is_email_verified: boolean;
    created_at: string;
}
interface AuthState {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
    login: (email: string, password: string) => Promise<void>;
    register: (
        email: string,
        password: string,
        fullName: string,
    ) => Promise<void>;
    logout: () => Promise<void>;
    checkAuth: () => Promise<void>;
    updateAvatar: (avatarUrl: string) => void;
}
export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
    login: async (email: string, password: string) => {
        try {
            set({ isLoading: true, error: null });
            const authUrl = getServiceUrl("auth");
            const response = await apiClient.post(`/auth/login`, { email, password });
            const { access_token, refresh_token, user } = response.data;
            if (typeof window !== "undefined") {
                localStorage.setItem("access_token", access_token);
                localStorage.setItem("refresh_token", refresh_token);
                const savedAvatar = localStorage.getItem("synthhire_avatar");
                if (savedAvatar) user.avatar_url = savedAvatar;
            }
            set({
                user,
                accessToken: access_token,
                refreshToken: refresh_token,
                isAuthenticated: true,
                isLoading: false,
            });
        } catch (error: any) {
            console.error("Login Error:", error);
            set({
                error: error.response?.data?.detail || "Login failed",
                isLoading: false,
            });
            throw error;
        }
    },
    register: async (email: string, password: string, fullName: string) => {
        try {
            set({ isLoading: true, error: null });
            const response = await apiClient.post(`/auth/register`, {
                email,
                password,
                full_name: fullName,
            });
            const { access_token, refresh_token, user } = response.data;
            if (typeof window !== "undefined") {
                localStorage.setItem("access_token", access_token);
                localStorage.setItem("refresh_token", refresh_token);
            }
            set({
                user,
                accessToken: access_token,
                refreshToken: refresh_token,
                isAuthenticated: true,
                isLoading: false,
            });
        } catch (error: any) {
            set({
                error: error.response?.data?.detail || "Registration failed",
                isLoading: false,
            });
            throw error;
        }
    },
    logout: async () => {
        try {
            await apiClient.post(`/auth/logout`);
        } catch (e) {
            console.error(e);
        }
        if (typeof window !== "undefined") {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
        }
        set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
        });
    },
    checkAuth: async () => {
        if (typeof window === "undefined") return;
        const token = localStorage.getItem("access_token");
        if (!token) {
            set({ isLoading: false, isAuthenticated: false });
            return;
        }
        try {
            const response = await apiClient.get(`/auth/me`);
            const user = response.data;
            if (typeof window !== "undefined") {
                const savedAvatar = localStorage.getItem("synthhire_avatar");
                if (savedAvatar) user.avatar_url = savedAvatar;
            }
            set({
                user,
                accessToken: token,
                refreshToken: null,
                isAuthenticated: true,
                isLoading: false,
            });
        } catch (error: any) {
            console.log("Check Auth Failed:", error);
            const status = error.response?.status;
            if (status === 401 || status === 403) {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                set({
                    isLoading: false,
                    isAuthenticated: false,
                    user: null,
                    accessToken: null,
                });
            } else {
                set({ isLoading: false, isAuthenticated: false });
            }
        }
    },
    updateAvatar: (avatarUrl: string) => {
        set((state) => ({
            user: state.user ? { ...state.user, avatar_url: avatarUrl } : null,
        }));
        if (typeof window !== "undefined") {
            localStorage.setItem("synthhire_avatar", avatarUrl);
        }
    },
}));
