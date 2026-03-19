import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { TokenResponse } from "../types";
const IS_SERVER = typeof window === "undefined";

let publicApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
publicApiUrl = publicApiUrl.replace(/\/+$/, "");
// If the configured URL doesn't already contain /api/services, append it so Nginx routing works reliably
if (!publicApiUrl.endsWith("/api/services")) {
    publicApiUrl += "/api/services";
}

let ssrApiUrl = process.env.SSR_API_URL || "http://localhost:8000";
ssrApiUrl = ssrApiUrl.replace(/\/+$/, "");
if (!ssrApiUrl.endsWith("/api/services")) {
    ssrApiUrl += "/api/services";
}

const API_BASE_URL = IS_SERVER ? ssrApiUrl : publicApiUrl;

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
    // Return relative without /api/services/ since the API_BASE_URL will already include it
    return `/${service}`;
};
export const getWebSocketUrl = (sessionId: string) => {
    return `wss://api.synthhire.me/ws/sessions/ws/${sessionId}`;
};
const api = { apiClient, getServiceUrl, getWebSocketUrl };
export default api;
