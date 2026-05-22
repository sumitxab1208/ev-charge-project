// ================= MAP =================

let map = L.map('map').setView([31.326, 75.5762], 12);

L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    { attribution: '© OpenStreetMap' }
).addTo(map);

// ================= GLOBAL =================

let stations      = [];
let markers       = [];
let routeControl  = null;
let selectedMarker = null;
let chartInstance  = null;
let userLat        = null;
let userLng        = null;

// ================= LOAD DATA =================

document.getElementById("result").innerText =
    "⚡ Loading Smart EV Network...";

fetch('/stations')
    .then(res => res.json())
    .then(data => {
        stations = data;
        renderStations(data);
        updateStats();
        createChart();
        document.getElementById("result").innerText =
            "✅ System Ready — " + data.length + " stations loaded";

        // Update hero live count
        let heroCount = document.getElementById("heroStationCount");
        if (heroCount) heroCount.innerText = data.length;
    });

// ================= LIVE CLOCK =================

function updateClock() {
    let now  = new Date();
    let h    = String(now.getHours()).padStart(2, '0');
    let m    = String(now.getMinutes()).padStart(2, '0');
    let s    = String(now.getSeconds()).padStart(2, '0');
    let el   = document.getElementById("clockTime");
    if (el) el.innerText = `${h}:${m}:${s}`;
}

updateClock();
setInterval(updateClock, 1000);

// ================= LIVE SEARCH =================

document.getElementById("searchBox")
    .addEventListener("input", () => {
        searchStation();
    });

// ================= RENDER STATIONS =================

function renderStations(data) {
    clearMarkers();

    let list = document.getElementById("stationList");
    list.innerHTML = "";

    if (data.length === 0) {
        list.innerHTML = `
            <div style="text-align:center;padding:30px;color:#475569;">
                <i class="fa-solid fa-circle-xmark" style="font-size:32px;margin-bottom:12px;display:block;"></i>
                No stations found
            </div>`;
        return;
    }

    data.forEach((station, index) => {

        // ================= ICON =================

        let iconUrl;

        if (!station.available) {
            iconUrl = 'https://maps.google.com/mapfiles/ms/icons/red-dot.png';
        } else if (station.type === "Fast") {
            iconUrl = 'https://maps.google.com/mapfiles/ms/icons/green-dot.png';
        } else {
            iconUrl = 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png';
        }

        let icon = new L.Icon({ iconUrl: iconUrl, iconSize: [35, 35] });

        // ================= MARKER =================

        let marker = L.marker([station.lat, station.lng], { icon })
            .addTo(map)
            .bindPopup(`
                <div style="font-family:Poppins;width:230px;padding:4px;">
                    <h3 style="margin-bottom:10px;font-size:15px;">⚡ ${station.name}</h3>
                    <p style="margin:5px 0;font-size:13px;"><b>Type:</b> ${station.type}</p>
                    <p style="margin:5px 0;font-size:13px;"><b>Status:</b> ${station.available ? "🟢 Available" : "🔴 Busy"}</p>
                    <p style="margin:5px 0;font-size:13px;"><b>Price:</b> ₹${station.price}/kWh</p>
                    <button onclick="openStationModal('${station.name}','${station.type}','${station.available}','${station.price}','${station.lat}','${station.lng}')"
                        style="margin-top:12px;width:100%;padding:9px;border:none;border-radius:10px;background:#2563eb;color:white;font-weight:600;cursor:pointer;font-size:13px;">
                        View Details
                    </button>
                </div>
            `);

        markers.push(marker);

        // ================= STATION CARD =================

        let badgeClass = station.type === "Fast" ? "badge-fast" : "badge-slow";
        let badgeIcon  = station.type === "Fast" ? "⚡" : "🐢";

        list.innerHTML += `
            <div
                class="station-card fade-in"
                style="animation-delay:${index * 0.06}s"
                onclick="openStationModal(
                    '${station.name}',
                    '${station.type}',
                    '${station.available}',
                    '${station.price}',
                    '${station.lat}',
                    '${station.lng}'
                )"
            >
                <div class="station-type-badge ${badgeClass}">
                    ${badgeIcon} ${station.type} Charger
                </div>

                <h3>⚡ ${station.name}</h3>

                <p>${station.available ? "🟢 Available" : "🔴 Currently Busy"}</p>

                <p>₹${station.price}/kWh</p>

                <div class="station-buttons">
                    <button
                        class="favorite-btn"
                        onclick="event.stopPropagation(); addFavorite('${station.name}')">
                        <i class="fa-solid fa-heart"></i> Save
                    </button>

                    <button
                        class="primary-btn"
                        onclick="event.stopPropagation(); bookStation('${station.name}')">
                        <i class="fa-solid fa-calendar-check"></i> Book
                    </button>
                </div>
            </div>
        `;
    });
}

// ================= STATION MODAL =================

function openStationModal(name, type, available, price, lat, lng) {

    document.getElementById("stationModal").classList.add("active");
    document.getElementById("modalTitle").innerText = name;
    document.getElementById("modalType").innerText  = type;
    document.getElementById("modalPrice").innerText = `₹${price}/kWh`;

    let isAvailable = available === "1" || available === "true" || available === true;

    document.getElementById("modalStatus").innerText =
        isAvailable ? "🟢 Available" : "🔴 Busy";

    // RANDOM IMAGES
    const images = [
        "https://images.unsplash.com/photo-1593941707882-a5bac6861d75?q=80&w=1200&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1621905252507-b35492cc74b4?q=80&w=1200&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1639399552304-9f05b6d4e4e6?q=80&w=1200&auto=format&fit=crop"
    ];

    document.getElementById("modalImage").src =
        images[Math.floor(Math.random() * images.length)];

    // BOOK BUTTON
    document.getElementById("bookNowBtn").onclick = () => bookStation(name);

    // FAVORITE BUTTON
    document.getElementById("favoriteNowBtn").onclick = () => addFavorite(name);

    // NAVIGATE BUTTON
    document.getElementById("navigateBtn").onclick = () => navigateTo(lat, lng, name);

    // MAP FLY
    map.flyTo([lat, lng], 15, { duration: 2 });
}

// ================= CLOSE MODAL =================

function closeModal() {
    document.getElementById("stationModal").classList.remove("active");
}

window.onclick = function (event) {
    let modal = document.getElementById("stationModal");
    if (event.target === modal) {
        modal.classList.remove("active");
    }
};

// ================= NAVIGATE TO STATION =================

function navigateTo(lat, lng, name) {
    closeModal();

    if (!navigator.geolocation) {
        showToast("❌ Geolocation not supported", "warn");
        return;
    }

    navigator.geolocation.getCurrentPosition(position => {
        let uLat = position.coords.latitude;
        let uLng = position.coords.longitude;

        if (routeControl) {
            map.removeControl(routeControl);
        }

        routeControl = L.Routing.control({
            waypoints: [
                L.latLng(uLat, uLng),
                L.latLng(lat, lng)
            ],
            show: false,
            lineOptions: {
                styles: [{ color: '#3b82f6', weight: 6, opacity: 0.85 }]
            },
            createMarker: () => null
        }).addTo(map);

        map.flyTo([lat, lng], 14, { duration: 2 });

        showToast(`🗺 Navigating to ${name}`, "info");
    }, () => {
        showToast("❌ Location access denied", "warn");
    });
}

// ================= CLEAR MARKERS =================

function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

// ================= COUNTER =================

function animateCounter(id, target) {
    let element = document.getElementById(id);
    let count   = 0;
    let speed   = Math.max(20, Math.floor(800 / target));

    let interval = setInterval(() => {
        count++;
        element.innerText = count;
        if (count >= target) clearInterval(interval);
    }, speed);
}

// ================= STATS =================

function updateStats() {
    let fast      = stations.filter(s => s.type === "Fast").length;
    let available = stations.filter(s => s.available).length;

    animateCounter("totalStations", stations.length);
    animateCounter("fastCount",     fast);
    animateCounter("availableCount", available);
}

// ================= SEARCH =================

function searchStation() {
    let input = document.getElementById("searchBox").value.toLowerCase();

    let filtered = stations.filter(station =>
        station.name.toLowerCase().includes(input)
    );

    renderStations(filtered);

    document.getElementById("result").innerText =
        filtered.length > 0
        ? `✅ Found ${filtered.length} station(s)`
        : "❌ No station found";
}

// ================= SHOW ALL =================

function showAll() {
    renderStations(stations);
    document.getElementById("result").innerText =
        `📍 Showing all ${stations.length} stations`;
    showToast("Showing all stations", "info");
}

// ================= FAST =================

function showFast() {
    let filtered = stations.filter(s => s.type === "Fast");
    renderStations(filtered);
    document.getElementById("result").innerText =
        `⚡ ${filtered.length} fast chargers`;
    showToast(`⚡ ${filtered.length} fast chargers found`, "info");
}

// ================= SLOW =================

function showSlow() {
    let filtered = stations.filter(s => s.type === "Slow");
    renderStations(filtered);
    document.getElementById("result").innerText =
        `🐢 ${filtered.length} slow chargers`;
}

// ================= SORT BY PRICE =================

function sortByPrice() {
    let sorted = [...stations].sort((a, b) => a.price - b.price);
    renderStations(sorted);
    document.getElementById("result").innerText =
        "💰 Sorted: cheapest first";
    showToast("💰 Sorted by price", "info");
}

// ================= SORT BY AVAILABILITY =================

function showAvailable() {
    let filtered = stations.filter(s => s.available);
    renderStations(filtered);
    document.getElementById("result").innerText =
        `🟢 ${filtered.length} available right now`;
    showToast(`🟢 ${filtered.length} stations available`, "success");
}

// ================= ZOOM =================

function zoomTo(lat, lng) {
    map.flyTo([lat, lng], 15, { duration: 2 });
}

// ================= DISTANCE =================

function getDistance(lat1, lng1, lat2, lng2) {
    let R    = 6371;
    let dLat = (lat2 - lat1) * Math.PI / 180;
    let dLng = (lng2 - lng1) * Math.PI / 180;

    let a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLng / 2) * Math.sin(dLng / 2);

    let c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// ================= FIND NEAREST =================

function findNearest() {
    if (!navigator.geolocation) {
        showToast("Geolocation not supported", "warn");
        return;
    }

    showToast("📍 Finding your location...", "info");

    navigator.geolocation.getCurrentPosition(position => {
        let uLat = position.coords.latitude;
        let uLng = position.coords.longitude;

        let nearest     = null;
        let minDistance = Infinity;

        stations.forEach(station => {
            let dist = getDistance(uLat, uLng, station.lat, station.lng);
            if (dist < minDistance) {
                minDistance = dist;
                nearest     = station;
            }
        });

        if (nearest) {
            map.flyTo([nearest.lat, nearest.lng], 14, { duration: 2 });

            if (routeControl) map.removeControl(routeControl);

            routeControl = L.Routing.control({
                waypoints: [
                    L.latLng(uLat, uLng),
                    L.latLng(nearest.lat, nearest.lng)
                ],
                show: false,
                lineOptions: {
                    styles: [{ color: '#3b82f6', weight: 6, opacity: 0.85 }]
                },
                createMarker: () => null
            }).addTo(map);

            document.getElementById("nearestDistance").innerText =
                minDistance.toFixed(2) + " km";

            document.getElementById("result").innerText =
                `⚡ Nearest: ${nearest.name} (${minDistance.toFixed(2)} km)`;

            showToast(`⚡ Nearest: ${nearest.name}`, "success");
        }
    }, () => {
        showToast("❌ Location access denied", "warn");
    });
}

// ================= SHOW NEARBY =================

function showNearby() {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(position => {
        let uLat = position.coords.latitude;
        let uLng = position.coords.longitude;

        let nearby = stations.filter(station =>
            getDistance(uLat, uLng, station.lat, station.lng) <= 5
        );

        renderStations(nearby);

        document.getElementById("result").innerText =
            `📍 ${nearby.length} stations within 5 km`;

        showToast(`${nearby.length} nearby stations found`, "info");
    }, () => {
        showToast("❌ Location access denied", "warn");
    });
}

// ================= FAVORITES =================

function addFavorite(name) {
    let favorites = JSON.parse(localStorage.getItem("favorites")) || [];

    if (!favorites.includes(name)) {
        favorites.push(name);
        localStorage.setItem("favorites", JSON.stringify(favorites));
        showToast(`❤️ ${name} saved to favorites`, "success");
    } else {
        showToast("Already in your favorites", "info");
    }
}

// ================= BOOKING =================

function bookStation(stationName) {
    closeModal();
    showToast(`⚡ Booking ${stationName}...`, "info");
    setTimeout(() => {
        window.location.href = `/book/${encodeURIComponent(stationName)}`;
    }, 900);
}

// ================= DARK MODE =================

function toggleDarkMode() {
    document.body.classList.toggle("light-mode");
    syncThemeBtn();

    if (document.body.classList.contains("light-mode")) {
        localStorage.setItem("theme", "light");
        showToast("☀️ Light mode on", "info");
    } else {
        localStorage.setItem("theme", "dark");
        showToast("🌙 Dark mode on", "info");
    }
}

function syncThemeBtn() {
    let icon  = document.getElementById("themeIcon");
    let label = document.getElementById("themeLabel");
    if (!icon || !label) return;

    if (document.body.classList.contains("light-mode")) {
        icon.className  = "fa-solid fa-sun";
        label.innerText = "Light";
    } else {
        icon.className  = "fa-solid fa-moon";
        label.innerText = "Dark";
    }
}

// ================= LOAD THEME =================

window.onload = () => {
    if (localStorage.getItem("theme") === "light") {
        document.body.classList.add("light-mode");
    }
    syncThemeBtn();
};

// ================= USER LOCATION =================

if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(position => {
        userLat = position.coords.latitude;
        userLng = position.coords.longitude;

        L.circleMarker([userLat, userLng], {
            radius:      10,
            color:       "#3b82f6",
            fillColor:   "#60a5fa",
            fillOpacity: 1,
            weight:      3
        })
        .addTo(map)
        .bindPopup(`
            <div style="font-family:Poppins;font-size:13px;padding:4px;">
                📍 <b>You are here</b>
            </div>
        `)
        .openPopup();
    });
}

// ================= CHART =================

function createChart() {
    const ctx = document.getElementById("usageChart");

    let fastCount      = stations.filter(s => s.type === "Fast").length;
    let slowCount      = stations.filter(s => s.type === "Slow").length;
    let availableCount = stations.filter(s => s.available).length;
    let busyCount      = stations.filter(s => !s.available).length;
    let total          = stations.length;

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['⚡ Fast Chargers', '🐢 Slow Chargers', '🟢 Available', '🔴 Busy'],
            datasets: [{
                label: 'Stations',
                data: [fastCount, slowCount, availableCount, busyCount],
                backgroundColor: [
                    'rgba(59,130,246,0.85)',
                    'rgba(34,197,94,0.85)',
                    'rgba(234,179,8,0.85)',
                    'rgba(239,68,68,0.85)'
                ],
                borderColor: [
                    '#3b82f6',
                    '#22c55e',
                    '#eab308',
                    '#ef4444'
                ],
                borderWidth: 0,
                borderRadius: 10,
                borderSkipped: false,
                barThickness: 38,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 3.2,
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255,255,255,0.6)',
                        font: { size: 12, family: 'Poppins', weight: '500' },
                        padding: 8
                    },
                    border: { display: false }
                },
                y: {
                    beginAtZero: true,
                    max: Math.max(fastCount, slowCount, availableCount, busyCount) + 2,
                    grid: {
                        color: 'rgba(255,255,255,0.04)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255,255,255,0.4)',
                        font: { size: 11, family: 'Poppins' },
                        stepSize: 1,
                        padding: 10
                    },
                    border: { display: false, dash: [4, 4] }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15,23,42,0.95)',
                    borderColor: 'rgba(255,255,255,0.08)',
                    borderWidth: 1,
                    padding: 14,
                    cornerRadius: 12,
                    titleColor: 'rgba(255,255,255,0.9)',
                    bodyColor: 'rgba(148,163,184,1)',
                    titleFont: { size: 13, family: 'Poppins', weight: '600' },
                    bodyFont: { size: 12, family: 'Poppins' },
                    callbacks: {
                        title: items => items[0].label.replace(/^.{2} /, ''),
                        label: ctx => `  ${ctx.raw} of ${total} stations  (${Math.round(ctx.raw/total*100)}%)`
                    }
                }
            }
        }
    });
}

// ================= TOAST =================

function showToast(message, type = "success") {
    let toast = document.getElementById("toast");

    toast.className = "";  // reset classes
    toast.classList.add(
        type === "success" ? "toast-success" :
        type === "warn"    ? "toast-warn"    : "toast-info"
    );

    toast.innerHTML = `
        <span style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:18px;">
                ${type === "success" ? "✅" : type === "warn" ? "⚠️" : "🔔"}
            </span>
            ${message}
        </span>
    `;

    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}