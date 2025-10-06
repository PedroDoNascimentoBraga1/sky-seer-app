document.addEventListener('DOMContentLoaded', () => {

    // 1. INICIALIZAÇÃO DO MAPA
    const map = L.map('map').setView([-22.9068, -43.1729], 12);

    // --- ALTERAÇÃO PRINCIPAL: Troca do tileLayer para um tema escuro ---
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    }).addTo(map);

    // Pega o campo de input que mostrará as coordenadas
    const coordinatesInput = document.getElementById('coordinates');

    // 2. CONFIGURAÇÃO DA FERRAMENTA DE DESENHO
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems,
            remove: true
        },
        draw: {
            polygon: false,
            polyline: false,
            circle: false,
            circlemarker: false,
            marker: true,
            rectangle: true,
        }
    });
    map.addControl(drawControl);

    // 3. EVENTO PARA CAPTURAR O DESENHO FINALIZADO
    map.on(L.Draw.Event.CREATED, (event) => {
        const layer = event.layer;
        const type = event.layerType;

        drawnItems.clearLayers();
        drawnItems.addLayer(layer);

        if (type === 'marker') {
            const latlng = layer.getLatLng();
            const formattedCoords = `${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`;
            coordinatesInput.value = formattedCoords;
        } else if (type === 'rectangle') {
            const bounds = layer.getBounds();
            const boundsJSON = JSON.stringify({
                northEast: bounds.getNorthEast(),
                southWest: bounds.getSouthWest()
            });
            coordinatesInput.value = boundsJSON;
        }
    });

    map.on('draw:deleted', () => {
        coordinatesInput.value = '';
    });
    
    document.getElementById('event-date').valueAsDate = new Date();
});