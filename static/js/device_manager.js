// Device connection management and polling

document.addEventListener('DOMContentLoaded', () => {
    // --- State Variables ---
    let pendingRequests = [];
    let connectedDevices = [];
    let isApprovalModalOpen = false;
    let isPollingPending = false;
    let isPollingDevices = false;

    // --- DOM Elements ---
    // Connections List
    const connectionsList = document.getElementById('connections-list');
    
    // Approval Modal
    const approvalModal = document.getElementById('device-approval-modal');
    const approvalForm = document.getElementById('device-approval-form');
    const approveBtn = document.getElementById('approve-device-btn');
    const rejectBtn = document.getElementById('reject-device-btn');
    const approvalErrorAlert = document.getElementById('approval-error-alert');
    const pendingDeviceIdInput = document.getElementById('pending-device-id');
    const deviceKeyInput = document.getElementById('device-key');
    const approveDeviceName = document.getElementById('approve-device-name');
    const approveDeviceId = document.getElementById('approve-device-id');

    // Device Info Modal
    const infoModal = document.getElementById('device-info-modal');
    const closeInfoBtn = document.getElementById('close-device-info-btn');
    const infoOverlay = document.getElementById('device-info-overlay');
    const disconnectBtn = document.getElementById('disconnect-device-btn');
    
    const infoDeviceName = document.getElementById('info-device-name');
    const infoDeviceId = document.getElementById('info-device-id');
    const infoDeviceIp = document.getElementById('info-device-ip');
    const infoDeviceStatus = document.getElementById('info-device-status');
    const infoStatusIndicator = document.getElementById('info-status-indicator');
    const infoDeviceApproval = document.getElementById('info-device-approval');
    
    let currentViewingDeviceId = null;

    // --- Initialization ---
    startPolling();
    fetchDevices();

    // --- Polling Loops ---
    function startPolling() {
        // Poll for pending requests every 3 seconds
        setInterval(fetchPendingRequests, 3000);
        // Poll for connected device updates every 5 seconds
        setInterval(fetchDevices, 5000);
    }

    // --- API Calls & Logic ---

    // 1. Fetch Pending Requests
    async function fetchPendingRequests() {
        if (isPollingPending || isApprovalModalOpen) return;
        isPollingPending = true;
        console.log("Polling for pending requests...");

        try {
            const response = await fetch('/api/system/pending');
            console.log("Pending requests response status:", response.status);
            
            if (!response.ok) throw new Error('Failed to fetch pending requests');
            
            const data = await response.json();
            console.log("Pending requests count:", data.requests ? data.requests.length : 0);
            pendingRequests = data.requests || [];
            
            if (pendingRequests.length > 0 && !isApprovalModalOpen) {
                console.log("Triggering modal for first pending request.");
                showApprovalModal(pendingRequests[0]);
            } else if (isApprovalModalOpen) {
                console.log("Modal already open, skipping trigger.");
            }
        } catch (error) {
            console.error('Error fetching pending requests:', error);
        } finally {
            isPollingPending = false;
        }
    }

    // 2. Fetch Connected Devices
    async function fetchDevices() {
        if (isPollingDevices) return;
        isPollingDevices = true;

        try {
            const response = await fetch('/api/system/devices');
            if (!response.ok) throw new Error('Failed to fetch devices');
            
            const data = await response.json();
            connectedDevices = data.devices || [];
            renderConnectionsList();
        } catch (error) {
            console.error('Error fetching devices:', error);
        } finally {
            isPollingDevices = false;
        }
    }

    // --- Modal Interactions ---

    function showApprovalModal(request) {
        isApprovalModalOpen = true;
        
        // Reset form
        approvalForm.reset();
        approvalErrorAlert.classList.add('hidden');
        
        // Populate data
        pendingDeviceIdInput.value = request.device_id;
        approveDeviceName.textContent = request.device_name;
        approveDeviceId.textContent = `ID: ${request.device_id}`;
        
        // Show modal
        console.log("Opening approval modal for:", request.device_name);
        approvalModal.classList.remove('hidden');
        setTimeout(() => deviceKeyInput.focus(), 100);
    }

    function closeApprovalModal() {
        approvalModal.classList.add('hidden');
        isApprovalModalOpen = false;
        
        // If there are more pending requests, wait a bit then show the next one
        if (pendingRequests.length > 1) {
            setTimeout(fetchPendingRequests, 1000);
        }
    }

    // --- Action Handlers ---

    approveBtn.addEventListener('click', async () => {
        if (!approvalForm.checkValidity()) {
            approvalForm.reportValidity();
            return;
        }

        const deviceId = pendingDeviceIdInput.value;
        const deviceKey = deviceKeyInput.value.trim();

        approveBtn.disabled = true;
        approveBtn.textContent = 'Approving...';
        approvalErrorAlert.classList.add('hidden');

        try {
            const response = await fetch('/api/system/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device_id: deviceId, device_key: deviceKey })
            });

            const result = await response.json();

            if (response.ok) {
                closeApprovalModal();
                fetchDevices(); // Immediatly update the devices list
            } else {
                approvalErrorAlert.textContent = result.error || 'Invalid key or approval failed.';
                approvalErrorAlert.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Approval Error:', error);
            approvalErrorAlert.textContent = 'Network error during approval.';
            approvalErrorAlert.classList.remove('hidden');
        } finally {
            approveBtn.disabled = false;
            approveBtn.textContent = 'Approve';
        }
    });

    rejectBtn.addEventListener('click', async () => {
        const deviceId = pendingDeviceIdInput.value;
        
        rejectBtn.disabled = true;
        rejectBtn.textContent = 'Rejecting...';

        try {
            const response = await fetch('/api/system/reject', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device_id: deviceId })
            });

            if (response.ok) {
                closeApprovalModal();
            } else {
                const result = await response.json();
                approvalErrorAlert.textContent = result.error || 'Failed to reject device.';
                approvalErrorAlert.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Rejection Error:', error);
            approvalErrorAlert.textContent = 'Network error during rejection.';
            approvalErrorAlert.classList.remove('hidden');
        } finally {
            rejectBtn.disabled = false;
            rejectBtn.textContent = 'Reject';
        }
    });

    // --- Connected Devices Rendering ---

    function getDeviceIcon(name) {
        const lowerName = name.toLowerCase();
        if (lowerName.includes('pi') || lowerName.includes('berry')) return 'developer_board';
        if (lowerName.includes('phone') || lowerName.includes('mobile')) return 'smartphone';
        if (lowerName.includes('tab') || lowerName.includes('pad')) return 'tablet_android';
        return 'desktop_windows';
    }

    function renderConnectionsList() {
        if (connectedDevices.length === 0) {
            connectionsList.innerHTML = `
                <div class="px-6 py-8 text-center bg-slate-50">
                    <span class="material-symbols-outlined text-4xl text-slate-300 mb-2">devices</span>
                    <p class="text-sm font-medium text-slate-500">No devices connected</p>
                </div>
            `;
            return;
        }

        connectionsList.innerHTML = connectedDevices.map(device => {
            const isOnline = device.connection_status === 'connected';
            const statusColor = isOnline ? 'bg-green-500' : 'bg-slate-300';
            const statusText = isOnline ? 'Online' : 'Offline';
            const icon = getDeviceIcon(device.device_name);

            return `
                <div class="px-6 flex items-center justify-between hover:bg-slate-50 transition-colors py-5 cursor-pointer" onclick="openDeviceInfo('${device.device_id}')">
                    <div class="flex items-center gap-4">
                        <div class="size-10 bg-primary/5 rounded-lg flex items-center justify-center text-primary">
                            <span class="material-symbols-outlined">${icon}</span>
                        </div>
                        <div>
                            <p class="text-sm font-semibold text-slate-900">${device.device_name}</p>
                            <p class="text-xs text-slate-500">ID: ${device.device_id}</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-6">
                        <div class="flex items-center gap-2">
                            <span class="size-2 rounded-full ${statusColor}"></span>
                            <span class="text-xs font-medium text-slate-600">${statusText}</span>
                        </div>
                        <button class="text-slate-400 hover:text-primary transition-colors border-none bg-transparent cursor-pointer" title="View details">
                            <span class="material-symbols-outlined">chevron_right</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    // --- Device Info Modal ---

    window.openDeviceInfo = async function(deviceId) {
        currentViewingDeviceId = deviceId;
        
        try {
            const response = await fetch(`/api/system/device/${deviceId}`);
            if (!response.ok) throw new Error('Failed to fetch device details');
            
            const data = await response.json();
            const device = data.device;
            
            if (!device) return;

            // Populate modal
            infoDeviceName.textContent = device.device_name;
            infoDeviceId.textContent = device.device_id;
            infoDeviceIp.textContent = device.ip_address || 'Unknown';
            
            const isOnline = device.connection_status === 'connected';
            infoDeviceStatus.textContent = isOnline ? 'Connected' : 'Disconnected';
            infoStatusIndicator.className = `size-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-slate-300'}`;
            
            infoDeviceApproval.textContent = new Date(device.approved_timestamp).toLocaleString();
            
            // Show modal
            console.log("Opening device info modal for:", device.device_name);
            infoModal.classList.remove('hidden');

            // Manage Disconnect button visibility/state
            if (isOnline) {
                disconnectBtn.style.display = 'inline-flex';
                disconnectBtn.disabled = false;
                disconnectBtn.textContent = 'Disconnect Device';
            } else {
                disconnectBtn.style.display = 'none';
            }

        } catch (error) {
            console.error('Error opening device info:', error);
            alert('Failed to load device details.');
        }
    };

    function closeDeviceInfo() {
        infoModal.classList.add('hidden');
        currentViewingDeviceId = null;
    }

    closeInfoBtn.addEventListener('click', closeDeviceInfo);
    infoOverlay.addEventListener('click', closeDeviceInfo);

    disconnectBtn.addEventListener('click', async () => {
        if (!currentViewingDeviceId) return;
        
        if (!confirm('Are you sure you want to disconnect this device?')) return;

        disconnectBtn.disabled = true;
        disconnectBtn.textContent = 'Disconnecting...';

        try {
            const response = await fetch('/api/system/disconnect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device_id: currentViewingDeviceId })
            });

            if (response.ok) {
                closeDeviceInfo();
                fetchDevices(); // Refresh the list
            } else {
                const result = await response.json();
                alert(result.error || 'Failed to disconnect device.');
            }
        } catch (error) {
            console.error('Disconnect Error:', error);
            alert('Network error during disconnect.');
        } finally {
            if (disconnectBtn) {
                disconnectBtn.disabled = false;
                disconnectBtn.textContent = 'Disconnect Device';
            }
        }
    });
});
