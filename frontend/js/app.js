/**
 * ATELIER — AI Personal Stylist & Smart Closet
 * Front-end Application Controller with User Authentication
 */

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

// Application State
const state = {
    currentTab: "wardrobe",
    currentUser: null,
    authMode: "login", // 'login' or 'register'
    items: [],
    selectedCategoryFilter: "all",
    selectedOccasion: "college",
    weather: null,
    recommendations: [],
    previewItem: null,
    feedbackStats: null,
    isGenerating: false,
    isUploading: false
};

// Editorial Look Titles
const LOOK_TITLES = [
    "The Minimalist Classic",
    "The Tailored Urban",
    "The Effortless Casual",
    "The Monochrome Statement",
    "The Contemporary Smart",
    "The Elevated Everyday",
    "The Sharp Metropolitan",
    "The Relaxed Luxe"
];

async function initApp() {
    setupTabNavigation();
    setupUploadHandlers();
    setupRecommenderControls();
    
    // Check Authentication Status
    await checkCurrentUser();
    
    // Load initial data
    await loadWardrobeItems();
    await loadWeather();
    await loadFeedbackStats();
}

function setupTabNavigation() {
    const navButtons = document.querySelectorAll(".nav-btn");
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    state.currentTab = tabName;
    
    // Update button styles
    document.querySelectorAll(".nav-btn").forEach(b => {
        if (b.dataset.tab === tabName) {
            b.classList.add("bg-zinc-900", "text-white", "shadow-xs");
            b.classList.remove("text-zinc-600", "hover:bg-white/60");
        } else {
            b.classList.remove("bg-zinc-900", "text-white", "shadow-xs");
            b.classList.add("text-zinc-600", "hover:bg-white/60");
        }
    });

    // Update section visibility
    document.querySelectorAll(".tab-section").forEach(sec => {
        sec.classList.add("hidden");
    });
    
    const activeSec = document.getElementById(`section-${tabName}`);
    if (activeSec) {
        activeSec.classList.remove("hidden");
    }

    if (tabName === "wardrobe") {
        loadWardrobeItems();
    } else if (tabName === "analytics") {
        loadFeedbackStats();
        renderAnalytics();
    }
}

/* =========================================================================
   1. User Authentication & Profile
   ========================================================================= */

async function checkCurrentUser() {
    try {
        const user = await API.getMe();
        state.currentUser = user;
        renderAuthUI(user);
    } catch (e) {
        state.currentUser = null;
        renderAuthUI(null);
    }
}

function renderAuthUI(user) {
    const loggedOutDiv = document.getElementById("auth-logged-out");
    const loggedInDiv = document.getElementById("auth-logged-in");
    
    if (user) {
        if (loggedOutDiv) loggedOutDiv.classList.add("hidden");
        if (loggedInDiv) loggedInDiv.classList.remove("hidden");
        
        const avatarInitial = document.getElementById("user-avatar-initial");
        const nameDisplay = document.getElementById("user-name-display");
        const emailDisplay = document.getElementById("user-email-display");
        
        if (avatarInitial) avatarInitial.textContent = (user.full_name || "U")[0].toUpperCase();
        if (nameDisplay) nameDisplay.textContent = user.full_name || user.email.split("@")[0];
        if (emailDisplay) emailDisplay.textContent = user.email;
    } else {
        if (loggedOutDiv) loggedOutDiv.classList.remove("hidden");
        if (loggedInDiv) loggedInDiv.classList.add("hidden");
    }
}

function openAuthModal(mode = "login") {
    state.authMode = mode;
    toggleAuthMode(mode);
    const modal = document.getElementById("auth-modal");
    if (modal) modal.classList.remove("hidden");
    const errBanner = document.getElementById("auth-error-banner");
    if (errBanner) errBanner.classList.add("hidden");
}

function closeAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.classList.add("hidden");
}

function toggleAuthMode(mode) {
    state.authMode = mode;
    const loginTab = document.getElementById("auth-tab-login");
    const registerTab = document.getElementById("auth-tab-register");
    const nameField = document.getElementById("auth-field-name");
    const styleField = document.getElementById("auth-field-style");
    const title = document.getElementById("auth-modal-title");
    const subtitle = document.getElementById("auth-modal-subtitle");
    const submitBtn = document.getElementById("auth-submit-btn");
    const errBanner = document.getElementById("auth-error-banner");
    if (errBanner) errBanner.classList.add("hidden");

    if (mode === "register") {
        loginTab.className = "flex-1 py-2 text-xs font-semibold rounded-xl text-zinc-500 hover:text-zinc-900 transition";
        registerTab.className = "flex-1 py-2 text-xs font-bold rounded-xl bg-white text-zinc-900 shadow-xs transition";
        if (nameField) nameField.classList.remove("hidden");
        if (styleField) styleField.classList.remove("hidden");
        if (title) title.textContent = "Create Your Style Profile";
        if (subtitle) subtitle.textContent = "Digitize your closet and unlock daily AI recommendations";
        if (submitBtn) submitBtn.textContent = "Create Account";
    } else {
        loginTab.className = "flex-1 py-2 text-xs font-bold rounded-xl bg-white text-zinc-900 shadow-xs transition";
        registerTab.className = "flex-1 py-2 text-xs font-semibold rounded-xl text-zinc-500 hover:text-zinc-900 transition";
        if (nameField) nameField.classList.add("hidden");
        if (styleField) styleField.classList.add("hidden");
        if (title) title.textContent = "Sign In to Your Closet";
        if (subtitle) subtitle.textContent = "Access your personalized wardrobe and AI lookbook";
        if (submitBtn) submitBtn.textContent = "Sign In";
    }
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const email = document.getElementById("auth-email-input").value;
    const password = document.getElementById("auth-password-input").value;
    const submitBtn = document.getElementById("auth-submit-btn");
    const errBanner = document.getElementById("auth-error-banner");

    try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="inline-block animate-spin mr-2">⏳</span> Processing...`;
        if (errBanner) errBanner.classList.add("hidden");

        let authData;
        if (state.authMode === "register") {
            const fullName = document.getElementById("auth-name-input").value;
            const style = document.getElementById("auth-style-input").value;
            authData = await API.register(email, fullName, password, style);
            showToast(`Welcome to ATELIER, ${fullName}! 🎉`, "success");
        } else {
            authData = await API.login(email, password);
            showToast(`Welcome back, ${authData.user.full_name}! 👋`, "success");
        }

        state.currentUser = authData.user;
        renderAuthUI(authData.user);
        closeAuthModal();

        // Refresh closet and stats for the authenticated user
        await loadWardrobeItems();
        await loadFeedbackStats();

        submitBtn.disabled = false;
        submitBtn.textContent = state.authMode === "register" ? "Create Account" : "Sign In";
    } catch (err) {
        submitBtn.disabled = false;
        submitBtn.textContent = state.authMode === "register" ? "Create Account" : "Sign In";
        if (errBanner) {
            errBanner.textContent = err.message;
            errBanner.classList.remove("hidden");
        }
    }
}

function toggleUserDropdown(event) {
    if (event) event.stopPropagation();
    const menu = document.getElementById("user-dropdown-menu");
    if (menu) {
        menu.classList.toggle("hidden");
    }
}

function closeUserDropdown() {
    const menu = document.getElementById("user-dropdown-menu");
    if (menu) {
        menu.classList.add("hidden");
    }
}

// Close dropdown when clicking outside
document.addEventListener("click", (e) => {
    const menu = document.getElementById("user-dropdown-menu");
    const btn = document.getElementById("user-profile-menu-btn");
    if (menu && !menu.contains(e.target) && btn && !btn.contains(e.target)) {
        menu.classList.add("hidden");
    }
});

function handleLogout() {
    closeUserDropdown();
    API.logout();
    state.currentUser = null;
    renderAuthUI(null);
    showToast("Signed out of ATELIER", "info");
    
    // Refresh view
    loadWardrobeItems();
    loadFeedbackStats();
}

/* =========================================================================
   2. Closet Gallery Management & Filtering
   ========================================================================= */

async function loadWardrobeItems() {
    const grid = document.getElementById("wardrobe-grid");
    const countBadge = document.getElementById("wardrobe-count");
    
    if (!state.currentUser) {
        state.items = [];
        if (countBadge) countBadge.textContent = "0 Pieces";
        renderWardrobeGrid();
        return;
    }

    try {
        const items = await API.getItems();
        state.items = items;
        if (countBadge) countBadge.textContent = `${items.length} Pieces`;
        renderWardrobeGrid();
    } catch (e) {
        console.error("Error loading closet items:", e);
        state.items = [];
        if (countBadge) countBadge.textContent = "0 Pieces";
        renderWardrobeGrid();
    }
}

function renderWardrobeGrid() {
    const grid = document.getElementById("wardrobe-grid");
    if (!grid) return;

    if (!state.currentUser) {
        grid.innerHTML = `
            <div class="col-span-full py-20 text-center bg-white rounded-3xl border border-[#EAE7DE] p-8">
                <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#FAF9F5] text-zinc-700 mb-4 border border-[#EAE7DE]">
                    <i data-lucide="lock" class="w-6 h-6 text-amber-700"></i>
                </div>
                <h3 class="font-serif text-2xl font-bold text-zinc-900">Your Private Digital Closet</h3>
                <p class="text-xs text-zinc-500 max-w-md mx-auto mt-2 mb-6">Sign in or create a new style profile to digitize your wardrobe and unlock personalized daily lookbooks.</p>
                <div class="flex items-center justify-center gap-3">
                    <button onclick="openAuthModal('login')" class="px-5 py-2.5 bg-white hover:bg-[#FAF9F5] text-zinc-800 text-xs font-bold rounded-xl border border-[#EAE7DE] transition shadow-2xs">
                        Sign In
                    </button>
                    <button onclick="openAuthModal('register')" class="px-5 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold rounded-xl shadow-xs transition">
                        Create Account
                    </button>
                </div>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    let filtered = state.items;
    if (state.selectedCategoryFilter !== "all") {
        filtered = filtered.filter(i => i.category === state.selectedCategoryFilter);
    }

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full py-20 text-center bg-white rounded-3xl border border-[#EAE7DE] p-8">
                <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#FAF9F5] text-zinc-600 mb-4 border border-[#EAE7DE]">
                    <i data-lucide="sparkles" class="w-6 h-6 text-amber-600"></i>
                </div>
                <h3 class="font-serif text-xl font-bold text-zinc-900">Your closet is completely fresh</h3>
                <p class="text-xs text-zinc-500 max-w-sm mx-auto mt-1 mb-6">Add photos of your tops, bottoms, and footwear to begin curating smart outfit recommendations!</p>
                <button onclick="switchTab('add_item')" class="px-6 py-3 bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold rounded-xl shadow-xs transition">
                    + Add New Piece
                </button>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    grid.innerHTML = filtered.map(item => `
        <div class="editorial-card rounded-2xl overflow-hidden flex flex-col group relative">
            <div class="relative aspect-square bg-[#FAF9F5] overflow-hidden">
                <img src="${item.image_url}" alt="${item.subcategory}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500">
                <div class="absolute top-3 left-3 bg-white/95 backdrop-blur-md px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider text-zinc-700 shadow-2xs">
                    ${item.category}
                </div>
                <button onclick="deleteItemHandler(${item.id})" class="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/90 hover:bg-rose-50 text-zinc-400 hover:text-rose-600 flex items-center justify-center opacity-0 group-hover:opacity-100 transition shadow-2xs" title="Remove piece">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
            </div>

            <div class="p-4 flex-1 flex flex-col justify-between">
                <div>
                    <div class="flex items-center justify-between gap-2 mb-1.5">
                        <h4 class="font-bold text-zinc-900 capitalize text-xs truncate">${item.subcategory}</h4>
                        <div class="flex items-center gap-1.5" title="${item.dominant_color_name}">
                            <span class="w-3 h-3 rounded-full border border-black/10 shadow-2xs inline-block" style="background-color: ${item.dominant_color_hex}"></span>
                            <span class="text-[11px] text-zinc-500 truncate max-w-[70px]">${item.dominant_color_name}</span>
                        </div>
                    </div>

                    <div class="flex flex-wrap gap-1.5 mt-2">
                        <span class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-[#FAF9F5] text-zinc-700 border border-[#EAE7DE]">
                            Warmth: ${'☀️'.repeat(item.warmth_level)}
                        </span>
                        <span class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-[#FAF9F5] text-zinc-700 border border-[#EAE7DE]">
                            Formality: ${item.formality_level}/5
                        </span>
                    </div>
                </div>
            </div>
        </div>
    `).join("");

    lucide.createIcons();
}

function filterWardrobe(cat) {
    state.selectedCategoryFilter = cat;
    document.querySelectorAll(".cat-pill").forEach(btn => {
        if (btn.dataset.cat === cat) {
            btn.classList.add("bg-zinc-900", "text-white", "shadow-xs");
            btn.classList.remove("bg-white", "text-zinc-600", "border-[#EAE7DE]");
        } else {
            btn.classList.remove("bg-zinc-900", "text-white", "shadow-xs");
            btn.classList.add("bg-white", "text-zinc-600", "border-[#EAE7DE]");
        }
    });
    renderWardrobeGrid();
}

async function deleteItemHandler(itemId) {
    if (!confirm("Remove this piece from your digital closet?")) return;
    try {
        await API.deleteItem(itemId);
        showToast("Piece removed from closet", "success");
        await loadWardrobeItems();
    } catch (e) {
        showToast(e.message, "error");
    }
}

/* =========================================================================
   3. Photo Upload & Intelligent Style Recognition
   ========================================================================= */

function setupUploadHandlers() {
    const dropzone = document.getElementById("upload-dropzone");
    const fileInput = document.getElementById("file-input");

    if (dropzone && fileInput) {
        dropzone.addEventListener("click", () => fileInput.click());
        dropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropzone.classList.add("border-zinc-900", "bg-zinc-50");
        });
        dropzone.addEventListener("dragleave", () => {
            dropzone.classList.remove("border-zinc-900", "bg-zinc-50");
        });
        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.classList.remove("border-zinc-900", "bg-zinc-50");
            if (e.dataTransfer.files.length > 0) {
                processUploadedFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                processUploadedFile(e.target.files[0]);
            }
        });
    }

    const saveBtn = document.getElementById("confirm-save-item-btn");
    if (saveBtn) {
        saveBtn.addEventListener("click", saveConfirmedItem);
    }
}

async function processUploadedFile(file) {
    if (!file.type.startsWith("image/")) {
        showToast("Please upload a valid photo file (JPG, PNG, WebP).", "error");
        return;
    }

    const loadingElem = document.getElementById("upload-loading");
    const previewModal = document.getElementById("tag-preview-card");
    const dropzoneElem = document.getElementById("upload-dropzone");

    try {
        if (loadingElem) loadingElem.classList.remove("hidden");
        if (dropzoneElem) dropzoneElem.classList.add("hidden");

        const previewData = await API.uploadPreview(file);
        state.previewItem = previewData;

        renderPreviewForm(previewData);

        if (loadingElem) loadingElem.classList.add("hidden");
        if (previewModal) previewModal.classList.remove("hidden");
    } catch (e) {
        if (loadingElem) loadingElem.classList.add("hidden");
        if (dropzoneElem) dropzoneElem.classList.remove("hidden");
        showToast("Error analyzing photo: " + e.message, "error");
    }
}

function renderPreviewForm(data) {
    document.getElementById("preview-img").src = data.temp_image_url;
    document.getElementById("preview-category-select").value = data.suggested_category;
    document.getElementById("preview-subcategory-input").value = data.suggested_subcategory;
    document.getElementById("preview-color-name").value = data.dominant_color_name;
    document.getElementById("preview-color-hex").value = data.dominant_color_hex;
    document.getElementById("color-preview-circle").style.backgroundColor = data.dominant_color_hex;
    
    document.getElementById("preview-warmth").value = data.suggested_warmth;
    document.getElementById("warmth-val-display").textContent = getWarmthLabelText(data.suggested_warmth);
    
    document.getElementById("preview-formality").value = data.suggested_formality;
    document.getElementById("formality-val-display").textContent = getFormalityLabelText(data.suggested_formality);

    // Color Swatches
    const swatchContainer = document.getElementById("color-swatches-container");
    if (swatchContainer && data.color_palette) {
        swatchContainer.innerHTML = data.color_palette.map(c => `
            <button type="button" onclick="selectColorSwatch('${c.name}', '${c.hex}')" 
                class="swatch-pill flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs bg-white hover:border-zinc-500 shadow-2xs transition">
                <span class="w-3.5 h-3.5 rounded-full border border-black/10" style="background-color: ${c.hex}"></span>
                <span class="font-medium text-zinc-700">${c.name} (${c.percentage}%)</span>
            </button>
        `).join("");
    }

    // Detected Suggestions
    const candidateContainer = document.getElementById("candidate-tags-container");
    if (candidateContainer && data.top_candidate_tags) {
        candidateContainer.innerHTML = data.top_candidate_tags.map(c => `
            <button type="button" onclick="selectCandidateTag('${c.category}', '${c.subcategory}', ${c.default_warmth}, ${c.default_formality})" 
                class="px-3 py-1.5 rounded-xl text-xs border border-[#EAE7DE] bg-white hover:border-zinc-900 text-zinc-800 font-semibold transition">
                ${c.subcategory} <span class="text-zinc-400 font-normal">(${c.confidence}%)</span>
            </button>
        `).join("");
    }
}

function selectColorSwatch(name, hex) {
    document.getElementById("preview-color-name").value = name;
    document.getElementById("preview-color-hex").value = hex;
    document.getElementById("color-preview-circle").style.backgroundColor = hex;
}

function selectCandidateTag(cat, subcat, warmth, formality) {
    document.getElementById("preview-category-select").value = cat;
    document.getElementById("preview-subcategory-input").value = subcat;
    document.getElementById("preview-warmth").value = warmth;
    document.getElementById("warmth-val-display").textContent = getWarmthLabelText(warmth);
    document.getElementById("preview-formality").value = formality;
    document.getElementById("formality-val-display").textContent = getFormalityLabelText(formality);
}

function getWarmthLabelText(val) {
    const map = {
        1: "Level 1 (Light Summer)",
        2: "Level 2 (Mild / Warm)",
        3: "Level 3 (Cool Spring / Autumn)",
        4: "Level 4 (Chilly / Layered)",
        5: "Level 5 (Deep Winter Coat)"
    };
    return map[val] || `Level ${val}`;
}

function getFormalityLabelText(val) {
    const map = {
        1: "Level 1 (Relaxed / Loungewear)",
        2: "Level 2 (Casual Everyday)",
        3: "Level 3 (Smart Casual)",
        4: "Level 4 (Semi-Formal / Cocktail)",
        5: "Level 5 (Black-Tie Formal)"
    };
    return map[val] || `Level ${val}/5`;
}

function updateWarmthLabel(val) {
    document.getElementById("warmth-val-display").textContent = getWarmthLabelText(val);
}

function updateFormalityLabel(val) {
    document.getElementById("formality-val-display").textContent = getFormalityLabelText(val);
}

async function saveConfirmedItem() {
    if (!state.previewItem) return;

    const payload = {
        image_filename: state.previewItem.temp_image_url,
        category: document.getElementById("preview-category-select").value,
        subcategory: document.getElementById("preview-subcategory-input").value,
        dominant_color_name: document.getElementById("preview-color-name").value,
        dominant_color_hex: document.getElementById("preview-color-hex").value,
        color_palette: state.previewItem.color_palette || [],
        warmth_level: parseInt(document.getElementById("preview-warmth").value),
        formality_level: parseInt(document.getElementById("preview-formality").value),
        occasion_tags: ["college", "casual_outing"],
        notes: document.getElementById("preview-notes") ? document.getElementById("preview-notes").value : ""
    };

    try {
        const btn = document.getElementById("confirm-save-item-btn");
        btn.disabled = true;
        btn.innerHTML = `<span class="inline-block animate-spin mr-2">⏳</span> Saving to Closet...`;

        await API.saveItem(payload);
        showToast("Piece added to your closet!", "success");

        state.previewItem = null;
        document.getElementById("tag-preview-card").classList.add("hidden");
        document.getElementById("upload-dropzone").classList.remove("hidden");
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="check" class="w-4 h-4"></i> Save to Closet`;

        switchTab("wardrobe");
    } catch (e) {
        showToast("Error saving piece: " + e.message, "error");
        document.getElementById("confirm-save-item-btn").disabled = false;
    }
}

function cancelUpload() {
    state.previewItem = null;
    document.getElementById("tag-preview-card").classList.add("hidden");
    document.getElementById("upload-dropzone").classList.remove("hidden");
}

/* =========================================================================
   4. Daily Stylist & Lookbook Generation
   ========================================================================= */

function setupRecommenderControls() {
    document.querySelectorAll(".occasion-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            state.selectedOccasion = pill.dataset.occasion;
            document.querySelectorAll(".occasion-pill").forEach(p => {
                p.classList.remove("border-zinc-900", "bg-zinc-900", "text-white", "shadow-xs");
                p.classList.add("border-[#EAE7DE]", "bg-white", "text-zinc-800");
                const sub = p.querySelector("span:last-child");
                if (sub) sub.classList.replace("text-zinc-300", "text-zinc-400");
            });
            pill.classList.add("border-zinc-900", "bg-zinc-900", "text-white", "shadow-xs");
            pill.classList.remove("border-[#EAE7DE]", "bg-white", "text-zinc-800");
            const sub = pill.querySelector("span:last-child");
            if (sub) sub.classList.replace("text-zinc-400", "text-zinc-300");
        });
    });

    const genBtn = document.getElementById("generate-outfits-btn");
    if (genBtn) {
        genBtn.addEventListener("click", generateOutfitsHandler);
    }

    const cityInput = document.getElementById("weather-city-input");
    if (cityInput) {
        cityInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                loadWeather(cityInput.value);
            }
        });
    }
}

async function loadWeather(city = null) {
    try {
        const weather = await API.getWeather(city);
        state.weather = weather;
        renderWeatherCard(weather);
    } catch (e) {
        console.error("Error loading weather forecast:", e);
    }
}

function renderWeatherCard(w) {
    const weatherCard = document.getElementById("weather-display-card");
    if (!weatherCard) return;

    weatherCard.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
                <span class="text-2xl">${w.weather_icon}</span>
                <div>
                    <h4 class="font-bold text-white text-xs">${w.city}</h4>
                    <p class="text-[11px] text-zinc-400">${w.weather_condition} • Humidity: ${w.humidity_percent}%</p>
                </div>
            </div>
            <div class="text-right">
                <div class="font-serif text-xl font-bold text-amber-200">${w.temperature_c}°C</div>
                <div class="text-[10px] text-zinc-300">${w.warmth_recommendation.split(':')[0]}</div>
            </div>
        </div>
    `;
}

function useGpsLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            try {
                const w = await API.getWeather(null, lat, lon);
                state.weather = w;
                renderWeatherCard(w);
                showToast("Location updated!", "success");
            } catch (e) {
                showToast("Failed to fetch local weather", "error");
            }
        }, () => {
            showToast("Location access denied or unavailable", "error");
        });
    } else {
        showToast("Geolocation not supported by browser", "error");
    }
}

async function generateOutfitsHandler() {
    const container = document.getElementById("outfit-results-container");
    const genBtn = document.getElementById("generate-outfits-btn");
    
    try {
        genBtn.disabled = true;
        genBtn.innerHTML = `<span class="inline-block animate-spin mr-2">✨</span> Styling Lookbook...`;
        container.innerHTML = `
            <div class="py-20 text-center bg-white rounded-3xl border border-[#EAE7DE] p-8">
                <div class="inline-block w-8 h-8 border-3 border-zinc-900 border-t-transparent rounded-full animate-spin mb-4"></div>
                <h4 class="font-serif text-lg font-bold text-zinc-900">Curating Your Personalized Looks...</h4>
                <p class="text-xs text-zinc-400 mt-1">Harmonizing color palettes, silhouettes, and weather adaptability</p>
            </div>
        `;

        const cityVal = document.getElementById("weather-city-input") ? document.getElementById("weather-city-input").value : null;
        const res = await API.getRecommendations({
            occasion: state.selectedOccasion,
            city: cityVal || (state.weather ? state.weather.city : "London"),
            top_n: 6
        });

        state.recommendations = res.outfits;
        renderOutfits(res);

        genBtn.disabled = false;
        genBtn.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4 text-zinc-900"></i> Curate Outfits`;
        lucide.createIcons();
    } catch (e) {
        genBtn.disabled = false;
        genBtn.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4 text-zinc-900"></i> Curate Outfits`;
        container.innerHTML = `
            <div class="py-14 px-8 bg-white rounded-3xl border border-amber-200 text-center max-w-lg mx-auto shadow-sm">
                <div class="w-12 h-12 rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center mx-auto mb-3">
                    <i data-lucide="sparkles" class="w-6 h-6"></i>
                </div>
                <h4 class="font-serif text-lg font-bold text-zinc-900">Add More Wardrobe Variety</h4>
                <p class="text-xs text-zinc-500 mt-1">${e.message}</p>
                <button onclick="switchTab('add_item')" class="mt-5 px-6 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-bold rounded-xl transition">
                    + Add Pieces to Closet
                </button>
            </div>
        `;
        lucide.createIcons();
    }
}

function renderOutfits(res) {
    const container = document.getElementById("outfit-results-container");
    if (!container) return;

    if (!res.outfits || res.outfits.length === 0) {
        container.innerHTML = `<div class="text-center py-16 text-zinc-400 text-sm">No outfits available for this combination.</div>`;
        return;
    }

    container.innerHTML = `
        <div class="mb-6 flex items-center justify-between">
            <div class="text-xs text-zinc-500 font-medium">
                Showing <span class="font-bold text-zinc-900">${res.outfits.length} curated looks</span> for your selection
            </div>
            <div class="inline-flex items-center gap-1.5 text-xs bg-white text-zinc-800 px-3.5 py-1.5 rounded-full font-semibold border border-[#EAE7DE] shadow-2xs">
                <span>✨ ${res.outfits[0].scores.scoring_model_used}</span>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            ${res.outfits.map((outfit, idx) => {
                const lookTitle = LOOK_TITLES[idx % LOOK_TITLES.length];
                return `
                <div class="editorial-card rounded-3xl overflow-hidden flex flex-col justify-between bg-white border border-[#EAE7DE]">
                    <div class="p-5 border-b border-[#F0EDE6] flex items-center justify-between">
                        <div>
                            <span class="text-[10px] font-bold tracking-widest uppercase text-amber-700 block mb-0.5">Look #${idx + 1}</span>
                            <h4 class="font-serif text-base font-bold text-zinc-900">${lookTitle}</h4>
                        </div>
                        <div class="text-right">
                            <span class="font-serif text-lg font-bold text-zinc-900">${outfit.scores.total_score}%</span>
                            <span class="text-[10px] text-zinc-400 block -mt-1 font-medium">Style Match</span>
                        </div>
                    </div>

                    <!-- Wardrobe Pieces Spread -->
                    <div class="p-5 grid grid-cols-3 gap-3 bg-[#FCFBF9]">
                        <!-- Top -->
                        <div class="lookbook-item-frame p-2 flex flex-col items-center text-center bg-white border border-[#EAE7DE] rounded-2xl">
                            <div class="w-full aspect-square rounded-xl overflow-hidden mb-2 bg-[#FAF9F5]">
                                <img src="${outfit.top.image_url}" class="w-full h-full object-cover">
                            </div>
                            <span class="text-[11px] font-bold text-zinc-900 capitalize truncate w-full">${outfit.top.subcategory}</span>
                            <div class="flex items-center gap-1 text-[10px] text-zinc-400 mt-0.5">
                                <span class="w-2 h-2 rounded-full inline-block" style="background-color: ${outfit.top.dominant_color_hex}"></span>
                                <span class="truncate max-w-[60px]">${outfit.top.dominant_color_name}</span>
                            </div>
                        </div>

                        <!-- Bottom -->
                        <div class="lookbook-item-frame p-2 flex flex-col items-center text-center bg-white border border-[#EAE7DE] rounded-2xl">
                            <div class="w-full aspect-square rounded-xl overflow-hidden mb-2 bg-[#FAF9F5]">
                                <img src="${outfit.bottom.image_url}" class="w-full h-full object-cover">
                            </div>
                            <span class="text-[11px] font-bold text-zinc-900 capitalize truncate w-full">${outfit.bottom.subcategory}</span>
                            <div class="flex items-center gap-1 text-[10px] text-zinc-400 mt-0.5">
                                <span class="w-2 h-2 rounded-full inline-block" style="background-color: ${outfit.bottom.dominant_color_hex}"></span>
                                <span class="truncate max-w-[60px]">${outfit.bottom.dominant_color_name}</span>
                            </div>
                        </div>

                        <!-- Footwear -->
                        <div class="lookbook-item-frame p-2 flex flex-col items-center text-center bg-white border border-[#EAE7DE] rounded-2xl">
                            <div class="w-full aspect-square rounded-xl overflow-hidden mb-2 bg-[#FAF9F5]">
                                <img src="${outfit.footwear.image_url}" class="w-full h-full object-cover">
                            </div>
                            <span class="text-[11px] font-bold text-zinc-900 capitalize truncate w-full">${outfit.footwear.subcategory}</span>
                            <div class="flex items-center gap-1 text-[10px] text-zinc-400 mt-0.5">
                                <span class="w-2 h-2 rounded-full inline-block" style="background-color: ${outfit.footwear.dominant_color_hex}"></span>
                                <span class="truncate max-w-[60px]">${outfit.footwear.dominant_color_name}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Editorial Styling Rationale -->
                    <div class="px-5 py-3.5 bg-white border-t border-[#F0EDE6]">
                        <div class="text-[11px] text-zinc-600 space-y-1">
                            ${outfit.match_reasons.map(r => `<div class="flex items-start gap-1.5"><span class="text-amber-700">✦</span><span>${r}</span></div>`).join("")}
                        </div>
                    </div>

                    <!-- Interaction Controls -->
                    <div class="p-4 bg-[#FAF9F5] border-t border-[#EAE7DE] flex items-center justify-between">
                        <span class="text-[11px] font-semibold text-zinc-500">Your Impression:</span>
                        <div class="flex items-center gap-2" id="feedback-btns-${outfit.recommendation_id}">
                            <button onclick="submitFeedbackHandler(${outfit.recommendation_id}, 1)" 
                                class="px-3.5 py-1.5 rounded-xl border ${outfit.user_rating === 1 ? 'bg-zinc-900 text-white border-zinc-900' : 'bg-white hover:border-zinc-400 text-zinc-800 border-[#EAE7DE]'} text-xs font-bold flex items-center gap-1.5 transition shadow-2xs">
                                ❤️ Love It
                            </button>
                            <button onclick="submitFeedbackHandler(${outfit.recommendation_id}, -1)" 
                                class="px-3.5 py-1.5 rounded-xl border ${outfit.user_rating === -1 ? 'bg-zinc-200 text-zinc-800 border-zinc-300' : 'bg-white hover:border-zinc-400 text-zinc-500 border-[#EAE7DE]'} text-xs font-semibold flex items-center gap-1 transition shadow-2xs">
                                ✕ Pass
                            </button>
                        </div>
                    </div>
                </div>
            `;}).join("")}
        </div>
    `;
    lucide.createIcons();
}

async function submitFeedbackHandler(recId, rating) {
    try {
        await API.submitFeedback(recId, rating);
        showToast(rating === 1 ? "Added to your style favorites! ❤️" : "Got it! We'll adjust your style profile.", "success");

        const container = document.getElementById(`feedback-btns-${recId}`);
        if (container) {
            container.innerHTML = `
                <button onclick="submitFeedbackHandler(${recId}, 1)" class="px-3.5 py-1.5 rounded-xl border ${rating === 1 ? 'bg-zinc-900 text-white border-zinc-900' : 'bg-white hover:border-zinc-400 text-zinc-800 border-[#EAE7DE]'} text-xs font-bold flex items-center gap-1.5">
                    ❤️ Love It
                </button>
                <button onclick="submitFeedbackHandler(${recId}, -1)" class="px-3.5 py-1.5 rounded-xl border ${rating === -1 ? 'bg-zinc-200 text-zinc-800 border-zinc-300' : 'bg-white hover:border-zinc-400 text-zinc-500 border-[#EAE7DE]'} text-xs font-semibold flex items-center gap-1">
                    ✕ Pass
                </button>
            `;
        }

        loadFeedbackStats();
    } catch (e) {
        showToast("Feedback error: " + e.message, "error");
    }
}

/* =========================================================================
   5. Style DNA & Taste Profile Insights
   ========================================================================= */

async function loadFeedbackStats() {
    try {
        const stats = await API.getFeedbackStats();
        state.feedbackStats = stats;
        
        const countElem = document.getElementById("stat-total-feedback");
        const likesElem = document.getElementById("stat-likes");
        const dislikesElem = document.getElementById("stat-dislikes");
        const statusBadge = document.getElementById("model-status-badge");

        if (countElem) countElem.textContent = stats.total_feedback_count;
        if (likesElem) likesElem.textContent = stats.thumbs_up_count;
        if (dislikesElem) dislikesElem.textContent = stats.thumbs_down_count;

        if (statusBadge) {
            if (stats.total_feedback_count >= 5) {
                statusBadge.innerHTML = `<span class="text-emerald-800 bg-emerald-50 px-3.5 py-1.5 rounded-full text-xs font-bold border border-emerald-200">Personal AI Stylist Optimized (${stats.total_feedback_count} ratings)</span>`;
            } else {
                statusBadge.innerHTML = `<span class="text-zinc-700 bg-[#FAF9F5] px-3.5 py-1.5 rounded-full text-xs font-bold border border-[#EAE7DE]">Learning Your Taste (${stats.total_feedback_count}/5 ratings)</span>`;
            }
        }
    } catch (e) {
        console.error("Error loading feedback statistics:", e);
    }
}

function renderAnalytics() {
    const items = state.items;
    const statsContainer = document.getElementById("analytics-content");
    if (!statsContainer) return;

    const catCounts = { top: 0, bottom: 0, footwear: 0, outerwear: 0 };
    const colorCounts = {};
    const warmthCounts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };

    items.forEach(item => {
        if (catCounts[item.category] !== undefined) catCounts[item.category]++;
        colorCounts[item.dominant_color_name] = (colorCounts[item.dominant_color_name] || 0) + 1;
        if (warmthCounts[item.warmth_level] !== undefined) warmthCounts[item.warmth_level]++;
    });

    const topColors = Object.entries(colorCounts).sort((a, b) => b[1] - a[1]).slice(0, 6);

    statsContainer.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Wardrobe Breakdown -->
            <div class="bg-white p-7 rounded-3xl border border-[#EAE7DE] shadow-xs">
                <h4 class="font-serif text-base font-bold text-zinc-900 mb-4">Closet Balance</h4>
                <div class="space-y-3">
                    <div class="flex justify-between items-center text-xs">
                        <span class="text-zinc-600 font-medium">Tops & Shirts</span>
                        <span class="font-bold text-zinc-900">${catCounts.top} pieces</span>
                    </div>
                    <div class="flex justify-between items-center text-xs">
                        <span class="text-zinc-600 font-medium">Trousers & Denim</span>
                        <span class="font-bold text-zinc-900">${catCounts.bottom} pieces</span>
                    </div>
                    <div class="flex justify-between items-center text-xs">
                        <span class="text-zinc-600 font-medium">Footwear Collection</span>
                        <span class="font-bold text-zinc-900">${catCounts.footwear} pairs</span>
                    </div>
                    <div class="flex justify-between items-center text-xs">
                        <span class="text-zinc-600 font-medium">Outerwear & Jackets</span>
                        <span class="font-bold text-zinc-900">${catCounts.outerwear} pieces</span>
                    </div>
                </div>
            </div>

            <!-- Signature Colors -->
            <div class="bg-white p-7 rounded-3xl border border-[#EAE7DE] shadow-xs">
                <h4 class="font-serif text-base font-bold text-zinc-900 mb-4">Signature Palette</h4>
                <div class="space-y-2.5">
                    ${topColors.map(([color, count]) => `
                        <div class="flex items-center justify-between text-xs">
                            <span class="text-zinc-700 font-medium truncate max-w-[140px]">${color}</span>
                            <span class="px-2.5 py-0.5 rounded-full bg-[#FAF9F5] text-zinc-800 font-bold border border-[#EAE7DE]">${count}</span>
                        </div>
                    `).join("")}
                </div>
            </div>

            <!-- Climate Spectrum -->
            <div class="bg-white p-7 rounded-3xl border border-[#EAE7DE] shadow-xs">
                <h4 class="font-serif text-base font-bold text-zinc-900 mb-4">Seasonal Adaptability</h4>
                <div class="space-y-2 text-xs">
                    <div class="flex justify-between"><span>Summer Light (Level 1):</span> <span class="font-bold text-zinc-900">${warmthCounts[1]} pieces</span></div>
                    <div class="flex justify-between"><span>Mild Warmth (Level 2):</span> <span class="font-bold text-zinc-900">${warmthCounts[2]} pieces</span></div>
                    <div class="flex justify-between"><span>Mid-Season (Level 3):</span> <span class="font-bold text-zinc-900">${warmthCounts[3]} pieces</span></div>
                    <div class="flex justify-between"><span>Autumn / Chilly (Level 4):</span> <span class="font-bold text-zinc-900">${warmthCounts[4]} pieces</span></div>
                    <div class="flex justify-between"><span>Winter Heavy (Level 5):</span> <span class="font-bold text-zinc-900">${warmthCounts[5]} pieces</span></div>
                </div>
            </div>
        </div>
    `;
}

/* =========================================================================
   6. Toast Notification System
   ========================================================================= */

function showToast(msg, type = "info") {
    const toast = document.createElement("div");
    toast.className = `fixed bottom-8 right-8 z-50 px-5 py-3.5 rounded-2xl text-xs font-bold shadow-xl transition transform duration-300 translate-y-4 opacity-0 flex items-center gap-2.5 ${
        type === "success" ? "bg-zinc-900 text-white border border-zinc-800" : type === "error" ? "bg-rose-900 text-white" : "bg-zinc-900 text-white"
    }`;
    toast.innerHTML = `<span>${type === "success" ? "✦" : type === "error" ? "✕" : "ℹ"}</span> <span>${msg}</span>`;
    
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove("translate-y-4", "opacity-0");
    }, 10);

    setTimeout(() => {
        toast.classList.add("translate-y-4", "opacity-0");
        setTimeout(() => toast.remove(), 350);
    }, 3200);
}
