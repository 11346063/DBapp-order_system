(function () {
    var dailyData = window.REPORT_DATA.daily;
    var monthlyData = window.REPORT_DATA.monthly;

    var isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    var textColor = isDark ? '#aaa' : '#666';
    var gridColor = isDark ? '#222' : '#eee';
    var yellow = '#F3E800';
    var red = '#ff6b6b';

    Chart.defaults.color = textColor;
    Chart.defaults.font.family = "'Noto Sans TC', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

    function buildOptions(orderAxisLabel, revenueAxisLabel) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    labels: {
                        color: textColor,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: isDark ? '#1a1a1a' : '#fff',
                    borderColor: isDark ? '#333' : '#ddd',
                    borderWidth: 1,
                    titleColor: isDark ? '#fff' : '#333',
                    bodyColor: isDark ? '#fff' : '#333'
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: textColor,
                        maxRotation: 45,
                        minRotation: 0
                    },
                    grid: {
                        color: gridColor
                    }
                },
                orders: {
                    type: 'linear',
                    position: 'left',
                    title: {
                        display: true,
                        text: orderAxisLabel,
                        color: textColor
                    },
                    beginAtZero: true,
                    ticks: {
                        color: textColor,
                        precision: 0
                    },
                    grid: {
                        color: gridColor
                    }
                },
                revenue: {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: revenueAxisLabel,
                        color: textColor
                    },
                    beginAtZero: true,
                    ticks: {
                        color: textColor,
                        callback: function (value) {
                            return '$' + value;
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        };
    }

    function buildMixedChart(canvasId, labels, counts, revenues, barPercentage) {
        var canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        return new Chart(canvas, {
            data: {
                labels: labels,
                datasets: [
                    {
                        type: 'bar',
                        label: '訂單數',
                        data: counts,
                        yAxisID: 'orders',
                        backgroundColor: yellow,
                        borderColor: yellow,
                        borderWidth: 1,
                        borderRadius: 4,
                        barPercentage: barPercentage
                    },
                    {
                        type: 'line',
                        label: '營收',
                        data: revenues,
                        yAxisID: 'revenue',
                        borderColor: red,
                        backgroundColor: 'rgba(255, 107, 107, 0.12)',
                        borderWidth: 3,
                        pointBackgroundColor: red,
                        pointBorderColor: red,
                        pointRadius: 3,
                        tension: 0.35,
                        fill: false
                    }
                ]
            },
            options: buildOptions('訂單數', '營收 ($)')
        });
    }

    buildMixedChart(
        'dailyChart',
        dailyData.dates,
        dailyData.counts,
        dailyData.revenues,
        0.7
    );

    buildMixedChart(
        'monthlyChart',
        monthlyData.months,
        monthlyData.counts,
        monthlyData.revenues,
        0.45
    );
})();
