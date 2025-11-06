document.addEventListener('DOMContentLoaded', () => {
    renderReport();
});

function renderReport() {
    if (window.reportData) {
        const data = window.reportData;

        document.getElementById('report-title').textContent = data.title;
        document.getElementById('update-time').textContent = data.update_time;

        const scoreNum = data.market_score || 0;
        document.getElementById('market-status').textContent = data.market_status;
        const scoreBar = document.getElementById('score-bar');
        const percentage = (scoreNum / 4) * 100;
        scoreBar.style.width = `${percentage}%`;
        const scoreValueSpan = document.getElementById('score-value');
        scoreValueSpan.textContent = `(市场分数: ${scoreNum})`;
        if (scoreNum === 0) scoreBar.style.backgroundColor = '#6c757d';
        else if (scoreNum === 1) scoreBar.style.backgroundColor = '#007bff';
        else if (scoreNum === 2) scoreBar.style.backgroundColor = '#ffc107';
        else if (scoreNum === 3) scoreBar.style.backgroundColor = '#fd7e14';
        else if (scoreNum >= 4) scoreBar.style.backgroundColor = '#dc3545';

        const reportContent = document.getElementById('report-content');
        reportContent.innerHTML = '';
        if (data.sections && data.sections.length > 0) {
            data.sections.forEach(section => {
                const card = document.createElement('div');
                card.className = 'card';
                const title = document.createElement('h2');
                title.textContent = section.question;
                card.appendChild(title);
                const answer = document.createElement('p');
                answer.innerHTML = section.answer.replace(/\n/g, '<br>');
                card.appendChild(answer);
                reportContent.appendChild(card);
            });
        } else {
            reportContent.innerHTML = '<p>暂无报告内容。</p>';
        }
    } else {
        document.getElementById('report-content').innerHTML = '<p>报告数据未嵌入，请检查脚本。</p>';
    }
}