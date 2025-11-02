// ReconX File Status Integration Script
// Deprecated: this script was for the legacy upload.html
// The new canonical page is upload_enhanced.html which includes built-in status updates.

(function() {
    'use strict';
    
    // Configuration
    const API_BASE_URL = 'http://localhost:5000/api';
    const STATUS_UPDATE_INTERVAL = 3000; // 3 seconds
    
    let statusUpdateInterval = null;
    
    // Helper function to get auth token
    function getAuthToken() {
        return localStorage.getItem('authToken') || 'demo-token';
    }
    
    // Helper function to show notifications
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-lg text-white text-sm font-semibold ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Update file status display
    function updateFileStatusDisplay(type, status, fileInfo = null) {
        const statusElement = document.getElementById(`${type}-status-badge`);
        const detailsElement = document.getElementById(`${type}-file-details`);
        
        if (!statusElement) return;
        
        const statusConfig = {
            'not_uploaded': { class: 'bg-gray-100 text-gray-600', text: 'Not Uploaded' },
            'uploading': { class: 'bg-yellow-100 text-yellow-700', text: 'Uploading...' },
            'uploaded': { class: 'bg-blue-100 text-blue-700', text: 'Uploaded' },
            'processing': { class: 'bg-yellow-100 text-yellow-700', text: 'Processing...' },
            'processed': { class: 'bg-green-100 text-green-700', text: 'Processed' },
            'error': { class: 'bg-red-100 text-red-700', text: 'Upload Failed' }
        };
        
        const config = statusConfig[status] || statusConfig['not_uploaded'];
        statusElement.className = `px-2 py-1 rounded-full text-[9px] font-semibold ${config.class}`;
        statusElement.textContent = config.text;
        
        if (fileInfo && detailsElement && (status === 'uploaded' || status === 'processed')) {
            detailsElement.innerHTML = `
                <div class="space-y-1 text-[10px] text-[#6b7280]">
                    <div class="flex justify-between">
                        <span>File:</span>
                        <span class="font-medium">${fileInfo.original_filename || fileInfo.filename || fileInfo.name}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Size:</span>
                        <span>${formatFileSize(fileInfo.file_size || fileInfo.size)}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Records:</span>
                        <span>${fileInfo.records_count || 0}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Uploaded:</span>
                        <span>${new Date(fileInfo.uploaded_at || Date.now()).toLocaleTimeString()}</span>
                    </div>
                </div>
            `;
            detailsElement.classList.remove('hidden');
        } else if (detailsElement) {
            detailsElement.classList.add('hidden');
        }
    }
    
    // Fetch file status from API
    async function fetchFileStatus() {
        try {
            const response = await fetch(`${API_BASE_URL}/files/status/summary`, {
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch file status');
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Update bank statement status
                if (data.bank_statement.status !== 'not_uploaded') {
                    updateFileStatusDisplay('bank', data.bank_statement.status, data.bank_statement);
                }
                
                // Update collection report status  
                if (data.internal_record.status !== 'not_uploaded') {
                    updateFileStatusDisplay('collection', data.internal_record.status, data.internal_record);
                }
                
                // Update file counter
                const totalFiles = data.summary.total_files;
                const counterElement = document.getElementById('uploadedFilesCounter');
                if (counterElement) {
                    counterElement.textContent = `${totalFiles} files uploaded`;
                }
                
                console.log('File status updated:', data);
            }
        } catch (error) {
            console.error('Error fetching file status:', error);
        }
    }
    
    // Start periodic file status updates
    function startFileStatusUpdates() {
        // Fetch initial status
        fetchFileStatus();
        
        // Set up periodic updates
        statusUpdateInterval = setInterval(fetchFileStatus, STATUS_UPDATE_INTERVAL);
        
        console.log('File status updates started');
    }
    
    // Stop file status updates
    function stopFileStatusUpdates() {
        if (statusUpdateInterval) {
            clearInterval(statusUpdateInterval);
            statusUpdateInterval = null;
            console.log('File status updates stopped');
        }
    }
    
    // Enhanced upload function that triggers status refresh
    function enhanceUploadFunction() {
        // Override the existing uploadFile function if it exists
        if (typeof window.uploadFile === 'function') {
            const originalUploadFile = window.uploadFile;
            
            window.uploadFile = async function(file, type) {
                try {
                    const result = await originalUploadFile(file, type);
                    
                    // Trigger immediate status refresh after upload
                    setTimeout(fetchFileStatus, 1000);
                    
                    return result;
                } catch (error) {
                    console.error('Upload error:', error);
                    throw error;
                }
            };
        }
    }
    
    // Initialize the integration
    function init() {
        console.log('ReconX File Status Integration initialized');
        
        // Start file status updates
        startFileStatusUpdates();
        
        // Enhance upload function
        enhanceUploadFunction();
        
        // Clean up on page unload
        window.addEventListener('beforeunload', stopFileStatusUpdates);
        
        // Show success message
        showNotification('File status updates enabled', 'success');
    }
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Export functions for manual control
    window.ReconXFileStatus = {
        start: startFileStatusUpdates,
        stop: stopFileStatusUpdates,
        refresh: fetchFileStatus,
        updateDisplay: updateFileStatusDisplay
    };
    
})();
