# 🚀 ReconX Frontend Integration Guide - File Status Updates

## 📋 **Overview**

This guide shows you how to integrate the enhanced file upload system with your frontend to display real-time file status updates in the "File Status" section.

## 🔗 **API Endpoints Summary**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/files/upload/bank-statement` | Upload bank statement file | ✅ |
| `POST` | `/api/files/upload/internal-record` | Upload internal record file | ✅ |
| `GET` | `/api/files/status/summary` | Get file status summary for dashboard | ✅ |
| `GET` | `/api/files/uploads` | List all uploaded files | ✅ |
| `GET` | `/api/files/uploads/{id}` | Get specific file details | ✅ |
| `GET` | `/api/files/uploads/{id}/status` | Get file processing status | ✅ |

## 🎯 **File Status API Response**

### **GET /api/files/status/summary**

This endpoint provides everything you need for the File Status section:

```json
{
  "success": true,
  "summary": {
    "total_files": 4,
    "processed_files": 1,
    "error_files": 2,
    "processing_files": 0
  },
  "bank_statement": {
    "status": "processed",
    "filename": "test_bank_statement.csv",
    "uploaded_at": "2025-09-21T17:07:03",
    "records_count": 3,
    "file_size": 208,
    "error_message": null
  },
  "internal_record": {
    "status": "not_uploaded",
    "filename": null,
    "uploaded_at": null,
    "records_count": 0,
    "file_size": 0,
    "error_message": null
  },
  "recent_files": {
    "bank_statements": [...],
    "internal_records": [...]
  }
}
```

## 🔧 **Frontend Integration Examples**

### **1. JavaScript/React Integration**

```javascript
// File status component
const FileStatus = () => {
  const [fileStatus, setFileStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch file status
  const fetchFileStatus = async () => {
    try {
      const response = await fetch('/api/files/status/summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setFileStatus(data);
    } catch (error) {
      console.error('Failed to fetch file status:', error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 5 seconds
  useEffect(() => {
    fetchFileStatus();
    const interval = setInterval(fetchFileStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status) => {
    const statusConfig = {
      'not_uploaded': { text: 'Not Uploaded', color: 'grey' },
      'uploaded': { text: 'Uploaded', color: 'blue' },
      'processing': { text: 'Processing', color: 'yellow' },
      'processed': { text: 'Processed', color: 'green' },
      'error': { text: 'Error', color: 'red' }
    };
    const config = statusConfig[status] || statusConfig['not_uploaded'];
    return `<span class="badge badge-${config.color}">${config.text}</span>`;
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="file-status">
      <div className="status-header">
        <h3>File Status</h3>
        <span className="file-count">{fileStatus.summary.total_files} files uploaded</span>
      </div>
      
      <div className="status-items">
        <div className="status-item">
          <label>Bank Statement:</label>
          {getStatusBadge(fileStatus.bank_statement.status)}
          {fileStatus.bank_statement.filename && (
            <div className="file-details">
              <small>{fileStatus.bank_statement.filename}</small>
              <small>{fileStatus.bank_statement.records_count} records</small>
            </div>
          )}
        </div>
        
        <div className="status-item">
          <label>Collection Report:</label>
          {getStatusBadge(fileStatus.internal_record.status)}
          {fileStatus.internal_record.filename && (
            <div className="file-details">
              <small>{fileStatus.internal_record.filename}</small>
              <small>{fileStatus.internal_record.records_count} records</small>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
```

### **2. File Upload with Status Updates**

```javascript
// File upload component
const FileUpload = ({ fileType, onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileUpload = async (file) => {
    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const endpoint = fileType === 'bank' 
        ? '/api/files/upload/bank-statement'
        : '/api/files/upload/internal-record';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      const result = await response.json();

      if (result.success) {
        // Show success message
        alert(`File uploaded successfully! ${result.records_count} records processed.`);
        
        // Trigger status refresh
        if (onUploadSuccess) {
          onUploadSuccess(result);
        }
      } else {
        alert(`Upload failed: ${result.error}`);
      }
    } catch (error) {
      alert(`Upload failed: ${error.message}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="file-upload">
      <input
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={(e) => handleFileUpload(e.target.files[0])}
        disabled={uploading}
      />
      {uploading && <div className="upload-progress">Uploading...</div>}
    </div>
  );
};
```

### **3. Real-time Status Updates**

```javascript
// Main dashboard component
const Dashboard = () => {
  const [fileStatus, setFileStatus] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  // Fetch file status
  const fetchFileStatus = async () => {
    try {
      const response = await fetch('/api/files/status/summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setFileStatus(data);
    } catch (error) {
      console.error('Failed to fetch file status:', error);
    }
  };

  // Handle upload success
  const handleUploadSuccess = (uploadResult) => {
    // Refresh file status
    fetchFileStatus();
    
    // Add to uploaded files list
    setUploadedFiles(prev => [uploadResult, ...prev]);
  };

  // Auto-refresh status
  useEffect(() => {
    fetchFileStatus();
    const interval = setInterval(fetchFileStatus, 3000); // Refresh every 3 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">
      <FileUpload fileType="bank" onUploadSuccess={handleUploadSuccess} />
      <FileUpload fileType="internal" onUploadSuccess={handleUploadSuccess} />
      <FileStatus fileStatus={fileStatus} />
    </div>
  );
};
```

## 🎨 **CSS Styling Examples**

```css
/* File Status Styling */
.file-status {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.file-count {
  color: #666;
  font-size: 14px;
}

.status-items {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-item label {
  font-weight: 500;
  min-width: 120px;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-details small {
  color: #666;
  font-size: 12px;
}

/* Status Badges */
.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.badge-grey { background: #f5f5f5; color: #666; }
.badge-blue { background: #e3f2fd; color: #1976d2; }
.badge-yellow { background: #fff3e0; color: #f57c00; }
.badge-green { background: #e8f5e8; color: #388e3c; }
.badge-red { background: #ffebee; color: #d32f2f; }
```

## 📊 **Status Mapping**

| Status | Display Text | Color | Description |
|--------|-------------|-------|-------------|
| `not_uploaded` | "Not Uploaded" | Grey | No file uploaded yet |
| `uploaded` | "Uploaded" | Blue | File uploaded, waiting to process |
| `processing` | "Processing" | Yellow | File is being processed |
| `processed` | "Processed" | Green | File successfully processed |
| `error` | "Error" | Red | Processing failed |

## 🔄 **Auto-Refresh Strategy**

1. **On Page Load**: Fetch initial status
2. **After Upload**: Refresh status immediately
3. **Periodic Refresh**: Every 3-5 seconds while processing
4. **On Focus**: Refresh when user returns to tab

## 🚨 **Error Handling**

```javascript
const handleApiError = (error, response) => {
  if (response?.status === 401) {
    // Token expired, redirect to login
    localStorage.removeItem('token');
    window.location.href = '/login';
  } else if (response?.status === 403) {
    // Access denied
    alert('You do not have permission to access this resource');
  } else {
    // Generic error
    alert(`Error: ${error.message}`);
  }
};
```

## 📱 **Mobile Responsive**

```css
@media (max-width: 768px) {
  .status-items {
    gap: 10px;
  }
  
  .status-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .status-item label {
    min-width: auto;
  }
}
```

## ✅ **Testing Checklist**

- [ ] File upload shows immediate feedback
- [ ] Status updates in real-time
- [ ] Error messages display correctly
- [ ] File details show properly
- [ ] Auto-refresh works
- [ ] Mobile responsive
- [ ] Handles network errors gracefully

## 🎯 **Expected Result**

After implementing this integration, your File Status section should:

1. **Show Current Status**: Display "Processed", "Processing", "Error", or "Not Uploaded"
2. **Display File Details**: Show filename, record count, upload date
3. **Update Automatically**: Refresh status without page reload
4. **Handle Errors**: Show clear error messages
5. **Provide Feedback**: Immediate response to uploads

Your users will now see real-time updates when they upload files, exactly matching the interface you showed me!
