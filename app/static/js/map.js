// Global state variables
let map;
let allStations = [];
let stationMarkers = {};
let activeStationId = null;
let autoRefreshInterval = null;
let countdownInterval = null;
let currentRoutePolylines = []; // Store active polylines drawn on the map
let userLocationMarker = null;
let userLocationCircle = null;
let activeReminders = {}; // Store bus and mrt arrival reminders

document.addEventListener('DOMContentLoaded', function() {
    // 1. 初始化 Leaflet 地圖，中心點設在台中核心（台中市政府與捷運站週邊）
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false
    }).setView([24.1528, 120.6656], 14);

    // 2. 載入高級暗色系地圖瓦片 (CartoDB Dark Matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // 3. 實作 GPS 精準定位控制元件
    createGPSControl();

    // 4. 從資料庫讀取所有站點並於地圖渲染
    loadAllStations();

    // 5. 檢查是否有 URL 傳入的指定站點定位參數 (e.g. ?station=HUB_01)
    handleUrlParams();

    // 6. 初始化載入「我的收藏」Tab 列表
    loadFavoritesSidebar();

    // 7. 動態建立高級 Toast 提示容器
    if (!document.getElementById('custom-toast-container')) {
        const container = document.createElement('div');
        container.id = 'custom-toast-container';
        document.body.appendChild(container);
    }
});

// ==========================================
// 1. 站點與標記點渲染邏輯
// ==========================================
function loadAllStations() {
    fetch('/api/stations')
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success') {
                allStations = res.data;
                populateRouteDropdowns(allStations);
                
                // 渲染地圖標記點
                allStations.forEach(station => {
                    // 依運具類型選取發光 DivIcon
                    let iconClass = 'marker-bus';
                    let iconHtml = '<i class="fa-solid fa-bus"></i>';
                    
                    if (station.transport_type === 'mrt') {
                        iconClass = 'marker-mrt';
                        iconHtml = '<i class="fa-solid fa-subway"></i>';
                    } else if (station.transport_type === 'transfer') {
                        iconClass = 'marker-transfer';
                        iconHtml = '<i class="fa-solid fa-arrows-spin"></i>';
                    }
                    
                    const customIcon = L.divIcon({
                        className: `custom-marker ${iconClass}`,
                        html: iconHtml,
                        iconSize: [32, 32],
                        iconAnchor: [16, 16]
                    });

                    const marker = L.marker([station.lat, station.lon], { icon: customIcon }).addTo(map);
                    
                    // 滑鼠懸停顯示站點小氣泡
                    marker.bindTooltip(`
                        <div style="font-family: 'Outfit', sans-serif; font-weight:700;">
                            ${station.station_name} 
                            <span class="badge bg-dark ms-1" style="font-size:0.65rem;">
                                ${station.transport_type === 'transfer' ? '轉乘樞紐' : (station.transport_type === 'mrt' ? '捷運' : '公車')}
                            </span>
                        </div>
                    `, { direction: 'top', offset: [0, -10] });

                    // 點擊標記與側邊欄聯動
                    marker.on('click', () => {
                        selectStation(station.station_id);
                    });

                    stationMarkers[station.station_id] = marker;
                });
            }
        })
        .catch(err => console.error("無法載入站點資訊：", err));
}

// 選擇某個站點，載入即時動態
function selectStation(stationId) {
    activeStationId = stationId;
    switchTab('live');
    
    // 平滑飛往該標記
    const station = allStations.find(s => s.station_id === stationId);
    if (station) {
        map.flyTo([station.lat, station.lon], 16, { animate: true, duration: 1 });
    }

    const container = document.getElementById('sidebar-live-content');
    container.innerHTML = `
        <div class="station-card">
            <span class="transport-tag tag-${station.transport_type}">
                ${station.transport_type === 'transfer' ? '🔄 轉乘樞紐' : (station.transport_type === 'mrt' ? '🚇 捷運' : '🚌 公車')}
            </span>
            <h2 class="station-title">${station.station_name}</h2>
            
            <div class="d-flex gap-2 mb-3">
                <button class="btn btn-outline-info btn-sm flex-1" onclick="setRouteStation('start', '${station.station_id}')">
                    <i class="fa-solid fa-circle-play me-1"></i>設為起點
                </button>
                <button class="btn btn-outline-danger btn-sm flex-1" onclick="setRouteStation('end', '${station.station_id}')">
                    <i class="fa-solid fa-circle-stop me-1"></i>設為終點
                </button>
            </div>

            <button class="btn btn-premium w-100 mb-3" style="font-size: 0.9rem;" onclick="triggerStationNavigation('${station.station_id}')">
                <i class="fa-solid fa-route me-1"></i>🚶 步行導航與指引
            </button>
            <div id="navigation-panel-container"></div>
            
            <div class="d-flex justify-content-between align-items-center mb-3">
                <button id="fav-btn-${station.station_id}" class="btn btn-sm btn-outline-warning" onclick="toggleFavorite('${station.station_id}')">
                    <i class="fa-regular fa-star me-1"></i>加入收藏
                </button>
                
                <div class="live-indicator">
                    <span class="pulse-dot"></span>
                    <span id="countdown-timer">30s 後更新</span>
                    <button class="btn btn-link p-0 text-cyan ms-2" onclick="refreshActiveStationData()" title="立即重新整理">
                        <i class="fa-solid fa-arrows-rotate" id="refresh-icon"></i>
                    </button>
                </div>
            </div>
            
            <div id="arrival-data">
                <div class="text-center py-4">
                    <div class="spinner-border text-info" role="status"></div>
                    <p class="mt-2 text-muted small">連線 TDX API，更新即時時程中...</p>
                </div>
            </div>
            
            <div class="text-center mt-3 text-muted" style="font-size:0.75rem;">
                數據更新時間：<span id="last-updated-time">--:--:--</span>
            </div>
        </div>
    `;

    // 檢查收藏狀態並更新按鈕外觀
    checkFavoriteStatus(stationId);
    
    // 獲取最新即時數據
    fetchArrivalData(stationId);

    // 重設並啟動自動更新計時器 (目標一：時程準確性)
    resetAutoRefreshTimer(stationId);
}

// ==========================================
// 2. TDX 即時數據抓取與併列呈現 (F-06 / 目標一)
// ==========================================
function fetchArrivalData(stationId) {
    const arrivalContainer = document.getElementById('arrival-data');
    const refreshIcon = document.getElementById('refresh-icon');
    
    if (refreshIcon) refreshIcon.classList.add('fa-spin');

    fetch(`/api/station/${stationId}`)
        .then(res => res.json())
        .then(res => {
            if (refreshIcon) refreshIcon.classList.remove('fa-spin');
            
            if (res.status === 'success') {
                const data = res.data;
                let busHtml = '';
                let mrtHtml = '';
                
                // 1. 公車即時動態 (若有)
                if (data.bus && data.bus.length > 0) {
                    busHtml = `
                        <div class="mb-4">
                            <div class="sub-header">
                                <h6 class="text-info fw-bold"><i class="fa-solid fa-bus me-1"></i> 🚌 公車進站即時倒數</h6>
                                <span class="badge bg-info-subtle text-info small">台中市公車</span>
                            </div>
                            <div class="arrival-list">
                                ${data.bus.map(item => {
                                    const min = Math.floor(item.EstimateTime / 60);
                                    let timeText = `${min} 分鐘`;
                                    let timeClass = 'time-normal';
                                    
                                    if (item.EstimateTime <= 60) {
                                        timeText = '進站中';
                                        timeClass = 'time-soon';
                                    } else if (min > 8) {
                                        timeClass = 'time-later';
                                    }
                                    
                                    const rKey = `${stationId}_bus_${item.RouteName}`;
                                    const isReminderActive = activeReminders[rKey] ? 'active' : '';
                                    
                                    return `
                                        <div class="arrival-item d-flex justify-content-between align-items-center">
                                            <span class="route-num">${item.RouteName} 路公車</span>
                                            <div class="d-flex align-items-center">
                                                <span class="arrival-time ${timeClass}">${timeText}</span>
                                                <button class="reminder-btn ${isReminderActive}" 
                                                        onclick="toggleArrivalReminder(event, '${stationId}', 'bus', '${item.RouteName}', ${item.EstimateTime})" 
                                                        title="設為 3 分鐘到站提醒">
                                                    <i class="fa-solid fa-bell"></i>
                                                </button>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `;
                }

                // 2. 捷運即時發車時刻 (若有)
                if (data.mrt && data.mrt.length > 0) {
                    mrtHtml = `
                        <div>
                            <div class="sub-header">
                                <h6 class="text-secondary fw-bold"><i class="fa-solid fa-subway me-1"></i> 🚇 捷運即時發車時刻</h6>
                                <span class="badge bg-secondary-subtle text-secondary small">台中捷運綠線</span>
                            </div>
                            <div class="arrival-list">
                                ${data.mrt.map(item => {
                                    const min = Math.floor(item.EstimateTime / 60);
                                    let timeText = `${min} 分鐘`;
                                    let timeClass = 'time-normal';
                                    
                                    if (item.EstimateTime <= 180) {
                                        timeClass = 'time-soon';
                                    }
                                    
                                    const rKey = `${stationId}_mrt_${item.Destination}`;
                                    const isReminderActive = activeReminders[rKey] ? 'active' : '';
                                    
                                    return `
                                        <div class="arrival-item d-flex justify-content-between align-items-center">
                                            <span class="route-num">往 ${item.Destination}</span>
                                            <div class="d-flex align-items-center">
                                                <span class="arrival-time ${timeClass}">${timeText}</span>
                                                <button class="reminder-btn ${isReminderActive}" 
                                                        onclick="toggleArrivalReminder(event, '${stationId}', 'mrt', '${item.Destination}', ${item.EstimateTime})" 
                                                        title="設為 3 分鐘到站提醒">
                                                    <i class="fa-solid fa-bell"></i>
                                                </button>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `;
                }

                // 將公車與捷運數據「併列呈現」在同一介面，徹底消除切換選單
                if (busHtml || mrtHtml) {
                    arrivalContainer.innerHTML = busHtml + mrtHtml;
                } else {
                    arrivalContainer.innerHTML = '<div class="text-center py-4 text-muted small">此站點目前無班次即時動態</div>';
                }

                // 觸發提醒檢測
                if (data.bus) checkAndTriggerReminders(stationId, 'bus', data.bus);
                if (data.mrt) checkAndTriggerReminders(stationId, 'mrt', data.mrt);

                // 更新最後刷新時間標記
                const now = new Date();
                const timeString = now.toTimeString().split(' ')[0];
                const lastUpdatedSpan = document.getElementById('last-updated-time');
                if (lastUpdatedSpan) lastUpdatedSpan.innerText = timeString;

            } else {
                arrivalContainer.innerHTML = '<p class="text-danger text-center">無法取得即時數據，請稍後再試</p>';
            }
        })
        .catch(err => {
            if (refreshIcon) refreshIcon.classList.remove('fa-spin');
            arrivalContainer.innerHTML = '<p class="text-danger text-center">網路連線異常，載入即時看板失敗</p>';
        });
}

// 重新整理當前站點
function refreshActiveStationData() {
    if (activeStationId) {
        fetchArrivalData(activeStationId);
        resetAutoRefreshTimer(activeStationId);
    }
}

// 重設自動重新整理定時器 (30秒)
function resetAutoRefreshTimer(stationId) {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    if (countdownInterval) clearInterval(countdownInterval);

    let secondsLeft = 30;
    const timerSpan = document.getElementById('countdown-timer');
    if (timerSpan) timerSpan.innerText = `${secondsLeft}s 後更新`;

    // 倒數秒數計時器
    countdownInterval = setInterval(() => {
        secondsLeft--;
        if (secondsLeft <= 0) {
            secondsLeft = 30;
        }
        if (timerSpan) timerSpan.innerText = `${secondsLeft}s 後更新`;
    }, 1000);

    // 30秒自動呼叫 API 更新
    autoRefreshInterval = setInterval(() => {
        fetchArrivalData(stationId);
    }, 30000);
}

// ==========================================
// 3. HTML5 Geolocation 精準定位 (目標三)
// ==========================================
function createGPSControl() {
    const GPSControl = L.Control.extend({
        options: { position: 'topleft' },
        onAdd: function() {
            const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-gps');
            container.innerHTML = '<i class="fa-solid fa-location-crosshairs" style="font-size:1.1rem;"></i>';
            container.title = "精準定位我的位置";
            
            container.onclick = function(e) {
                e.stopPropagation();
                triggerGPSLocation();
            };
            return container;
        }
    });
    map.addControl(new GPSControl());
}

function triggerGPSLocation() {
    if (!navigator.geolocation) {
        alert("您的瀏覽器不支援 GPS 定位服務。");
        return;
    }

    // 更改定位按鈕狀態為旋轉載入
    const gpsBtn = document.querySelector('.leaflet-control-gps i');
    if (gpsBtn) gpsBtn.className = "fa-solid fa-spinner fa-spin text-info";

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const accuracy = position.coords.accuracy;

            if (gpsBtn) gpsBtn.className = "fa-solid fa-location-crosshairs";

            // 移除舊的定位標記與圓圈
            if (userLocationMarker) map.removeLayer(userLocationMarker);
            if (userLocationCircle) map.removeLayer(userLocationCircle);

            // 1. 繪製精準定位呼吸脈衝標記
            const gpsIcon = L.divIcon({
                className: 'user-gps-marker',
                html: '<div class="user-gps-dot"></div><div class="user-gps-ring"></div>',
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });
            userLocationMarker = L.marker([lat, lon], { icon: gpsIcon }).addTo(map);

            // 2. 繪製半透明誤差圈 (顯示定位精準度)
            userLocationCircle = L.circle([lat, lon], {
                radius: accuracy,
                color: '#0088ff',
                fillColor: '#0088ff',
                fillOpacity: 0.12,
                weight: 1.5
            }).addTo(map);

            // 3. 地圖平滑飛向使用者定位點並放大
            map.flyTo([lat, lon], 15, { animate: true, duration: 1.2 });
        },
        (error) => {
            if (gpsBtn) gpsBtn.className = "fa-solid fa-location-crosshairs";
            let errMsg = "無法取得您的定位。";
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errMsg = "您拒絕了定位權限授權，請手動開啟瀏覽器定位。";
                    break;
                case error.POSITION_UNAVAILABLE:
                    errMsg = "無法取得位置資訊，請確認 GPS 已開啟。";
                    break;
                case error.TIMEOUT:
                    errMsg = "定位請求逾時，請再試一次。";
                    break;
            }
            alert(errMsg);
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );
}

// ==========================================
// 4. 多運具路線規劃與替代方案渲染 (目標四、五、六、七)
// ==========================================
function populateRouteDropdowns(stations) {
    // 傳統 select 已被 autocomplete search input 取代，無須生成靜態選單
}

function setRouteStation(role, stationId) {
    const station = allStations.find(s => s.station_id === stationId);
    if (station) {
        const typeStr = station.transport_type === 'transfer' ? '轉乘點' : (station.transport_type === 'mrt' ? '捷運' : '公車');
        document.getElementById(`${role}-station-input`).value = `${station.station_name} (${typeStr})`;
        document.getElementById(`${role}-station-id`).value = station.station_id;
        switchTab('route');
    }
}

function planTripRoute() {
    const startId = document.getElementById('start-station-id').value;
    const endId = document.getElementById('end-station-id').value;
    const resultsContainer = document.getElementById('route-results-container');

    if (!startId || !endId) {
        alert("請同時選擇「出發站點」與「目的站點」！您可直接在起訖輸入框內打字搜尋。");
        return;
    }

    if (startId === endId) {
        alert("起點站與終點站不能相同！");
        return;
    }

    resultsContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 text-muted small">後端演算法計算台中最佳路線與雙十票價優惠中...</p>
        </div>
    `;

    // 呼叫後端多方案路線規劃 API
    fetch(`/api/v1/route_plans?start=${startId}&end=${endId}`)
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success') {
                renderRoutePlans(res.plans);
            } else {
                resultsContainer.innerHTML = `<p class="text-danger text-center small">${res.message}</p>`;
            }
        })
        .catch(err => {
            resultsContainer.innerHTML = '<p class="text-danger text-center small">連線逾時，無法加載路徑規劃</p>';
        });
}

function renderRoutePlans(plans) {
    const resultsContainer = document.getElementById('route-results-container');
    resultsContainer.innerHTML = '';

    plans.forEach((plan, index) => {
        const isActive = index === 0 ? 'active' : '';
        const cardId = `plan-card-${plan.id}`;
        
        let segmentDetailsHtml = plan.segments.map(seg => {
            let nodeClass = 'node-walking';
            if (seg.type === 'mrt') nodeClass = 'node-mrt';
            if (seg.type === 'bus') nodeClass = 'node-bus';
            if (seg.type === 'youbike') nodeClass = 'node-youbike';
            
            let fareText = seg.fare !== undefined ? `NT$ ${seg.fare}` : '免費';
            if (seg.fare === 0 && seg.type === 'bus') {
                fareText = '十公里免費 NT$ 0';
            } else if (seg.fare === 0 && seg.type === 'walking') {
                fareText = '免費';
            }
            
            return `
                <div class="segment-item">
                    <div class="segment-node ${nodeClass}"></div>
                    <div class="segment-details">
                        <div class="segment-title">${seg.desc}</div>
                        <div class="segment-sub">
                            <span>${seg.value}</span>
                            <span>•</span>
                            <span class="text-cyan"><i class="fa-regular fa-clock me-1"></i>${seg.minutes} 分鐘</span>
                            <span>•</span>
                            <span class="text-success"><i class="fa-solid fa-hand-holding-dollar me-1"></i>${fareText}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        resultsContainer.innerHTML += `
            <div class="plan-card ${isActive}" id="${cardId}" onclick="selectRoutePlan(${JSON.stringify(plan).replace(/"/g, '&quot;')})">
                <div class="plan-header">
                    <span class="plan-name">${plan.name}</span>
                    <div class="plan-price-time">
                        <span class="plan-time"><i class="fa-regular fa-clock me-1"></i>${plan.total_minutes} 分鐘</span>
                        <span class="plan-price"><i class="fa-solid fa-dollar-sign me-1"></i>NT$ ${plan.total_fare}</span>
                    </div>
                </div>
                <div class="plan-desc">${plan.description}</div>
                
                <div class="segment-timeline">
                    ${segmentDetailsHtml}
                </div>
            </div>
        `;
    });

    // 預設渲染與繪製第一個方案 (捷運優先)
    if (plans.length > 0) {
        drawRouteOnMap(plans[0]);
    }
}

function selectRoutePlan(plan) {
    // 移除其他方案的高亮 active 樣式
    document.querySelectorAll('.plan-card').forEach(card => card.classList.remove('active'));
    
    // 為被點擊方案加入 active 高亮
    const card = document.getElementById(`plan-card-${plan.id}`);
    if (card) card.classList.add('active');

    // 繪製地圖折線並縮放至最適合範圍
    drawRouteOnMap(plan);
}

// 繪製地圖分段多色折線 (L.polyline)
function drawRouteOnMap(plan) {
    // 1. 清除舊有繪製線段
    currentRoutePolylines.forEach(line => map.removeLayer(line));
    currentRoutePolylines = [];

    // 2. 建立新線段。我們根據 segments 來決定繪製顏色：公車為藍色，捷運為紫色，步行/Youbike為橘色與灰色虛線
    const path = plan.path;
    if (!path || path.length < 2) return;

    // 簡化起見：我們繪製一條包含彩虹漸變的高級複合路網
    const planId = plan.id;
    let lineColor = '#0ea5e9'; // 預設藍
    let dashStyle = null;

    if (planId === 'plan_mrt') {
        // 捷運方案為多色分段拼接：
        // 步行段: Dotted Gray, 捷運段: Purple, 公車段: Blue
        const seg1 = L.polyline([path[0], path[1]], { color: '#94a3b8', weight: 4, dashArray: '5, 8' });
        const seg2 = L.polyline([path[1], path[2]], { color: '#a855f7', weight: 6 });
        const seg3 = L.polyline([path[2], path[3]], { color: '#0ea5e9', weight: 5 });
        
        seg1.addTo(map);
        seg2.addTo(map);
        seg3.addTo(map);
        
        currentRoutePolylines.push(seg1, seg2, seg3);
    } else if (planId === 'plan_bus') {
        // 公車方案為整條深藍色發光線
        const line = L.polyline(path, { color: '#0ea5e9', weight: 5, opacity: 0.95 }).addTo(map);
        currentRoutePolylines.push(line);
    } else if (planId === 'plan_green') {
        // 綠能方案為 YouBike橘色線 + 步行虛線
        const seg1 = L.polyline([path[0], path[1]], { color: '#f59e0b', weight: 5 });
        const seg2 = L.polyline([path[1], path[2]], { color: '#94a3b8', weight: 4, dashArray: '5, 8' });
        
        seg1.addTo(map);
        seg2.addTo(map);
        
        currentRoutePolylines.push(seg1, seg2);
    }

    // 3. 自動縮放地圖至能完美包覆整條線路與站點 (地圖適配性)
    const bounds = L.latLngBounds(path);
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
}

// ==========================================
// 5. 個人化常用收藏管理邏輯 (F-05)
// ==========================================
function loadFavoritesSidebar() {
    const container = document.getElementById('sidebar-fav-list');
    
    fetch('/api/favorites')
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success') {
                const favIds = res.data;
                if (favIds.length === 0) {
                    container.innerHTML = `
                        <div class="text-center py-4 text-muted">
                            <p class="small">目前沒有收藏的站點。<br>在大眾運輸站點面板點擊「加入收藏」以快速管理。</p>
                        </div>
                    `;
                    return;
                }
                
                let html = '';
                favIds.forEach(id => {
                    const station = allStations.find(s => s.station_id === id);
                    if (station) {
                        const typeStr = station.transport_type === 'transfer' ? '雙運具轉乘點' : (station.transport_type === 'mrt' ? '捷運站' : '公車站');
                        html += `
                            <div class="fav-sidebar-card" onclick="selectStation('${station.station_id}')">
                                <div class="fav-info">
                                    <span class="fav-name">${station.station_name}</span>
                                    <span class="fav-meta"><i class="fa-solid fa-location-dot me-1"></i>${typeStr}</span>
                                </div>
                                <button class="fav-action-btn" onclick="deleteFavoriteSidebar(event, '${station.station_id}')" title="移除">
                                    <i class="fa-solid fa-trash-can"></i>
                                </button>
                            </div>
                        `;
                    }
                });
                container.innerHTML = html;
            }
        })
        .catch(err => console.error("無法加載常用收藏：", err));
}

function checkFavoriteStatus(stationId) {
    const btn = document.getElementById(`fav-btn-${stationId}`);
    if (!btn) return;

    fetch('/api/favorites')
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success') {
                const isFav = res.data.includes(stationId);
                if (isFav) {
                    btn.className = "btn btn-sm btn-warning text-dark fw-bold";
                    btn.innerHTML = '<i class="fa-solid fa-star me-1"></i>已收藏';
                } else {
                    btn.className = "btn btn-sm btn-outline-warning";
                    btn.innerHTML = '<i class="fa-regular fa-star me-1"></i>加入收藏';
                }
            }
        });
}

function toggleFavorite(stationId) {
    const btn = document.getElementById(`fav-btn-${stationId}`);
    const isAlreadyFav = btn.classList.contains('btn-warning');
    
    const url = isAlreadyFav ? `/favorites/delete/${stationId}` : '/favorites/add';
    const body = isAlreadyFav ? null : JSON.stringify({ station_id: stationId });
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: body
    })
    .then(res => res.json())
    .then(res => {
        if (res.status === 'success') {
            // 即時切換外觀，無延遲感 (微互動優化)
            if (isAlreadyFav) {
                btn.className = "btn btn-sm btn-outline-warning";
                btn.innerHTML = '<i class="fa-regular fa-star me-1"></i>加入收藏';
            } else {
                btn.className = "btn btn-sm btn-warning text-dark fw-bold";
                btn.innerHTML = '<i class="fa-solid fa-star me-1"></i>已收藏';
            }
            // 重新載入側邊欄收藏列表
            loadFavoritesSidebar();
        }
    })
    .catch(err => alert("收藏操作失敗，請稍候重試"));
}

function deleteFavoriteSidebar(event, stationId) {
    event.stopPropagation(); // 阻止氣泡傳遞，以免觸發 selectStation 飛航
    
    if (!confirm("確定要將此站點移出收藏嗎？")) return;
    
    fetch(`/favorites/delete/${stationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(res => res.json())
    .then(res => {
        if (res.status === 'success') {
            loadFavoritesSidebar();
            // 如果當前側邊欄剛好是這站點，也更新其按鈕外觀
            if (activeStationId === stationId) {
                const btn = document.getElementById(`fav-btn-${stationId}`);
                if (btn) {
                    btn.className = "btn btn-sm btn-outline-warning";
                    btn.innerHTML = '<i class="fa-regular fa-star me-1"></i>加入收藏';
                }
            }
        }
    });
}

// ==========================================
// 6. UI 其他控制輔助邏輯
// ==========================================
function switchTab(tabName) {
    // 移除所有 Tab 按鈕與內容的 active 狀態
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content-panel').forEach(panel => panel.classList.remove('active'));

    // 為對應 Tab 加上 active 狀態
    const targetBtn = document.getElementById(`tab-${tabName}`);
    const targetContent = document.getElementById(`content-${tabName}`);
    
    if (targetBtn) targetBtn.classList.add('active');
    if (targetContent) targetContent.classList.add('active');
}

function handleUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const stationId = urlParams.get('station');
    if (stationId) {
        // 延遲一下待站點加載完成後再選擇，確保地圖實體已存在
        setTimeout(() => {
            selectStation(stationId);
        }, 800);
    }
}

// ==========================================
// 7. 到站前 3 分鐘提醒與系統通知
// ==========================================
function toggleArrivalReminder(event, stationId, type, routeName, initialEstimate) {
    event.stopPropagation();
    
    if (initialEstimate <= 180) {
        showPremiumToast("已在範圍內", `該車次目前已在 3 分鐘內即將到站，不需再設定提醒囉！`, type);
        return;
    }

    const key = `${stationId}_${type}_${routeName}`;
    const btn = event.currentTarget;
    const station = allStations.find(s => s.station_id === stationId);
    const stationName = station ? station.station_name : "轉乘站點";

    if (activeReminders[key]) {
        delete activeReminders[key];
        btn.classList.remove('active');
        showPremiumToast("取消提醒", `已取消 ${routeName} 的到站提醒。`, type);
    } else {
        if (Notification.permission !== "granted" && Notification.permission !== "denied") {
            Notification.requestPermission();
        }

        activeReminders[key] = {
            stationId: stationId,
            stationName: stationName,
            transportType: type,
            routeName: routeName,
            notified: false
        };
        btn.classList.add('active');
        showPremiumToast("設定成功", `已成功設定 ${routeName} ➔ 當車次到站前 3 分鐘時會跳出通知。`, type);
    }
}

function checkAndTriggerReminders(stationId, type, dataList) {
    if (!dataList || dataList.length === 0) return;
    
    dataList.forEach(item => {
        const routeName = type === 'bus' ? item.RouteName : item.Destination;
        const estSec = item.EstimateTime;
        const key = `${stationId}_${type}_${routeName}`;
        
        if (activeReminders[key] && !activeReminders[key].notified) {
            if (estSec <= 180 && estSec >= 0) {
                activeReminders[key].notified = true;
                triggerSystemNotification(activeReminders[key]);
                
                setTimeout(() => {
                    delete activeReminders[key];
                    if (activeStationId === stationId) {
                        fetchArrivalData(stationId);
                    }
                }, 3000);
            }
        }
    });
}

function triggerSystemNotification(reminder) {
    const title = `🔔 乘車到站提醒！`;
    const body = `${reminder.routeName} 即將在 3 分鐘內抵達【${reminder.stationName}】，請準備上車！`;
    
    if (Notification.permission === "granted") {
        try {
            new Notification(title, {
                body: body
            });
        } catch (e) {
            console.error("系統通知觸發失敗：", e);
        }
    }
    
    showPremiumToast(
        "即將到站！", 
        `${reminder.routeName} 即將在 3 分鐘內抵達【${reminder.stationName}】，請準備上車。`, 
        reminder.transportType, 
        10000
    );
    
    if ('speechSynthesis' in window) {
        const text = reminder.transportType === 'bus' 
            ? `${reminder.routeName}公車即將抵達${reminder.stationName}，請準備上車。`
            : `往${reminder.routeName}捷運即將抵達${reminder.stationName}，請準備上車。`;
        const speech = new SpeechSynthesisUtterance(text);
        speech.lang = 'zh-TW';
        speech.rate = 1.0;
        window.speechSynthesis.speak(speech);
    }
}

function showPremiumToast(title, message, type = 'warning', duration = 5000) {
    const container = document.getElementById('custom-toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `premium-toast toast-${type}`;
    
    const icon = type === 'bus' ? 'fa-bus' : (type === 'mrt' ? 'fa-subway' : 'fa-bell');
    
    toast.innerHTML = `
        <div class="premium-toast-icon"><i class="fa-solid ${icon}"></i></div>
        <div class="premium-toast-body">
            <div class="premium-toast-title">${title}</div>
            <div class="premium-toast-desc">${message}</div>
        </div>
        <button class="premium-toast-close" onclick="this.parentElement.remove()"><i class="fa-solid fa-xmark"></i></button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-20px) scale(0.95)';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

// ==========================================
// 8. 點對點 GPS 導航指引
// ==========================================
function triggerStationNavigation(stationId) {
    const station = allStations.find(s => s.station_id === stationId);
    if (!station) return;

    if (!navigator.geolocation) {
        alert("您的瀏覽器不支援定位，無法啟用導航指引。");
        return;
    }

    showPremiumToast("定位中", "正在獲取您當前的精準 GPS 位置...", "info");

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const userLat = position.coords.latitude;
            const userLon = position.coords.longitude;
            const accuracy = position.coords.accuracy;

            if (userLocationMarker) map.removeLayer(userLocationMarker);
            if (userLocationCircle) map.removeLayer(userLocationCircle);

            const gpsIcon = L.divIcon({
                className: 'user-gps-marker',
                html: '<div class="user-gps-dot"></div><div class="user-gps-ring"></div>',
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });
            userLocationMarker = L.marker([userLat, userLon], { icon: gpsIcon }).addTo(map);

            userLocationCircle = L.circle([userLat, userLon], {
                radius: accuracy,
                color: '#0088ff',
                fillColor: '#0088ff',
                fillOpacity: 0.1,
                weight: 1.5
            }).addTo(map);

            currentRoutePolylines.forEach(line => map.removeLayer(line));
            currentRoutePolylines = [];

            const navLine = L.polyline([[userLat, userLon], [station.lat, station.lon]], {
                color: '#f59e0b',
                weight: 4,
                dashArray: '6, 10',
                opacity: 0.9
            }).addTo(map);
            currentRoutePolylines.push(navLine);

            const distKm = getDistance(userLat, userLon, station.lat, station.lon);
            let distText = `${Math.round(distKm * 1000)} 公尺`;
            if (distKm >= 1.0) {
                distText = `${distKm} 公里`;
            }
            
            const walkTimeMinutes = Math.max(1, Math.round(distKm * 15));

            const bounds = L.latLngBounds([[userLat, userLon], [station.lat, station.lon]]);
            map.fitBounds(bounds, { padding: [60, 60], maxZoom: 16 });

            const navContainer = document.getElementById('navigation-panel-container');
            if (navContainer) {
                navContainer.innerHTML = `
                    <div class="navigation-panel">
                        <div class="fw-bold text-warning mb-2"><i class="fa-solid fa-person-hiking me-1"></i> 🚶 步行導航引導中</div>
                        <div class="nav-metric-row">
                            <div class="nav-metric-item"><i class="fa-solid fa-route text-info"></i> 距離：${distText}</div>
                            <div class="nav-metric-item"><i class="fa-solid fa-clock text-info"></i> 時間：約 ${walkTimeMinutes} 分鐘</div>
                        </div>
                        <div class="text-muted small mb-2" style="font-size: 0.75rem;">
                            依黃色虛線指示前行即可抵達 **${station.station_name}**，無須開啟外部地圖。
                        </div>
                        <a href="https://www.google.com/maps/dir/?api=1&origin=${userLat},${userLon}&destination=${station.lat},${station.lon}&travelmode=walking" 
                           target="_blank" class="btn btn-outline-info btn-sm w-100 py-1" style="font-size:0.75rem; border-radius: 8px;">
                            <i class="fa-solid fa-map-location-dot me-1"></i>開啟外部 Google Maps 行動導航
                        </a>
                    </div>
                `;
            }
            
            showPremiumToast("導航已啟用", `已為您規劃至 ${station.station_name} 的步行路徑！`, "success");
        },
        (error) => {
            showPremiumToast("定位失敗", "無法取得您的精準位置，請確認 GPS 開啟與權限允許。", "danger");
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );
}

function getDistance(lat1, lon1, lat2, lon2) {
    const R = 6371.0;
    const dlat = (lat2 - lat1) * Math.PI / 180;
    const dlon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dlat / 2) * Math.sin(dlat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dlon / 2) * Math.sin(dlon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c * 100) / 100;
}

// ==========================================
// 9. 站點即時搜尋與地圖聯動
// ==========================================
function handleStationSearch() {
    const query = document.getElementById('station-search-input').value.trim().toLowerCase();
    const resultsContainer = document.getElementById('search-results-list');
    const clearBtn = document.getElementById('clear-search-btn');

    if (!query) {
        resultsContainer.style.display = 'none';
        clearBtn.style.display = 'none';
        return;
    }

    clearBtn.style.display = 'block';

    // 進行模糊比對。allStations 在載入時已被加載
    const matched = allStations.filter(station => {
        return station.station_name.toLowerCase().includes(query) || 
               station.transport_type.toLowerCase().includes(query);
    });

    if (matched.length === 0) {
        resultsContainer.innerHTML = '<div class="text-center text-muted small py-3">查無符合的站點</div>';
        resultsContainer.style.display = 'flex';
        return;
    }

    let html = '';
    matched.slice(0, 10).forEach(station => {
        let typeText = '公車';
        let typeClass = 'bg-info text-dark';
        if (station.transport_type === 'mrt') {
            typeText = '捷運';
            typeClass = 'bg-secondary text-white';
        } else if (station.transport_type === 'transfer') {
            typeText = '轉乘樞紐';
            typeClass = 'bg-success text-white';
        }

        html += `
            <div class="search-result-item" onmousedown="selectSearchedStation('${station.station_id}')">
                <span class="search-result-name">${station.station_name}</span>
                <span class="search-result-type badge ${typeClass}">${typeText}</span>
            </div>
        `;
    });

    resultsContainer.innerHTML = html;
    resultsContainer.style.display = 'flex';
}

function selectSearchedStation(stationId) {
    // 隱藏搜尋下拉結果
    document.getElementById('search-results-list').style.display = 'none';
    
    // 觸發站點選擇，地圖平滑飛航並載入動態
    selectStation(stationId);
}

function clearSearchInput() {
    document.getElementById('station-search-input').value = '';
    document.getElementById('search-results-list').style.display = 'none';
    document.getElementById('clear-search-btn').style.display = 'none';
}

// ==========================================
// 10. 路線規劃起訖點打字搜尋與聯動
// ==========================================
function handleRouteSearch(role) {
    const query = document.getElementById(`${role}-station-input`).value.trim().toLowerCase();
    const resultsContainer = document.getElementById(`${role}-search-results`);

    // 當沒有輸入時，預設顯示前 8 個常用站點
    let matched = allStations;
    if (query) {
        matched = allStations.filter(station => {
            return station.station_name.toLowerCase().includes(query) || 
                   station.transport_type.toLowerCase().includes(query);
        });
    }

    if (matched.length === 0) {
        resultsContainer.innerHTML = '<div class="text-center text-muted small py-3">查無符合的站點</div>';
        resultsContainer.style.display = 'flex';
        return;
    }

    let html = '';
    matched.slice(0, 8).forEach(station => {
        let typeText = '公車';
        let typeClass = 'bg-info text-dark';
        if (station.transport_type === 'mrt') {
            typeText = '捷運';
            typeClass = 'bg-secondary text-white';
        } else if (station.transport_type === 'transfer') {
            typeText = '轉乘點';
            typeClass = 'bg-success text-white';
        }

        html += `
            <div class="search-result-item" onmousedown="selectRouteStation('${role}', '${station.station_id}', '${station.station_name}', '${typeText}')">
                <span class="search-result-name">${station.station_name}</span>
                <span class="search-result-type badge ${typeClass}">${typeText}</span>
            </div>
        `;
    });

    resultsContainer.innerHTML = html;
    resultsContainer.style.display = 'flex';
}

function selectRouteStation(role, stationId, stationName, typeStr) {
    document.getElementById(`${role}-station-input`).value = `${stationName} (${typeStr})`;
    document.getElementById(`${role}-station-id`).value = stationId;
    document.getElementById(`${role}-search-results`).style.display = 'none';
}

// 點擊頁面其他地方時，隱藏搜尋下拉選單（包含起訖站和一般站點搜尋）
document.addEventListener('click', function(e) {
    // 站點即時搜尋
    const searchContainer = document.querySelector('.search-container');
    const searchResults = document.getElementById('search-results-list');
    if (searchContainer && !searchContainer.contains(e.target) && searchResults) {
        searchResults.style.display = 'none';
    }

    // 起點搜尋
    const startContainer = document.getElementById('start-search-results');
    const startInput = document.getElementById('start-station-input');
    if (startInput && !startInput.contains(e.target) && startContainer && !startContainer.contains(e.target)) {
        startContainer.style.display = 'none';
    }

    // 終點搜尋
    const endContainer = document.getElementById('end-search-results');
    const endInput = document.getElementById('end-station-input');
    if (endInput && !endInput.contains(e.target) && endContainer && !endContainer.contains(e.target)) {
        endContainer.style.display = 'none';
    }
});
