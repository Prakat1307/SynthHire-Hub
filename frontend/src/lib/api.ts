import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { TokenResponse } from "../types";
const IS_SERVER = typeof window === "undefined";
const API_BASE_URL = IS_SERVER
    ? process.env.SSR_API_URL || "http:
    : process.env.NEXT_PUBLIC_API_URL || "http:
export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: { "Content-Type": "application/json" },
    withCredentials: false,
});
apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        if (typeof window !== "undefined") {
            const token = localStorage.getItem("access_token");
            if (token && config.headers) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error: AxiosError) => Promise.reject(error),
);
apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
            _retry?: boolean;
            _retryCount?: number;
        };
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                const refreshToken = localStorage.getItem("refresh_token") || "";
                const { data } = await axios.post<TokenResponse>(
                    `${API_BASE_URL}/auth/refresh`,
                    { refresh_token: refreshToken },
                    { withCredentials: false },
                );
                if (typeof window !== "undefined") {
                    localStorage.setItem("access_token", data.access_token);
                    if (data.refresh_token) {
                        localStorage.setItem("refresh_token", data.refresh_token);
                    }
                }
                if (originalRequest.headers) {
                    originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
                }
                return apiClient(originalRequest);
            } catch (refreshError) {
                if (typeof window !== "undefined") {
                    localStorage.removeItem("access_token");
                    localStorage.removeItem("refresh_token");
                    window.location.href = "/login";
                }
                return Promise.reject(refreshError);
            }
        }
        const status = error.response?.status;
        const isTransientError =
            status === 502 || status === 503 || error.code === "ERR_NETWORK";
        if (isTransientError) {
            originalRequest._retryCount = originalRequest._retryCount || 0;
            if (originalRequest._retryCount < 30) {
                originalRequest._retryCount++;
                await new Promise((resolve) => setTimeout(resolve, 2000));
                return apiClient(originalRequest);
            }
        }
        return Promise.reject(error);
    },
);
export const getServiceUrl = (
    service:
        | "auth"
        | "session"
        | "speech"
        | "assessment"
        | "code"
        | "analytics"
        | "coaching"
        | "report"
        | "certification"
        | "learning"
        | "company"
        | "shortlisting"
        | "matching"
        | "job"
        | "user"
        | "onboarding"
        | "resume",
) => {
    return `/api/services/${service}`;
};
export const getWebSocketUrl = (sessionId: string) => {
    const base = process.env.NEXT_PUBLIC_WS_URL || "ws:
    return `${base}/ws/sessions/ws/${sessionId}`;
};
const api = { apiClient, getServiceUrl, getWebSocketUrl };
export default api;
