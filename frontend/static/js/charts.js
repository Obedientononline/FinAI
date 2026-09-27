/* Safe Wealth Advisory — Chart Utilities */

// Standard Plotly layout defaults
const CHART_COLORS = {
    equities: '#1E88E5',
    fixed_income: '#43A047',
    commodities: '#FB8C00',
    cash: '#7E57C2',
    primary: '#1E88E5',
    secondary: '#9E9E9E',
    success: '#43A047',
    danger: '#E53935'
};

const DEFAULT_LAYOUT = {
    margin: { l: 40, r: 20, t: 40, b: 40 },
    font: { family: 'Inter, sans-serif' },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    legend: {
        orientation: 'h',
        yanchor: 'bottom',
        y: -0.2,
        xanchor: 'center',
        x: 0.5
    }
};

const PLOTLY_CONFIG = {
    responsive: true,
    displayModeBar: false
};

/**
 * Render a donut chart for asset allocation.
 * @param {string} elementId - DOM element ID
 * @param {Object} allocation - e.g. {equities: 0.55, fixed_income: 0.25, ...}
 */
function renderAllocationDonut(elementId, allocation) {
    const labels = Object.keys(allocation).map(k => k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()));
    const values = Object.values(allocation);
    const colors = Object.keys(allocation).map(k => CHART_COLORS[k] || '#999');

    const data = [{
        values: values,
        labels: labels,
        type: 'pie',
        hole: 0.45,
        marker: { colors: colors },
        textinfo: 'label+percent',
        textposition: 'outside'
    }];

    const layout = Object.assign({}, DEFAULT_LAYOUT, {
        height: 320,
        showlegend: true
    });

    Plotly.newPlot(elementId, data, layout, PLOTLY_CONFIG);
}

/**
 * Render grouped bar chart comparing current vs target allocation.
 * @param {string} elementId
 * @param {Object} current - e.g. {equities: 0.55, ...}
 * @param {Object} target - e.g. {equities: 0.50, ...}
 */
function renderAllocationBar(elementId, current, target) {
    const classes = ['equities', 'fixed_income', 'commodities', 'cash'];
    const labels = classes.map(c => c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));

    const data = [
        {
            x: labels,
            y: classes.map(c => current[c] || 0),
            name: 'Current',
            type: 'bar',
            marker: { color: '#90CAF9' }
        },
        {
            x: labels,
            y: classes.map(c => target[c] || 0),
            name: 'Target',
            type: 'bar',
            marker: { color: '#1E88E5' }
        }
    ];

    const layout = Object.assign({}, DEFAULT_LAYOUT, {
        barmode: 'group',
        height: 320,
        yaxis: { tickformat: '.0%', title: 'Weight' }
    });

    Plotly.newPlot(elementId, data, layout, PLOTLY_CONFIG);
}

/**
 * Render backtest portfolio value curves.
 * @param {string} elementId
 * @param {Array} timeseries - array of {date, governed_portfolio_value, drifting_benchmark_value}
 */
function renderBacktestCurves(elementId, timeseries) {
    const dates = timeseries.map(r => r.date);

    const data = [
        {
            x: dates,
            y: timeseries.map(r => r.governed_portfolio_value),
            name: 'Governed Rebalanced',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#1E88E5', width: 3 },
            marker: { size: 4 }
        },
        {
            x: dates,
            y: timeseries.map(r => r.drifting_benchmark_value),
            name: 'Unmanaged Drifting',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#9E9E9E', width: 2, dash: 'dash' }
        }
    ];

    const layout = Object.assign({}, DEFAULT_LAYOUT, {
        height: 380,
        title: 'Portfolio Wealth Trajectory (2020–2024)',
        yaxis: { title: 'Portfolio Value ($)', tickprefix: '$' },
        xaxis: { title: 'Timeline' }
    });

    Plotly.newPlot(elementId, data, layout, PLOTLY_CONFIG);
}

/**
 * Render tracking error comparison.
 * @param {string} elementId
 * @param {Array} timeseries
 */
function renderTrackingError(elementId, timeseries) {
    const dates = timeseries.map(r => r.date);

    const data = [
        {
            x: dates,
            y: timeseries.map(r => r.governed_tracking_error),
            name: 'Governed',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#43A047', width: 2.5 }
        },
        {
            x: dates,
            y: timeseries.map(r => r.drifting_tracking_error),
            name: 'Drifting',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#E53935', width: 2, dash: 'dot' }
        }
    ];

    const layout = Object.assign({}, DEFAULT_LAYOUT, {
        height: 300,
        title: 'Tracking Error to Target (%)',
        yaxis: { title: 'Tracking Error', ticksuffix: '%' }
    });

    Plotly.newPlot(elementId, data, layout, PLOTLY_CONFIG);
}

/**
 * Render equity weight drift with fiduciary ceiling.
 * @param {string} elementId
 * @param {Array} timeseries
 * @param {number} ceiling - e.g. 0.60
 */
function renderEquityDrift(elementId, timeseries, ceiling) {
    ceiling = ceiling || 0.60;
    const dates = timeseries.map(r => r.date);

    const data = [
        {
            x: dates,
            y: timeseries.map(r => r.governed_equity_weight),
            name: 'Governed Equity',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#1E88E5', width: 2.5 }
        },
        {
            x: dates,
            y: timeseries.map(r => r.drifting_equity_weight),
            name: 'Drifting Equity',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#E53935', width: 2, dash: 'dot' }
        }
    ];

    const layout = Object.assign({}, DEFAULT_LAYOUT, {
        height: 300,
        title: 'Equity Weight vs Fiduciary Ceiling',
        yaxis: { title: 'Equity Weight', tickformat: '.0%' },
        shapes: [{
            type: 'line',
            x0: dates[0], x1: dates[dates.length - 1],
            y0: ceiling, y1: ceiling,
            line: { color: '#C62828', width: 2, dash: 'dash' }
        }],
        annotations: [{
            x: dates[dates.length - 1],
            y: ceiling,
            text: 'Policy Ceiling',
            showarrow: false,
            font: { color: '#C62828', size: 11 },
            xanchor: 'right'
        }]
    });

    Plotly.newPlot(elementId, data, layout, PLOTLY_CONFIG);
}
