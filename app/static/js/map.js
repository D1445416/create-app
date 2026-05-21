document.addEventListener('DOMContentLoaded', function() {
    // 初始化地圖，中心點設在台中火車站
    const map = L.map('map').setView([24.1373, 120.6856], 15);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // 模擬站點數據
    const mockStations = [
        { id: 'BUS_01', name: '台中車站(民族路口)', lat: 24.1373, lon: 120.6856, type: 'bus' },
        { id: 'MRT_01', name: '市政府站', lat: 24.1628, lon: 120.6439, type: 'mrt' },
        { id: 'BUS_02', name: '新光/遠東', lat: 24.1645, lon: 120.6433, type: 'bus' }
    ];

    const markers = {};

    mockStations.forEach(station => {
        const marker = L.marker([station.lat, station.lon]).addTo(map);
        marker.on('click', () => {
            loadStationInfo(station);
        });
        markers[station.id] = marker;
    });

    function loadStationInfo(station) {
        const sidebarContent = document.getElementById('sidebar-content');
        sidebarContent.innerHTML = `
            <div class="station-card">
                <span class="transport-tag tag-${station.type}">${station.type === 'bus' ? '公車' : '捷運'}</span>
                <h2 class="station-title">${station.name}</h2>
                <div id="arrival-data">
                    <div class="text-center py-3">
                        <div class="spinner-border text-primary" role="status"></div>
                        <p class="mt-2">讀取即時數據中...</p>
                    </div>
                </div>
                <button class="btn btn-outline-light btn-sm w-100 mt-3">加入收藏</button>
            </div>
        `;

        // 呼叫 Flask API
        fetch(`/api/station/${station.id}`)
            .then(response => response.json())
            .then(res => {
                if (res.status === 'success') {
                    updateSidebarArrivals(res.data);
                }
            })
            .catch(err => {
                document.getElementById('arrival-data').innerHTML = `<p class="text-danger">無法取得即時數據</p>`;
            });
    }

    function updateSidebarArrivals(data) {
        const arrivalData = document.getElementById('arrival-data');
        
        let busHtml = `
            <div class="mb-4">
                <h6 class="text-secondary mb-2">🚌 公車即時到站</h6>
                <div class="arrival-list">
                    ${data.bus.map(item => `
                        <div class="arrival-item">
                            <span class="route-num">${item.RouteName}</span>
                            <span class="arrival-time ${item.EstimateTime <= 60 ? 'time-soon' : 'time-normal'}">
                                ${item.EstimateTime <= 60 ? '進站中' : Math.floor(item.EstimateTime / 60) + ' 分鐘'}
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        let mrtHtml = `
            <div>
                <h6 class="text-secondary mb-2">🚇 捷運發車時刻</h6>
                <div class="arrival-list">
                    ${data.mrt.map(item => `
                        <div class="arrival-item">
                            <span class="route-num">往 ${item.Destination}</span>
                            <span class="arrival-time ${item.EstimateTime <= 180 ? 'time-soon' : 'time-normal'}">
                                ${Math.floor(item.EstimateTime / 60)} 分鐘
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        arrivalData.innerHTML = busHtml + mrtHtml;
    }
});
