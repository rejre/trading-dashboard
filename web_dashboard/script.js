document.addEventListener('DOMContentLoaded', () => {
    fetchReport();
    setInterval(fetchReport, 300000); // 每5分钟刷新一次报告
});

async function fetchReport() {
    const url = 'https://raw.githubusercontent.com/rejre/trading-dashboard/main/status.json';

    try {
        const response = await fetch(url + `?t=${new Date().getTime()}`);
        const data = await response.json();

        document.getElementById('report-title').textContent = data.title;
        const score = data.sections.find(s => s.question.includes("天时判断"))?.answer.match(/市场分数: (\d+)/)?.[1] || 0;
        const scoreNum = parseInt(score, 10);

        document.getElementById('market-status').textContent = `${data.market_status} (市场分数: ${scoreNum})`;

        const scoreBar = document.getElementById('score-bar');
        const percentage = (scoreNum / 4) * 100; // 最高4分
        scoreBar.style.width = `${percentage}%`;

        // 根据分数设置颜色
        if (scoreNum === 0) scoreBar.style.backgroundColor = '#6c757d'; // 灰色
        else if (scoreNum === 1) scoreBar.style.backgroundColor = '#007bff'; // 蓝色
        else if (scoreNum === 2) scoreBar.style.backgroundColor = '#ffc107'; // 黄色
        else if (scoreNum === 3) scoreBar.style.backgroundColor = '#fd7e14'; // 橙色
        else if (scoreNum >= 4) scoreBar.style.backgroundColor = '#dc3545'; // 红色

        const reportContent = document.getElementById('report-content');
        reportContent.innerHTML = ''; // 清空旧内容

        if (data.sections && data.sections.length > 0) {
            data.sections.forEach(section => {
                const card = document.createElement('div');
                card.className = 'card';

                const title = document.createElement('h2');
                title.textContent = section.question;
                card.appendChild(title);

                const answer = document.createElement('p');
                // 将换行符转换成<br>标签以在HTML中显示
                answer.innerHTML = section.answer.replace(/\n/g, '<br>');
                card.appendChild(answer);

                reportContent.appendChild(card);
            });
        } else {
            reportContent.innerHTML = '<p>暂无报告内容。</p>';
        }

    } catch (error) {
        console.error('Error fetching report:', error);
        document.getElementById('report-content').innerHTML = '<p>加载报告失败，请检查网络或稍后再试。</p>';
    }
}