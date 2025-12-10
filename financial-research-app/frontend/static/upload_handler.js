

/**
 * Excel Upload Handler
 * Manages file upload, validation, and company extraction
 */

class ExcelUploadHandler {
    constructor(uploadZoneId, options = {}) {
        this.uploadZone = document.getElementById(uploadZoneId);
        this.fileInput = null;
        this.options = {
            maxFileSize: options.maxFileSize || 10 * 1024 * 1024, // 10MB default
            allowedExtensions: options.allowedExtensions || ['.xlsx', '.xls'],
            onUploadStart: options.onUploadStart || (() => { }),
            onUploadProgress: options.onUploadProgress || (() => { }),
            onUploadComplete: options.onUploadComplete || (() => { }),
            onUploadError: options.onUploadError || (() => { }),
            onCompaniesExtracted: options.onCompaniesExtracted || (() => { })
        };

        this.init();
    }

    init() {
        if (!this.uploadZone) {
            console.error('Upload zone element not found');
            return;
        }

        // Create hidden file input
        this.fileInput = document.createElement('input');
        this.fileInput.type = 'file';
        this.fileInput.accept = this.options.allowedExtensions.join(',');
        this.fileInput.style.display = 'none';
        document.body.appendChild(this.fileInput);

        // Set up event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Click to upload
        this.uploadZone.addEventListener('click', () => {
            this.fileInput.click();
        });

        // File input change
        this.fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFile(file);
            }
        });

        // Drag and drop
        this.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadZone.classList.add('drag-over');
        });

        this.uploadZone.addEventListener('dragleave', () => {
            this.uploadZone.classList.remove('drag-over');
        });

        this.uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadZone.classList.remove('drag-over');

            const file = e.dataTransfer.files[0];
            if (file) {
                this.handleFile(file);
            }
        });
    }

    validateFile(file) {
        // Check file extension
        const fileName = file.name.toLowerCase();
        const hasValidExtension = this.options.allowedExtensions.some(ext =>
            fileName.endsWith(ext)
        );

        if (!hasValidExtension) {
            return {
                valid: false,
                error: `Invalid file type. Please upload ${this.options.allowedExtensions.join(' or ')} file.`
            };
        }

        // Check file size
        if (file.size > this.options.maxFileSize) {
            const maxSizeMB = (this.options.maxFileSize / (1024 * 1024)).toFixed(1);
            return {
                valid: false,
                error: `File too large. Maximum size is ${maxSizeMB}MB.`
            };
        }

        return { valid: true };
    }

    async handleFile(file) {
        // Validate file
        const validation = this.validateFile(file);
        if (!validation.valid) {
            this.options.onUploadError(validation.error);
            this.showNotification(validation.error, 'error');
            return;
        }

        // Start upload
        this.options.onUploadStart(file);

        try {
            // Upload file to server
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/excel/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const result = await response.json();

            if (result.success) {
                this.options.onUploadComplete(result);

                // Extract companies if available
                if (result.companies) {
                    this.options.onCompaniesExtracted(result.companies);
                }

                this.showNotification(`Successfully uploaded ${file.name}`, 'success');
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.options.onUploadError(error.message);
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} fade-in`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            z-index: 9999;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            max-width: 400px;
        `;

        // Set background based on type
        const colors = {
            success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            error: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            info: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
            warning: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
        };

        notification.style.background = colors[type] || colors.info;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(20px)';
            notification.style.transition = 'all 0.3s ease';

            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    }

    reset() {
        this.fileInput.value = '';
        this.uploadZone.classList.remove('drag-over');
    }
}

// Progress Tracker Component
class ProgressTracker {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.companies = [];
        this.status = {};
    }

    setCompanies(companies) {
        this.companies = companies;
        this.status = {};
        companies.forEach(company => {
            this.status[company] = 'pending';
        });
        this.render();
    }

    updateStatus(company, status, details = {}) {
        this.status[company] = status;
        this.render();
    }

    render() {
        if (!this.container) return;

        const html = `
            <div class="progress-container">
                <h3 class="mb-4">Research Progress</h3>
                <div class="progress-list">
                    ${this.companies.map(company => this.renderCompanyProgress(company)).join('')}
                </div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    renderCompanyProgress(company) {
        const status = this.status[company] || 'pending';
        const statusIcons = {
            pending: '⏳',
            processing: '🔄',
            complete: '✅',
            error: '❌'
        };

        const statusColors = {
            pending: 'var(--gray-400)',
            processing: 'var(--info-500)',
            complete: 'var(--success-500)',
            error: 'var(--error-500)'
        };

        return `
            <div class="progress-item fade-in" style="display: flex; align-items: center; padding: 12px; margin-bottom: 8px; background: var(--card-bg); border-radius: 8px; border-left: 4px solid ${statusColors[status]};">
                <span style="font-size: 24px; margin-right: 12px;">${statusIcons[status]}</span>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: var(--text-primary);">${company}</div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary); text-transform: capitalize;">${status}</div>
                </div>
            </div>
        `;
    }
}

// Company List Display
function displayCompanyList(companies, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const html = `
        <div class="company-list">
            <div class="flex items-center justify-between mb-4">
                <h3>Companies (${companies.length})</h3>
                <button class="btn btn-sm" onclick="showAddCompanyModal()" style="background: var(--gradient-success); color: white; padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer;">
                    + Add Company
                </button>
            </div>
            <div class="grid grid-3 gap-4">
                ${companies.map((company, index) => `
                    <div class="card fade-in company-card" style="animation-delay: ${index * 0.05}s;" data-company="${company}">
                        <div class="flex items-center gap-4">
                            <div style="width: 40px; height: 40px; background: var(--gradient-primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                                ${company.charAt(0)}
                            </div>
                            <div style="flex: 1;">
                                <div style="font-weight: 600; color: var(--text-primary);">${company}</div>
                                <div style="font-size: 0.75rem; color: var(--text-secondary);">Ready for research</div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Show Add Company Modal
function showAddCompanyModal() {
    const modal = document.createElement('div');
    modal.id = 'addCompanyModal';
    modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;';
    modal.innerHTML = `
        <div style="background: var(--card-bg, #fff); padding: 24px; border-radius: 12px; width: 400px; max-width: 90%;">
            <h3 style="margin-bottom: 16px;">Add New Company</h3>
            <div style="margin-bottom: 12px;">
                <label style="display: block; margin-bottom: 4px; font-weight: 500;">Company Name *</label>
                <input type="text" id="newCompanyName" placeholder="e.g., Reliance Industries" style="width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;">
            </div>
            <div style="margin-bottom: 12px;">
                <label style="display: block; margin-bottom: 4px; font-weight: 500;">Moneycontrol Slug *</label>
                <input type="text" id="newCompanySlug" placeholder="e.g., relianceindustries" style="width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;">
                <small style="color: #666;">From URL: moneycontrol.com/financials/<b>slug</b>/...</small>
            </div>
            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 4px; font-weight: 500;">Moneycontrol Code *</label>
                <input type="text" id="newCompanyCode" placeholder="e.g., RI" style="width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;">
                <small style="color: #666;">From URL: .../quarterly-results/<b>CODE</b></small>
            </div>
            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button onclick="closeAddCompanyModal()" style="padding: 8px 16px; border: 1px solid #ddd; border-radius: 6px; background: #f5f5f5; cursor: pointer;">Cancel</button>
                <button onclick="addNewCompany()" style="padding: 8px 16px; border: none; border-radius: 6px; background: var(--gradient-primary, #4f46e5); color: white; cursor: pointer;">Add Company</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Close Add Company Modal
function closeAddCompanyModal() {
    const modal = document.getElementById('addCompanyModal');
    if (modal) modal.remove();
}

// Add New Company
async function addNewCompany() {
    const name = document.getElementById('newCompanyName').value.trim();
    const slug = document.getElementById('newCompanySlug').value.trim();
    const code = document.getElementById('newCompanyCode').value.trim();
    
    if (!name || !slug || !code) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('/api/companies/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, slug, code })
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeAddCompanyModal();
            // Refresh company list
            if (result.companies) {
                extractedCompanies = result.companies;
                displayCompanyList(result.companies, 'companiesDisplay');
            }
            alert('Company added successfully!');
        } else {
            alert('Error: ' + (result.error || 'Failed to add company'));
        }
    } catch (error) {
        console.error('Error adding company:', error);
        alert('Error adding company: ' + error.message);
    }
}

// Batch Research Controller
async function startBatchResearch(companies, quarters, year) {
    if (!companies || companies.length === 0) {
        alert('No companies selected for research');
        return;
    }

    // Show progress section immediately
    const progressSection = document.getElementById('researchProgressSection');
    if (progressSection) {
        progressSection.classList.remove('hidden');
        progressSection.innerHTML = `
            <div class="card" style="text-align: center; padding: var(--space-8);">
                <div class="spinner" style="margin: 0 auto var(--space-4);"></div>
                <h3 style="margin-bottom: var(--space-2);">Starting Research...</h3>
                <p style="color: var(--text-secondary);">Initializing batch research for ${companies.length} companies</p>
            </div>
        `;
    }

    try {
        const response = await fetch('/api/research/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                companies: companies,
                quarters: quarters || ['Q1', 'Q2', 'Q3', 'Q4'],
                year: year || 2024
            })
        });

        const result = await response.json();

        if (result.success) {
            // Show success message and start polling
            if (progressSection) {
                progressSection.innerHTML = `
                    <div class="card">
                        <h3 class="mb-4">Research In Progress</h3>
                        <div class="progress-bar" style="margin-bottom: var(--space-4);">
                            <div class="progress-fill" id="batchProgressBar" style="width: 10%;">10%</div>
                        </div>
                        <p id="batchProgressMessage" style="color: var(--text-secondary); text-align: center;">Processing companies...</p>
                    </div>
                `;
            }

            // Start polling for progress with callback
            pollResearchStatus(() => {
                // On complete callback
                if (progressSection) {
                    progressSection.innerHTML = `
                        <div class="card" style="text-align: center; padding: var(--space-8); background: var(--gradient-success); color: white;">
                            <div style="font-size: 4rem; margin-bottom: var(--space-4);">✅</div>
                            <h3 style="color: white; margin-bottom: var(--space-2);">Research Complete!</h3>
                            <p style="opacity: 0.9;">All companies have been researched successfully</p>
                            <button class="btn" style="margin-top: var(--space-4); background: white; color: var(--success-500);" onclick="downloadExcel()">
                                📥 Download Results
                            </button>
                        </div>
                    `;
                }

                // Reload stats
                if (typeof loadStats === 'function') {
                    loadStats();
                }
            });
        } else {
            throw new Error(result.error || 'Failed to start research');
        }
    } catch (error) {
        console.error('Batch research error:', error);
        if (progressSection) {
            progressSection.innerHTML = `
                <div class="card" style="text-align: center; padding: var(--space-8); border: 2px solid var(--error-500);">
                    <div style="font-size: 4rem; margin-bottom: var(--space-4);">❌</div>
                    <h3 style="color: var(--error-500); margin-bottom: var(--space-2);">Research Failed</h3>
                    <p style="color: var(--text-secondary);">${error.message}</p>
                    <button class="btn btn-outline" style="margin-top: var(--space-4);" onclick="location.reload()">
                        🔄 Try Again
                    </button>
                </div>
            `;
        }
        alert(`Failed to start batch research: ${error.message}`);
    }
}

// Poll research status
let statusPollInterval = null;

function pollResearchStatus(onCompleteCallback) {
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
    }

    let pollCount = 0;

    statusPollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/research/status');
            const status = await response.json();

            pollCount++;
            console.log(`Poll #${pollCount}:`, status);

            // Update UI with status
            updateProgressUI(status);

            // Stop polling if complete
            if (!status.running && status.progress >= 100) {
                clearInterval(statusPollInterval);
                statusPollInterval = null;

                // Call completion callback if provided
                if (onCompleteCallback) {
                    setTimeout(onCompleteCallback, 500);
                }
            }
        } catch (error) {
            console.error('Status poll error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

function updateProgressUI(status) {
    console.log('Updating progress UI:', status);

    // Update progress bar in batch research section
    const batchProgressBar = document.getElementById('batchProgressBar');
    if (batchProgressBar) {
        const progress = status.progress || 0;
        batchProgressBar.style.width = `${progress}%`;
        batchProgressBar.textContent = `${Math.round(progress)}%`;
    }

    // Update status message in batch research section
    const batchProgressMessage = document.getElementById('batchProgressMessage');
    if (batchProgressMessage) {
        batchProgressMessage.textContent = status.message || 'Processing...';
    }

    // Also update the old progress bar if it exists
    const progressBar = document.getElementById('researchProgressBar');
    if (progressBar) {
        progressBar.style.width = `${status.progress || 0}%`;
    }

    // Update status message
    const statusMessage = document.getElementById('researchStatusMessage');
    if (statusMessage) {
        statusMessage.textContent = status.message || 'Processing...';
    }
}
