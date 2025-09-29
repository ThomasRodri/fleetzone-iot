// FleetZone Dashboard - JavaScript

// Elementos DOM
const totalDetections = document.getElementById('total-detections');
const uniqueMotos = document.getElementById('unique-motos');
const avgFps = document.getElementById('avg-fps');
const detectionRate = document.getElementById('detection-rate');
const uniqueClasses = document.getElementById('unique-classes');
const iotDevices = document.getElementById('iot-devices');
const detectionsTable = document.getElementById('detections-table');
const alertsContainer = document.getElementById('alerts-container');
const iotDevicesContainer = document.getElementById('iot-devices-container');

// Estado da aplicação
let alerts = [];
let iotDevicesList = [];

// Variáveis para controle de paginação
let showAllDevices = false;
const maxDevicesShow = 6;

// Função para atualizar métricas
function updateMetrics() {
    fetch('/metrics', {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            totalDetections.textContent = data.total_events.toLocaleString();
            uniqueMotos.textContent = data.unique_motos || 0;
            avgFps.textContent = data.avg_fps_last_60.toFixed(1);
            detectionRate.textContent = (data.avg_detection_rate || 0).toFixed(2);
            uniqueClasses.textContent = data.unique_classes || 0;
            
            // Atualiza métricas IoT apenas se métricas principais funcionaram
            updateIoTMetrics();
        })
        .catch(error => {
            console.error('Erro detalhado ao buscar métricas:', error.message);
            // Mostra indicador de erro na interface
            totalDetections.textContent = 'Erro';
            uniqueMotos.textContent = 'Erro';
            avgFps.textContent = 'Erro';
            detectionRate.textContent = 'Erro';
            uniqueClasses.textContent = 'Erro';
        });
}

// Função para atualizar métricas IoT
function updateIoTMetrics() {
    fetch('/iot/devices')
        .then(response => response.json())
        .then(data => {
            iotDevicesList = data;
            iotDevices.textContent = data.length;
            displayIoTDevices();
        })
        .catch(error => {
            console.error('Erro ao carregar dispositivos IoT:', error.message);
            iotDevicesContainer.innerHTML = '<p style="color: #ff5252;">Erro ao carregar dispositivos IoT</p>';
        });
}

// Função para exibir dispositivos IoT
function displayIoTDevices() {
    if (iotDevicesList.length === 0) {
        iotDevicesContainer.innerHTML = '<p style="color: #8a9bb8; font-style: italic;">Nenhum dispositivo conectado</p>';
        return;
    }
    
    const sensors = iotDevicesList.filter(d => d.device_type === 'sensor');
    const actuators = iotDevicesList.filter(d => d.device_type === 'actuator');
    
    // Limita dispositivos mostrados
    const sensorsToShow = showAllDevices ? sensors : sensors.slice(0, maxDevicesShow);
    const actuatorsToShow = showAllDevices ? actuators : actuators.slice(0, 3);
    
    let html = '<div style="margin-bottom: 15px;">';
    html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">`;
    html += `<h4 style="color: #9fb0ff; margin: 0;">Sensores (${sensors.length})</h4>`;
    
    if (sensors.length > maxDevicesShow) {
        html += `<button onclick="toggleDevicesView()" style="background: #4a5568; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; cursor: pointer;">
            ${showAllDevices ? 'Ver Menos' : 'Ver Mais'}
        </button>`;
    }
    html += '</div>';
    
    sensorsToShow.forEach(sensor => {
        const statusClass = sensor.status === 'active' ? 'status-online' : 'status-offline';
        const batteryClass = sensor.battery_level > 50 ? 'confidence-high' : 
                           sensor.battery_level > 20 ? 'confidence-medium' : 'confidence-low';
        
        html += `
            <div style="background: rgba(255, 255, 255, 0.05); padding: 8px; margin-bottom: 8px; border-radius: 6px; font-size: 0.8rem;">
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span class="status-indicator ${statusClass}"></span>
                    <strong>${sensor.device_id}</strong>
                </div>
                <div style="color: #8a9bb8;">${sensor.location}</div>
                <div style="color: #8a9bb8;">Bateria: <span class="${batteryClass}">${sensor.battery_level}%</span></div>
            </div>
        `;
    });
    
    if (!showAllDevices && sensors.length > maxDevicesShow) {
        html += `<div style="color: #8a9bb8; font-style: italic; text-align: center; padding: 8px;">
            ... e mais ${sensors.length - maxDevicesShow} sensores
        </div>`;
    }
    
    html += '</div>';
    
    if (actuators.length > 0) {
        html += '<div style="margin-top: 20px;">';
        html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">`;
        html += `<h4 style="color: #9fb0ff; margin: 0;">Atuadores (${actuators.length})</h4>`;
        
        if (actuators.length > 3) {
            html += `<button onclick="toggleDevicesView()" style="background: #4a5568; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; cursor: pointer;">
                ${showAllDevices ? 'Ver Menos' : 'Ver Mais'}
            </button>`;
        }
        html += '</div>';
        
        actuatorsToShow.forEach(actuator => {
            const statusClass = actuator.status === 'idle' ? 'status-offline' : 'status-online';
            
            html += `
                <div style="background: rgba(255, 255, 255, 0.05); padding: 8px; margin-bottom: 8px; border-radius: 6px; font-size: 0.8rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span class="status-indicator ${statusClass}"></span>
                        <strong>${actuator.device_id}</strong>
                    </div>
                    <div style="color: #8a9bb8;">${actuator.location}</div>
                    <div style="color: #8a9bb8;">Status: ${actuator.status}</div>
                </div>
            `;
        });
        
        if (!showAllDevices && actuators.length > 3) {
            html += `<div style="color: #8a9bb8; font-style: italic; text-align: center; padding: 8px;">
                ... e mais ${actuators.length - 3} atuadores
            </div>`;
        }
        
        html += '</div>';
    }
    
    iotDevicesContainer.innerHTML = html;
}

// Função para carregar alertas
function loadAlerts() {
    fetch('/alerts')
        .then(response => response.json())
        .then(data => {
            alerts = data;
            displayAlerts();
        })
        .catch(error => {
            console.error('Erro ao carregar alertas:', error.message);
            alertsContainer.innerHTML = '<p style="color: #ff5252;">Erro ao carregar alertas</p>';
        });
}

// Função para exibir alertas
function displayAlerts() {
    if (alerts.length === 0) {
        alertsContainer.innerHTML = '<p style="color: #8a9bb8; font-style: italic;">Nenhum alerta ativo</p>';
        return;
    }
    
    alertsContainer.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.severity}">
            <strong>${alert.alert_type}</strong><br>
            ${alert.message}<br>
            <small>${new Date(alert.created_at).toLocaleTimeString()}</small>
        </div>
    `).join('');
}

// Função para adicionar detecção à tabela
function addDetection(detection) {
    const row = document.createElement('tr');
    
    const confidenceClass = detection.confidence > 0.7 ? 'confidence-high' : 
                          detection.confidence > 0.4 ? 'confidence-medium' : 'confidence-low';
    
    const classBadgeClass = detection.class_name === 'motorbike' ? 'class-motorbike' :
                           detection.class_name === 'bicycle' ? 'class-bicycle' : 'class-car';
    
    row.innerHTML = `
        <td>${new Date(detection.created_at).toLocaleTimeString()}</td>
        <td>${detection.frame}</td>
        <td><span class="class-badge ${classBadgeClass}">${detection.class_name}</span></td>
        <td class="${confidenceClass}">${(detection.confidence * 100).toFixed(1)}%</td>
        <td>${detection.area.toLocaleString()}</td>
        <td>${detection.fps?.toFixed(1) || '0.0'}</td>
    `;
    
    detectionsTable.insertBefore(row, detectionsTable.firstChild);
    
    // Mantém apenas as últimas 20 linhas
    while (detectionsTable.rows.length > 20) {
        detectionsTable.deleteRow(-1);
    }
}

// Função para alternar visualização de dispositivos
function toggleDevicesView() {
    showAllDevices = !showAllDevices;
    displayIoTDevices();
}

// Função de inicialização
function initializeDashboard() {
    updateMetrics();
    loadAlerts();
    updateIoTMetrics();
    
    // Atualiza métricas a cada 2 segundos
    setInterval(updateMetrics, 2000);
    setInterval(loadAlerts, 5000);
    setInterval(updateIoTMetrics, 3000);
}

// Configuração do Socket.IO
function setupSocketIO() {
    const socket = io();
    
    socket.on('connect', () => {
        console.log('Conectado ao servidor');
    });
    
    socket.on('detection', (detection) => {
        addDetection(detection);
        updateMetrics();
    });
    
    socket.on('alert', (alert) => {
        alerts.unshift(alert);
        if (alerts.length > 10) alerts.pop();
        displayAlerts();
        updateMetrics();
    });
    
    socket.on('iot_sensor', (data) => {
        console.log('Dados IoT Sensor:', data);
        updateIoTMetrics();
    });
    
    socket.on('iot_actuator', (data) => {
        console.log('Dados IoT Atuador:', data);
        updateIoTMetrics();
    });
    
    socket.on('disconnect', () => {
        console.log('Desconectado do servidor');
    });
}

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
    setupSocketIO();
});
