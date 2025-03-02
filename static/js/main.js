// 自动关闭警告框
document.addEventListener('DOMContentLoaded', function() {
    // 获取所有的警告框
    const alerts = document.querySelectorAll('.alert');
    
    // 为每个警告框设置3秒后自动关闭
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.click();
            }
        }, 3000);
    });
    
    // 日期输入格式化（如果有日期输入框）
    const dateInput = document.getElementById('date');
    if (dateInput) {
        dateInput.addEventListener('blur', function() {
            const val = this.value.trim();
            // 简单的日期格式验证和格式化
            if (val && !/^\d{4}\/\d{2}\/\d{2}$/.test(val)) {
                // 尝试将其他格式转换为YYYY/MM/DD
                try {
                    const date = new Date(val);
                    if (!isNaN(date.getTime())) {
                        const year = date.getFullYear();
                        const month = String(date.getMonth() + 1).padStart(2, '0');
                        const day = String(date.getDate()).padStart(2, '0');
                        this.value = `${year}/${month}/${day}`;
                    }
                } catch (e) {
                    console.error('日期格式化失败', e);
                }
            }
        });
    }
    
    // 初始化过期论文折叠功能
    initExpiredRowsToggle();
});

/**
 * 初始化过期论文折叠功能
 */
function initExpiredRowsToggle() {
    const toggleBtn = document.getElementById('toggle-expired');
    
    if (toggleBtn) {
        const expiredRows = document.querySelectorAll('tr[data-expired="true"]');
        const expiredCount = document.getElementById('expired-count');
        const toggleText = document.getElementById('toggle-expired-text');
        
        // 设置过期行数
        if (expiredCount) {
            expiredCount.textContent = expiredRows.length;
        }
        
        // 默认隐藏过期行
        let showExpired = false;
        updateExpiredRowsVisibility();
        
        // 添加点击事件
        toggleBtn.addEventListener('click', function() {
            showExpired = !showExpired;
            updateExpiredRowsVisibility();
        });
        
        /**
         * 更新过期行的显示状态
         */
        function updateExpiredRowsVisibility() {
            expiredRows.forEach(row => {
                row.style.display = showExpired ? 'table-row' : 'none';
            });
            
            if (toggleText) {
                toggleText.textContent = showExpired ? '隐藏已过期安排' : '显示已过期安排';
            }
        }
    }
} 
