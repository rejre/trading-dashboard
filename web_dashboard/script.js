document.addEventListener('DOMContentLoaded', () => {
    fetchStatus();
    setInterval(fetchStatus, 60000); // 每60秒刷新一次
});

async function fetchStatus() {
    // 在部署后，这里需要替换为你的GitHub Raw文件的URL
    const url = 'https://raw.githubusercontent.com/rejre/trading-dashboard/main/status.json'; 

    try {
        const response = await fetch(url + `?t=${new Date().getTime()}`); // 添加时间戳防止缓存
        const data = await response.json();

        document.getElementById('update-time').textContent = data.update_time;
        document.getElementById('market-status').textContent = data.market_status;

        const portfolioList = document.getElementById('portfolio-list');
        portfolioList.innerHTML = '';
        if (Object.keys(data.live_portfolio).length > 0) {
            for (const [code, details] of Object.entries(data.live_portfolio)) {
                const li = document.createElement('li');
                li.textContent = `代码: ${code}, 买入价: ${details.buy_price.toFixed(2)}, 买入日期: ${new Date(details.buy_date).toLocaleString()}`;
                portfolioList.appendChild(li);
            }
        } else {
            portfolioList.innerHTML = '<li>暂无持仓</li>';
        }

        const signalsList = document.getElementById('signals-list');
        signalsList.innerHTML = '';
        if (data.last_signals.length > 0) {
            data.last_signals.forEach(signal => {
                const li = document.createElement('li');
                li.textContent = signal.replace(/<[^>]*>/g, ' '); // 移除HTML标签，只显示文本
                signalsList.appendChild(li);
            });
        } else {
            signalsList.innerHTML = '<li>暂无信号</li>';
        }

    } catch (error) {
        console.error('Error fetching status:', error);
    }
}
