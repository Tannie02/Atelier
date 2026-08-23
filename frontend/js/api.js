/**
 * ATELIER API Client with Authentication, Bearer Tokens & Robust Error Handling
 */

const API_BASE = "";

const API = {
    getToken() {
        return localStorage.getItem("atelier_auth_token") || null;
    },

    setToken(token) {
        if (token) {
            localStorage.setItem("atelier_auth_token", token);
        } else {
            localStorage.removeItem("atelier_auth_token");
        }
    },

    getAuthHeaders(contentType = "application/json") {
        const headers = {};
        if (contentType) {
            headers["Content-Type"] = contentType;
        }
        const token = this.getToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        return headers;
    },

    async handleResponse(res, defaultErrMsg = "Request failed") {
        if (!res.ok) {
            let errorMsg = defaultErrMsg;
            try {
                const errData = await res.json();
                errorMsg = errData.detail || defaultErrMsg;
            } catch (e) {
                if (res.status === 401) {
                    errorMsg = "Please sign in or create an account.";
                } else if (res.status === 413) {
                    errorMsg = "Image is too large. Please upload a smaller photo.";
                } else {
                    errorMsg = `Server response error (${res.status}). Please retry.`;
                }
            }
            if (res.status === 401) {
                this.logout();
                if (typeof renderAuthUI === "function") renderAuthUI(null);
            }
            throw new Error(errorMsg);
        }
        return await res.json();
    },

    // --- Authentication ---
    async register(email, fullName, password, stylePreference = "Contemporary Minimalist") {
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email,
                full_name: fullName,
                password,
                style_preference: stylePreference
            })
        });
        const data = await this.handleResponse(res, "Registration failed");
        this.setToken(data.access_token);
        return data;
    },

    async login(email, password) {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await this.handleResponse(res, "Invalid email or password");
        this.setToken(data.access_token);
        return data;
    },

    async getMe() {
        const res = await fetch(`${API_BASE}/api/auth/me`, {
            headers: this.getAuthHeaders()
        });
        return await this.handleResponse(res, "Not authenticated");
    },

    logout() {
        this.setToken(null);
    },

    // --- System & Wardrobe ---
    async checkHealth() {
        try {
            const res = await fetch(`${API_BASE}/api/health`);
            return await res.json();
        } catch (e) {
            return { status: "offline" };
        }
    },

    async uploadPreview(file) {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`${API_BASE}/api/wardrobe/upload-preview`, {
            method: "POST",
            body: formData
        });
        return await this.handleResponse(res, "Failed to analyze garment");
    },

    async saveItem(itemPayload) {
        const res = await fetch(`${API_BASE}/api/wardrobe/items`, {
            method: "POST",
            headers: this.getAuthHeaders(),
            body: JSON.stringify(itemPayload)
        });
        return await this.handleResponse(res, "Failed to save piece to closet");
    },

    async getItems(filters = {}) {
        const params = new URLSearchParams();
        if (filters.category) params.append("category", filters.category);
        if (filters.subcategory) params.append("subcategory", filters.subcategory);
        if (filters.color) params.append("color", filters.color);

        const url = `${API_BASE}/api/wardrobe/items?${params.toString()}`;
        const res = await fetch(url, {
            headers: this.getAuthHeaders()
        });
        return await this.handleResponse(res, "Failed to fetch closet pieces");
    },

    async deleteItem(itemId) {
        const res = await fetch(`${API_BASE}/api/wardrobe/items/${itemId}`, {
            method: "DELETE",
            headers: this.getAuthHeaders()
        });
        return await this.handleResponse(res, "Failed to delete piece");
    },

    async getWeather(city = null, lat = null, lon = null) {
        const params = new URLSearchParams();
        if (city) params.append("city", city);
        if (lat !== null) params.append("lat", lat);
        if (lon !== null) params.append("lon", lon);

        const res = await fetch(`${API_BASE}/api/weather/current?${params.toString()}`);
        return await this.handleResponse(res, "Failed to fetch weather");
    },

    async getRecommendations(reqData) {
        const res = await fetch(`${API_BASE}/api/recommend/outfits`, {
            method: "POST",
            headers: this.getAuthHeaders(),
            body: JSON.stringify(reqData)
        });
        return await this.handleResponse(res, "Failed to generate recommendations");
    },

    async submitFeedback(outfitId, rating, reason = "") {
        const res = await fetch(`${API_BASE}/api/feedback`, {
            method: "POST",
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
                outfit_id: outfitId,
                rating: rating,
                feedback_reason: reason
            })
        });
        return await this.handleResponse(res, "Failed to submit feedback");
    },

    async getFeedbackStats() {
        const res = await fetch(`${API_BASE}/api/feedback/stats`, {
            headers: this.getAuthHeaders()
        });
        return await this.handleResponse(res, "Failed to fetch feedback stats");
    }
};
