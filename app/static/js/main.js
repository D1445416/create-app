document.addEventListener('DOMContentLoaded', () => {
    // --- Auto-dismiss Flask Toasts ---
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toastEl => {
        // Auto hide toast after 5 seconds
        setTimeout(() => {
            const bsToast = bootstrap.Toast.getInstance(toastEl);
            if (bsToast) {
                bsToast.hide();
            } else {
                toastEl.classList.remove('show');
            }
        }, 5000);
    });

    // --- Geolocation Helper Functions ---
    window.getCurrentLocation = (latInputId, lngInputId, statusTextId) => {
        const latInput = document.getElementById(latInputId);
        const lngInput = document.getElementById(lngInputId);
        const statusText = document.getElementById(statusTextId);

        if (!navigator.geolocation) {
            if (statusText) statusText.innerText = '此瀏覽器不支援定位功能。';
            return;
        }

        if (statusText) {
            statusText.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>正在獲取 GPS 定位中...';
            statusText.className = 'text-accent small mt-1';
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                if (latInput) latInput.value = lat.toFixed(6);
                if (lngInput) lngInput.value = lng.toFixed(6);

                if (statusText) {
                    statusText.innerHTML = '<i class="fa-solid fa-circle-check text-success me-2"></i>已成功獲取定位資訊！';
                    statusText.className = 'text-success small mt-1';
                }
            },
            (error) => {
                console.error('Geolocation error:', error);
                if (statusText) {
                    let errMsg = '無法獲取定位。';
                    if (error.code === error.PERMISSION_DENIED) {
                        errMsg = '使用者拒絕了定位權限請求。';
                    } else if (error.code === error.POSITION_UNAVAILABLE) {
                        errMsg = '定位位置資訊不可用。';
                    } else if (error.code === error.TIMEOUT) {
                        errMsg = '定位獲取逾時。';
                    }
                    statusText.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-danger me-2"></i>${errMsg}`;
                    statusText.className = 'text-danger small mt-1';
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 8000,
                maximumAge: 0
            }
        );
    };
});
