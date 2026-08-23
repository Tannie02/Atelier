/**
 * ATELIER API Client with Authentication & Bearer Tokens
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
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Registration failed");
        }
        const data = await res.json();
        this.setToken(data.access_token);
        return data;
    },

    async login(email, password) {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Invalid email or password");
        }
        const data = await res.json();
        this.setToken(data.access_token);
        return data;
    },

    async getMe() {
        const res = await fetch(`${API_BASE}/api/auth/me`, {
            headers: this.getAuthHeaders()
        });
        if (!res.ok) throw new Error("Not authenticated");
        return await res.json();
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
        const headers = {};
        const token = this.getToken();
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`${API_BASE}/api/wardrobe/upload-preview`, {
            method: "POST",
            headers: headers,
            body: formData
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to analyze image");
        }
        return await res.json();
    },

    async saveItem(itemPayload) {
        const res = await fetch(`${API_BASE}/api/wardrobe/items`, {
            method: "POST",
            headers: this.getAuthHeaders(),
            body: JSON.stringify(itemPayload)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to save piece");
        }
        return await res.json();
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
        if (!res.ok) throw new Error("Failed to fetch wardrobe pieces");
        return await res.json();
    },

    async deleteItem(itemId) {
        const res = await fetch(`${API_BASE}/api/wardrobe/items/${itemId}`, {
            method: "DELETE",
            headers: this.getAuthHeaders()
        });
        if (!res.ok) throw new Error("Failed to delete piece");
        return await res.json();
    },

    async getWeather(city = null, lat = null, lon = null) {
        const params = new URLSearchParams();
        if (city) params.append("city", city);
        if (lat !== null) params.append("lat", lat);
        if (lon !== null) params.append("lon", lon);

        const res = await fetch(`${API_BASE}/api/weather/current?${params.toString()}`);
        if (!res.ok) throw new Error("Failed to fetch weather forecast");
        return await res.json();
    },

    async getRecommendations(reqData) {
        const res = await fetch(`${API_BASE}/api/recommend/outfits`, {
            method: "POST",
            headers: this.getAuthHeaders(),
            body: JSON.stringify(reqData)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to generate recommendations");
        }
        return await res.json();
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
        if (!res.ok) throw new Error("Failed to submit feedback");
        return await res.json();
    },

    async getFeedbackStats() {
        const res = await fetch(`${API_BASE}/api/feedback/stats`, {
            headers: this.getAuthHeaders()
        });
        if (!res.ok) throw new Error("Failed to fetch feedback stats");
        return await res.json();
    }
};
