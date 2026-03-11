async function startTracing() {
    const eq = document.getElementById('eq').value;
    const p = document.getElementById('p').value;
    const res = await fetch('/trace', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({eq: eq, p: p})
    });
    const data = await res.json();
    
    let html = '<h3>जासूसी रिपोर्ट</h3>';
    for (let key in data.report) {
        let info = data.report[key];
        html += `<div class="report-card">
                    <b style="color:#4f46e5">${key}</b><br>
                    <i>क्यों?:</i> ${info['क्यों?']}<br>
                    <i>रिजल्ट:</i> ${info['रिजल्ट']}<br>
                    <i>मतलब:</i> ${info['मतलब']}
                 </div>`;
    }
    document.getElementById('results').innerHTML = html;
    const graph = JSON.parse(data.graph);
    Plotly.newPlot('plot', graph.data, graph.layout);
}
