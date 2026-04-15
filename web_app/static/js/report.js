(function() {
    var dailyData = window.REPORT_DATA.daily;
    var monthlyData = window.REPORT_DATA.monthly;

    var isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    var textColor = isDark ? '#aaa' : '#666';
    var axisLineColor = isDark ? '#333' : '#ddd';
    var yellow = '#F3E800';

    // Daily Chart
    var dailyChart = echarts.init(document.getElementById('dailyChart'));
    dailyChart.setOption({
        tooltip: {
            trigger: 'axis',
            backgroundColor: isDark ? '#1a1a1a' : '#fff',
            borderColor: isDark ? '#333' : '#ddd',
            textStyle: { color: isDark ? '#fff' : '#333' }
        },
        legend: {
            data: ['訂單數', '營收'],
            textStyle: { color: textColor }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'category',
            data: dailyData.dates,
            axisLabel: { color: textColor, rotate: 45 },
            axisLine: { lineStyle: { color: axisLineColor } }
        },
        yAxis: [
            {
                type: 'value',
                name: '訂單數',
                nameTextStyle: { color: textColor },
                axisLabel: { color: textColor },
                axisLine: { lineStyle: { color: axisLineColor } },
                splitLine: { lineStyle: { color: isDark ? '#222' : '#eee' } }
            },
            {
                type: 'value',
                name: '營收 ($)',
                nameTextStyle: { color: textColor },
                axisLabel: { color: textColor },
                axisLine: { lineStyle: { color: axisLineColor } },
                splitLine: { show: false }
            }
        ],
        series: [
            {
                name: '訂單數',
                type: 'bar',
                yAxisIndex: 0,
                data: dailyData.counts,
                itemStyle: { color: yellow }
            },
            {
                name: '營收',
                type: 'line',
                yAxisIndex: 1,
                data: dailyData.revenues,
                smooth: true,
                itemStyle: { color: '#ff6b6b' },
                lineStyle: { width: 2 }
            }
        ]
    });

    // Monthly Chart
    var monthlyChart = echarts.init(document.getElementById('monthlyChart'));
    monthlyChart.setOption({
        tooltip: {
            trigger: 'axis',
            backgroundColor: isDark ? '#1a1a1a' : '#fff',
            borderColor: isDark ? '#333' : '#ddd',
            textStyle: { color: isDark ? '#fff' : '#333' }
        },
        legend: {
            data: ['訂單數', '營收'],
            textStyle: { color: textColor }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'category',
            data: monthlyData.months,
            axisLabel: { color: textColor },
            axisLine: { lineStyle: { color: axisLineColor } }
        },
        yAxis: [
            {
                type: 'value',
                name: '訂單數',
                nameTextStyle: { color: textColor },
                axisLabel: { color: textColor },
                axisLine: { lineStyle: { color: axisLineColor } },
                splitLine: { lineStyle: { color: isDark ? '#222' : '#eee' } }
            },
            {
                type: 'value',
                name: '營收 ($)',
                nameTextStyle: { color: textColor },
                axisLabel: { color: textColor },
                axisLine: { lineStyle: { color: axisLineColor } },
                splitLine: { show: false }
            }
        ],
        series: [
            {
                name: '訂單數',
                type: 'bar',
                yAxisIndex: 0,
                data: monthlyData.counts,
                itemStyle: { color: yellow },
                barWidth: '40%'
            },
            {
                name: '營收',
                type: 'line',
                yAxisIndex: 1,
                data: monthlyData.revenues,
                smooth: true,
                itemStyle: { color: '#ff6b6b' },
                lineStyle: { width: 3 },
                areaStyle: { color: 'rgba(255,107,107,0.1)' }
            }
        ]
    });

    // Responsive resize
    window.addEventListener('resize', function() {
        dailyChart.resize();
        monthlyChart.resize();
    });
})();