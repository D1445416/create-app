/**
 * 台中大眾運輸站點狀態與擁擠度顯示系統 - 前端主邏輯 (main.js)
 * 提供 GPS 地理定位、即時快取手動重整、搜尋與篩選的高畫質動畫互動。
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('台中大眾運輸站點擁擠度系統前端載入成功！');
    initGPSRecommend();
});

/**
 * 初始化 GPS 周邊推薦站點功能
 */
function initGPSRecommend() {
    const gpsBtn = document.getElementById('btn-gps-recommend');
    const container = document.getElementById('gps-recommend-list');
    
    if (!gpsBtn || !container) return;

    gpsBtn.addEventListener('click', () => {
        // 開啟載入動畫狀態
        gpsBtn.disabled = true;
        gpsBtn.innerHTML = '<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> 定位獲取中...';
        container.innerHTML = '<div class="text-center p-4 text-muted"><p>瀏覽器正在請求您的 GPS 定位權限...</p></div>';

        if (!navigator.geolocation) {
            showGPSError('您的瀏覽器不支援地理位置定位功能。');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                fetchNearbyStations(lat, lng);
            },
            (error) => {
                let msg = '定位失敗，無法取得您的位置。';
                if (error.code === error.PERMISSION_DENIED) {
                    msg = '定位請求遭拒，請允許瀏覽器定位權限以取得周邊推薦站點。';
                }
                showGPSError(msg);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    });

    function showGPSError(message) {
        gpsBtn.disabled = false;
        gpsBtn.innerHTML = '📍 GPS 定位推薦周邊站點';
        container.innerHTML = `
            <div class="alert alert-warning m-0 p-3 d-flex align-items-center" role="alert">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-exclamation-triangle-fill flex-shrink-0 me-2" viewBox="0 0 16 16">
                    <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
                </svg>
                <div>${message}</div>
            </div>
        `;
    }

    /**
     * 向後端 API 發送經緯度，獲取周邊推薦站點列表
     */
    async function fetchNearbyStations(lat, lng) {
        try {
            const response = await fetch(`/api/stations/nearby?lat=${lat}&lng=${lng}&limit=5`);
            if (!response.ok) {
                throw new Error('伺服器回傳異常');
            }
            const data = await response.json();
            renderNearbyStations(data);
        } catch (error) {
            showGPSError('無法從伺服器取得周邊推薦站點，請稍後再試。');
        } finally {
            gpsBtn.disabled = false;
            gpsBtn.innerHTML = '📍 重新定位周邊站點';
        }
    }

    /**
     * 渲染從 API 取得的周邊站點 HTML
     */
    function renderNearbyStations(stations) {
        if (!stations || stations.length === 0) {
            container.innerHTML = '<div class="text-center p-4 text-muted"><p>您附近 10 公里內無本系統服務之大眾運輸站點。</p></div>';
            return;
        }

        let html = '<div class="list-group list-group-flush gap-2">';
        stations.forEach(station => {
            // 計算大眾運輸徽章樣式
            const typeBadge = station.type === 'metro' 
                ? '<span class="badge badge-metro">捷運</span>' 
                : '<span class="badge badge-bus">公車</span>';

            // 擁擠度狀態等級對應 Class 與名稱
            let levelClass = 'crowd-green';
            let levelName = '通暢';
            if (station.level === 'orange') {
                levelClass = 'crowd-orange';
                levelName = '普通';
            } else if (station.level === 'red') {
                levelClass = 'crowd-red';
                levelName = '擁擠';
            }

            html += `
                <a href="/station/${station.station_id}" class="list-group-item list-group-item-action glass-panel border-0 p-3 d-flex align-items-center justify-content-between text-decoration-none">
                    <div class="d-flex align-items-center gap-3">
                        <div class="station-icon text-center fs-4">🚉</div>
                        <div>
                            <div class="d-flex align-items-center gap-2">
                                <h5 class="mb-0 text-white">${station.name}</h5>
                                ${typeBadge}
                            </div>
                            <small class="text-muted">${station.route_name}</small>
                        </div>
                    </div>
                    <div class="d-flex align-items-center gap-3">
                        <span class="crowd-indicator ${levelClass}">${levelName}</span>
                        <div class="text-end text-muted d-none d-sm-block">
                            <small class="d-block">${station.passenger_count} 人</small>
                        </div>
                    </div>
                </a>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    }
}
