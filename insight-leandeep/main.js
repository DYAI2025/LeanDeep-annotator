// main.js — Tab Switching & Chart Rendering

const chartCtx = document.getElementById('insightChart').getContext('2d');
let myChart;

function renderChart(config) {
    if (myChart) {
        myChart.destroy();
    }
    myChart = new Chart(chartCtx, config);
}

window.switchTab = function(tabId, element) {
    // Update Tab Styling
    document.querySelectorAll('#tabs button').forEach(btn => {
        btn.classList.remove('tab-active');
    });
    element.classList.add('tab-active');

    const data = useCaseData[tabId];
    const lang = currentLanguage;
    
    // Animation trigger
    const panel = document.getElementById('contentPanel');
    panel.classList.remove('fade-in');
    void panel.offsetWidth; // Trigger reflow
    panel.classList.add('fade-in');

    // Update Content
    const titleKey = `title_${lang}`;
    const subtitleKey = `subtitle_${lang}`;
    const scenarioKey = `scenario_${lang}`;
    const insightKey = `insight_${lang}`;
    const benefitKey = `benefit_${lang}`;
    const chartTitleKey = `chartTitle_${lang}`;

    document.getElementById('panelTitle').innerHTML = data[titleKey];
    document.getElementById('panelSubtitle').innerHTML = data[subtitleKey];
    document.getElementById('panelScenario').innerHTML = data[scenarioKey];
    document.getElementById('panelInsight').innerHTML = data[insightKey];
    document.getElementById('panelBenefit').innerHTML = data[benefitKey];
    document.getElementById('chartDescription').innerHTML = data[chartTitleKey];

    // Update Chart
    renderChart(data.config);
};

// Initialize with Therapy tab on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    renderChart(useCaseData['therapy'].config);
});

// Re-apply chart when language changes (optional enhancement)
// This ensures chart labels update if needed
const originalToggle = window.toggleLanguage;
window.toggleLanguage = function() {
    originalToggle.call(this);
    // Refresh current tab's chart
    const activeTab = document.querySelector('.tab-active');
    if (activeTab) {
        const tabId = activeTab.getAttribute('onclick').match(/'(\w+)'/)[1];
        renderChart(useCaseData[tabId].config);
    }
};
