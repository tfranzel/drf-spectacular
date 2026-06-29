const redocSettings = JSON.parse(document.getElementById('settings').textContent);
Redoc.init(document.currentScript.dataset.schemaurl, redocSettings, document.getElementById('redoc-container'))