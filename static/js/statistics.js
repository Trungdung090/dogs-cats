function timeAgo(date) {
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    const intervals = [
        { label: 'năm', seconds: 31536000 },
        { label: 'tháng', seconds: 2592000 },
        { label: 'ngày', seconds: 86400 },
        { label: 'giờ', seconds: 3600 },
        { label: 'phút', seconds: 60 }
    ];
    for (const interval of intervals) {
        const delta = Math.floor(seconds / interval.seconds);
        if (delta >= 1) return `${delta} ${interval.label} trước`;
    }
    return 'Vừa xong';
}

fetch('/api/statistics')
    .then(res => res.json())
    .then(data => {
        document.getElementById('totalImages').textContent = data.total.toLocaleString();
        document.getElementById('avgAccuracy').textContent = data.avg_accuracy.toFixed(1) + '%';
        document.getElementById('popularBreed').textContent = data.popular_breed;

    const breedChartCtx = document.getElementById('breedChart').getContext('2d');
    new Chart(breedChartCtx, {
        type: 'doughnut',
        data: {
            labels: data.breed_distribution.map(b => b.label),
            datasets: [{
                data: data.breed_distribution.map(b => b.count),
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                    '#9966FF', '#FF9F40', '#C9CBCF', '#20c997',
                    '#fd7e14', '#6f42c1'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } },
            cutout: '60%'
        }
    });

    const timeChartCtx = document.getElementById('timeChart').getContext('2d');
    new Chart(timeChartCtx, {
        type: 'line',
        data: {
            labels: data.time_activity.map(t => t.day),
            datasets: [{
                label: 'Số lượng phân loại',
                data: data.time_activity.map(t => t.count),
                borderColor: '#5a67d8',
                backgroundColor: 'rgba(90, 103, 216, 0.2)',
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 6,
                pointBackgroundColor: '#5a67d8',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });

    const recentContainer = document.getElementById('recentClassifications');
    recentContainer.innerHTML = '';
    data.recent.forEach(item => {
        const el = document.createElement('div');
        el.className = 'classification-item';
        el.innerHTML = `
              <img src="${item.image_path}" class="classification-image" alt="Pet">
              <div class="classification-info">
                  <h4>${item.breed}</h4>
                  <p>${timeAgo(new Date(item.timestamp))}</p>
              </div>
              <span class="confidence-badge">${item.confidence}%</span>
        `;
        recentContainer.appendChild(el);
    });
    });
