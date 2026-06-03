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
    // 1. 初始化地圖，中心點設在台中火車站附近
    const map = L.map('map').setView([24.1373, 120.6856], 14);

    // 使用極致美觀的 Dark Mode 地圖樣式
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    let activeStationId = null;
    let refreshInterval = null;
    let refreshCountdown = 10;
    let countdownInterval = null;

    // 2. 自訂站點圖示 (Bus / MRT)
    function createCustomIcon(type, name) {
        const colorClass = type.toLowerCase() === 'bus' ? 'icon-bus' : 'icon-mrt';
        const iconChar = type.toLowerCase() === 'bus' ? '🚌' : '🚇';
        return L.divIcon({
            className: 'custom-div-icon',
            html: `<div class="marker-pin ${colorClass}"><span>${iconChar}</span></div>`,
            iconSize: [36, 36],
            iconAnchor: [18, 36],
            popupAnchor: [0, -30]
        });
    }

    // 3. 從後端載入所有站點
    const markers = {};
    fetch('/api/stations')
        .then(response => response.json())
        .then(res => {
            if (res.status === 'success' && res.data) {
                res.data.forEach(station => {
                    const icon = createCustomIcon(station.transport_type, station.station_name);
                    const marker = L.marker([station.lat, station.lon], { icon: icon }).addTo(map);
                    
                    // 滑鼠懸停顯示氣泡提示
                    marker.bindTooltip(`<b>${station.station_name}</b><br><small>${station.transport_type === 'Bus' ? '公車站' : '捷運站'}</small>`, {
                        direction: 'top',
                        opacity: 0.9
                    });

                    marker.on('click', () => {
                        selectStation(station.station_id);
                    });
                    
                    markers[station.station_id] = marker;
                });

                // 檢查 URL Query 參數是否有指定 station_id (從收藏頁點選「在地圖查看」回來)
                const urlParams = new URLSearchParams(window.location.search);
                const queryStationId = urlParams.get('station_id');
                if (queryStationId && markers[queryStationId]) {
                    selectStation(queryStationId);
                    // 移動地圖中心點並放大
                    const marker = markers[queryStationId];
                    map.setView(marker.getLatLng(), 16);
                }
            }
        })
        .catch(err => console.error("無法載入站點資訊：", err));

    // 4. 點選站點邏輯
    function selectStation(stationId) {
        activeStationId = stationId;
        
        // 清除舊的計時器
        clearInterval(refreshInterval);
        clearInterval(countdownInterval);

        // 初始化側邊欄框架
        renderSidebarSkeleton();

        // 首次載入數據
        fetchStationRealtimeData(stationId);

        // 設定 10 秒自動重新整理
        refreshCountdown = 10;
        setupAutoRefresh(stationId);
    }

    // 5. 渲染側邊欄架構與骨架
    function renderSidebarSkeleton() {
        const sidebarContent = document.getElementById('sidebar-content');
        sidebarContent.innerHTML = `
            <div class="station-detail-container">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span id="sidebar-transport-tag" class="transport-tag">載入中</span>
                    <div id="refresh-status" class="refresh-indicator">
                        <span class="pulse-dot"></span>
                        <span id="refresh-text" class="text-muted small">即時更新中 (10s)</span>
                    </div>
                </div>
                <h2 id="sidebar-title" class="station-title mb-3">載入中...</h2>
                
                <div id="favorite-btn-container" class="mb-4">
                    <button class="btn btn-outline-secondary w-100 disabled" type="button">
                        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        檢查收藏狀態...
                    </button>
                </div>

                <div id="arrival-data">
                    <div class="text-center py-5">
                        <div class="spinner-border text-info" role="status"></div>
                        <p class="mt-2 text-muted">讀取即時到站數據中...</p>
                    </div>
                </div>
            </div>
        `;
    }

    // 6. 取得即時數據與收藏狀態
    function fetchStationRealtimeData(stationId) {
        // A. 取得即時到站資訊
        fetch(`/api/station/${stationId}`)
            .then(response => response.json())
            .then(res => {
                if (res.status === 'success' && activeStationId === stationId) {
                    const data = res.data;
                    
                    // 更新標題與 Tag
                    const tagEl = document.getElementById('sidebar-transport-tag');
                    tagEl.className = `transport-tag tag-${data.transport_type.toLowerCase()}`;
                    tagEl.innerText = data.transport_type === 'Bus' ? '公車' : '捷運';
                    
                    document.getElementById('sidebar-title').innerText = data.station_name;

                    // 更新到站資訊
                    updateArrivalsUI(data);
                }
            })
            .catch(err => {
                console.error(err);
                if (activeStationId === stationId) {
                    document.getElementById('arrival-data').innerHTML = `
                        <div class="alert alert-danger py-2 text-center" role="alert">
                            ⚠️ 無法取得即時交通數據，請稍後再試。
                        </div>
                    `;
                }
            });

        // B. 取得收藏狀態
        fetch(`/api/favorites/check/${stationId}`)
            .then(response => response.json())
            .then(res => {
                if (res.status === 'success' && activeStationId === stationId) {
                    renderFavoriteButton(stationId, res.is_favorited);
                }
            })
            .catch(err => console.error("無法檢查收藏狀態：", err));
    }

    // 7. 更新到站清單 UI
    function updateArrivalsUI(data) {
        const arrivalData = document.getElementById('arrival-data');
        let html = '';

        // 處理公車資訊
        if (data.transport_type === 'Bus' || (data.bus && data.bus.length > 0)) {
            html += `
                <div class="mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="text-info fw-bold mb-0">🚌 公車即時到站</h6>
                        <span class="badge bg-secondary-subtle text-secondary small">TDX 即時</span>
                    </div>
                    <div class="arrival-list">
            `;
            if (data.bus && data.bus.length > 0) {
                data.bus.forEach(item => {
                    let timeText = '';
                    let timeClass = '';
                    if (item.EstimateTime <= 0) {
                        timeText = '進站中';
                        timeClass = 'time-soon';
                    } else if (item.EstimateTime <= 60) {
                        timeText = '將到站';
                        timeClass = 'time-soon';
                    } else {
                        timeText = `${Math.floor(item.EstimateTime / 60)} 分鐘`;
                        timeClass = item.EstimateTime <= 180 ? 'time-soon' : 'time-normal';
                    }
                    html += `
                        <div class="arrival-item d-flex justify-content-between align-items-center py-2 border-bottom">
                            <span class="route-num text-light">${item.RouteName} 路</span>
                            <span class="arrival-time ${timeClass}">${timeText}</span>
                        </div>
                    `;
                });
            } else {
                html += `<p class="text-muted small py-2">目前沒有班次動態資訊</p>`;
            }
            html += `</div></div>`;
        }

        // 處理捷運資訊
        if (data.transport_type === 'MRT' || (data.mrt && data.mrt.length > 0)) {
            html += `
                <div class="mb-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="text-info fw-bold mb-0">🚇 捷運班次時刻</h6>
                        <span class="badge bg-secondary-subtle text-secondary small">中捷即時</span>
                    </div>
                    <div class="arrival-list">
            `;
            if (data.mrt && data.mrt.length > 0) {
                data.mrt.forEach(item => {
                    let timeText = '';
                    let timeClass = '';
                    if (item.EstimateTime <= 60) {
                        timeText = '即將發車';
                        timeClass = 'time-soon';
                    } else {
                        timeText = `${Math.floor(item.EstimateTime / 60)} 分鐘`;
                        timeClass = item.EstimateTime <= 180 ? 'time-soon' : 'time-normal';
                    }
                    html += `
                        <div class="arrival-item d-flex justify-content-between align-items-center py-2 border-bottom">
                            <span class="route-num text-light">往 ${item.Destination}</span>
                            <span class="arrival-time ${timeClass}">${timeText}</span>
                        </div>
                    `;
                });
            } else {
                html += `<p class="text-muted small py-2">目前沒有班次發車時刻</p>`;
            }
            html += `</div></div>`;
        }

        arrivalData.innerHTML = html;
    }

    // 8. 渲染收藏按鈕並綁定點擊事件
    function renderFavoriteButton(stationId, isFavorited) {
        const container = document.getElementById('favorite-btn-container');
        if (isFavorited) {
            container.innerHTML = `
                <button id="btn-fav" class="btn btn-warning w-100 d-flex align-items-center justify-content-center gap-2">
                    <span>⭐ 已加入收藏</span>
                </button>
            `;
            document.getElementById('btn-fav').onclick = () => removeFavorite(stationId);
        } else {
            container.innerHTML = `
                <button id="btn-fav" class="btn btn-outline-info w-100 d-flex align-items-center justify-content-center gap-2">
                    <span>☆ 加入收藏</span>
                </button>
            `;
            document.getElementById('btn-fav').onclick = () => addFavorite(stationId);
        }
    }

    // 9. 加入收藏 AJAX
    function addFavorite(stationId) {
        const btn = document.getElementById('btn-fav');
        btn.disabled = true;
        
        fetch('/favorites/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ station_id: stationId })
        })
        .then(response => response.json())
        .then(res => {
            if (res.status === 'success') {
                renderFavoriteButton(stationId, true);
            } else {
                alert("收藏失敗：" + res.message);
                btn.disabled = false;
            }
        })
        .catch(err => {
            console.error(err);
            btn.disabled = false;
        });
    }

    // 10. 移除收藏 AJAX
    function removeFavorite(stationId) {
        const btn = document.getElementById('btn-fav');
        btn.disabled = true;

        fetch(`/favorites/delete/${stationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(res => {
            if (res.status === 'success') {
                renderFavoriteButton(stationId, false);
            } else {
                alert("移除失敗：" + res.message);
                btn.disabled = false;
            }
        })
        .catch(err => {
            console.error(err);
            btn.disabled = false;
        });
    }

    // 11. 設定自動更新計時器與倒數秒數 UI
    function setupAutoRefresh(stationId) {
        // 設定每秒更新一次倒數 UI
        countdownInterval = setInterval(() => {
            refreshCountdown--;
            if (refreshCountdown <= 0) {
                refreshCountdown = 10;
            }
            const refreshText = document.getElementById('refresh-text');
            if (refreshText) {
                refreshText.innerText = `即時更新中 (${refreshCountdown}s)`;
            }
        }, 1000);

        // 設定每 10 秒向後端請求一次最新動態數據
        refreshInterval = setInterval(() => {
            if (activeStationId === stationId) {
                fetchStationRealtimeData(stationId);
            }
        }, 10000);
    }
});
