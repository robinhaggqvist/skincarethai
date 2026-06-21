document.addEventListener("DOMContentLoaded", function() {
    // Configuration
    const SHOW_DELAY = 15000; // 15 seconds
    const SCROLL_TRIGGER = 0.4; // 40% scroll height
    const POPUP_ID = 'skincare-conversion-popup';

    let popupShown = false;

    // Helper to create popup
    function createPopup(link, title) {
        if (document.getElementById(POPUP_ID)) return;

        const popup = document.createElement('div');
        popup.id = POPUP_ID;
        popup.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 300px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            padding: 20px;
            z-index: 9999;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            border: 1px solid #f0f0f0;
        `;

        popup.innerHTML = `
            <button id="${POPUP_ID}-close" style="position: absolute; top: 10px; right: 10px; border: none; background: none; font-size: 20px; color: #999; cursor: pointer;">&times;</button>
            <h4 style="margin: 0 0 10px; font-size: 16px; color: #333; font-weight: 600;">สนใจสินค้านี้อยู่ใช่ไหม?</h4>
            <p style="font-size: 13px; color: #666; margin-bottom: 15px; line-height: 1.4;">เช็คโปรโมชั่นล่าสุดและราคาพิเศษสำหรับ ${title} ได้เลย</p>
            <a href="${link}" target="_blank" rel="sponsored" style="display: block; width: 100%; padding: 12px 0; background: #0071e3; color: white; text-align: center; text-decoration: none; border-radius: 8px; font-weight: 500; font-size: 14px; transition: background 0.2s;">เช็คราคาที่ Lazada/Shopee</a>
        `;

        document.body.appendChild(popup);

        // Close handler
        document.getElementById(`${POPUP_ID}-close`).addEventListener('click', () => {
            popup.style.transform = 'translateY(20px)';
            popup.style.opacity = '0';
            setTimeout(() => popup.remove(), 400);
        });

        // Show animation
        requestAnimationFrame(() => {
            popup.style.transform = 'translateY(0)';
            popup.style.opacity = '1';
        });
    }

    function triggerPopup() {
        if (popupShown) return;
        
        // Find affiliate link
        const btn = document.querySelector('.aff-link-btn');
        if (!btn) return;
        
        const link = btn.href;
        
        // Find title (h1 or product name)
        const titleEl = document.querySelector('.product-name') || document.querySelector('h1');
        let title = 'สินค้า';
        if (titleEl) {
            // Truncate title if too long
            title = titleEl.innerText.split(':')[0].substring(0, 30);
            if (titleEl.innerText.length > 30) title += '...';
        }

        createPopup(link, title);
        popupShown = true;
    }

    // Timed trigger
    setTimeout(triggerPopup, SHOW_DELAY);

    // Scroll trigger
    window.addEventListener('scroll', () => {
        if (popupShown) return;
        const scrollPercent = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);
        if (scrollPercent > SCROLL_TRIGGER) {
            triggerPopup();
        }
    });
});
