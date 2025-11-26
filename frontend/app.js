const API_URL = '';

let companies = [];
let currentCompany = null;
let inputMode = 'paste'; // 'paste' or 'url'
let cookieInputMode = 'paste'; // 'paste' or 'url'
let privacyInputMode = 'paste'; // 'paste' or 'url'
let currentTab = 'terms'; // 'terms', 'cookies', 'privacy', or 'all'

// DOM Elements
const companiesGrid = document.getElementById('companiesGrid');
const loading = document.getElementById('loading');
const emptyState = document.getElementById('emptyState');
const companyModal = document.getElementById('companyModal');
const addModal = document.getElementById('addModal');
const cookieModal = document.getElementById('cookieModal');
const privacyModal = document.getElementById('privacyModal');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCompanies();
    setupEventListeners();
});

function setupEventListeners() {
    // Seed buttons
    document.getElementById('seedBtn').addEventListener('click', seedDatabase);
    document.getElementById('seedRealBtn').addEventListener('click', seedRealData);
    document.getElementById('analyzeAllBtn').addEventListener('click', analyzeAllCompanies);

    // Add company button
    document.getElementById('addCompanyBtn').addEventListener('click', () => {
        addModal.style.display = 'block';
    });

    // Close modals
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', () => {
            companyModal.style.display = 'none';
            addModal.style.display = 'none';
            cookieModal.style.display = 'none';
            privacyModal.style.display = 'none';
        });
    });

    // Click outside modal to close
    window.addEventListener('click', (e) => {
        if (e.target === companyModal) companyModal.style.display = 'none';
        if (e.target === addModal) addModal.style.display = 'none';
        if (e.target === cookieModal) cookieModal.style.display = 'none';
        if (e.target === privacyModal) privacyModal.style.display = 'none';
    });

    // Add company form
    document.getElementById('addCompanyForm').addEventListener('submit', handleAddCompany);

    // Cancel add button
    document.getElementById('cancelAddBtn').addEventListener('click', () => {
        addModal.style.display = 'none';
    });

    // Analyze button
    document.getElementById('analyzeBtn').addEventListener('click', analyzeCompany);

    // Delete button
    document.getElementById('deleteBtn').addEventListener('click', deleteCompany);

    // Toggle terms visibility
    document.getElementById('toggleTermsBtn').addEventListener('click', toggleTerms);
    document.getElementById('toggleCookieBtn').addEventListener('click', toggleCookie);
    document.getElementById('togglePrivacyBtn').addEventListener('click', togglePrivacy);

    // Cookie policy buttons
    document.getElementById('uploadCookieBtn').addEventListener('click', () => {
        cookieModal.style.display = 'block';
    });
    document.getElementById('cancelCookieBtn').addEventListener('click', () => {
        cookieModal.style.display = 'none';
    });
    document.getElementById('uploadCookieForm').addEventListener('submit', handleUploadCookie);
    document.getElementById('analyzeCookieBtn').addEventListener('click', analyzeCookiePolicy);

    // Privacy policy buttons
    document.getElementById('uploadPrivacyBtn').addEventListener('click', () => {
        privacyModal.style.display = 'block';
    });
    document.getElementById('cancelPrivacyBtn').addEventListener('click', () => {
        privacyModal.style.display = 'none';
    });
    document.getElementById('uploadPrivacyForm').addEventListener('submit', handleUploadPrivacy);
    document.getElementById('analyzePrivacyBtn').addEventListener('click', analyzePrivacyPolicy);
}

async function loadCompanies() {
    try {
        loading.style.display = 'block';
        emptyState.style.display = 'none';
        companiesGrid.innerHTML = '';

        const response = await fetch(`${API_URL}/api/companies`);
        companies = await response.json();

        loading.style.display = 'none';

        if (companies.length === 0) {
            emptyState.style.display = 'block';
        } else {
            renderCompanies();
        }
    } catch (error) {
        console.error('Error loading companies:', error);
        loading.style.display = 'none';
        emptyState.style.display = 'block';
        emptyState.querySelector('p').textContent = 'Error loading companies. Please try again.';
    }
}

function renderCompanies() {
    companiesGrid.innerHTML = companies.map(company => {
        // Support both old and new schema
        const risks = company.terms_risks || company.risks || [];
        const riskCounts = {
            high: risks.filter(r => r.severity === 'high').length,
            medium: risks.filter(r => r.severity === 'medium').length,
            low: risks.filter(r => r.severity === 'low').length
        };

        const iconContent = company.icon_url
            ? `<img src="${company.icon_url}" alt="${company.name}" onerror="this.parentElement.innerHTML='${company.name[0]}'">`
            : company.name[0];

        return `
            <div class="company-card" onclick="showCompanyDetails('${company.id}')">
                <div class="company-icon">${iconContent}</div>
                <h3>${company.name}</h3>
                <span class="category">${company.category}</span>
                <div class="risk-indicator">
                    ${Array(riskCounts.high).fill('<span class="risk-dot high"></span>').join('')}
                    ${Array(riskCounts.medium).fill('<span class="risk-dot medium"></span>').join('')}
                    ${Array(riskCounts.low).fill('<span class="risk-dot low"></span>').join('')}
                </div>
            </div>
        `;
    }).join('');
}

function showCompanyDetails(companyId) {
    currentCompany = companies.find(c => c.id === companyId);
    if (!currentCompany) return;

    const iconContent = currentCompany.icon_url
        ? `<img src="${currentCompany.icon_url}" alt="${currentCompany.name}" onerror="this.parentElement.innerHTML='${currentCompany.name[0]}'">`
        : currentCompany.name[0];

    document.getElementById('modalIcon').innerHTML = iconContent;
    document.getElementById('modalCompanyName').textContent = currentCompany.name;
    document.getElementById('modalCategory').textContent = currentCompany.category;

    // Update risk counts in tabs (support both old and new schema)
    const termsRisks = currentCompany.terms_risks || currentCompany.risks || [];
    const cookieRisks = currentCompany.cookie_risks || [];
    const privacyRisks = currentCompany.privacy_risks || [];
    const totalRisks = termsRisks.length + cookieRisks.length + privacyRisks.length;

    document.getElementById('termsRiskCount').textContent = termsRisks.length || '';
    document.getElementById('cookiesRiskCount').textContent = cookieRisks.length || '';
    document.getElementById('privacyRiskCount').textContent = privacyRisks.length || '';
    document.getElementById('allRiskCount').textContent = totalRisks || '';

    // Populate Terms tab
    populateTermsTab();

    // Populate Cookies tab
    populateCookiesTab();

    // Populate Privacy tab
    populatePrivacyTab();

    // Populate All Combined tab
    populateAllTab();

    // Reset to terms tab
    switchDocumentTab('terms');

    companyModal.style.display = 'block';
}

function populateTermsTab() {
    // Support both old and new schema
    const risks = currentCompany.terms_risks || currentCompany.risks || [];
    
    document.getElementById('modalSummary').textContent = 
        currentCompany.terms_summary || currentCompany.summary || 'No summary available. Click "Analyze Terms with AI" to generate one.';

    const risksList = document.getElementById('risksList');
    if (risks.length === 0) {
        risksList.innerHTML = '<p class="no-risks">No risks analyzed yet. Click "Analyze Terms with AI" to identify privacy risks.</p>';
    } else {
        risksList.innerHTML = risks.map(risk => `
            <div class="risk-item ${risk.severity}">
                <h4>
                    ${risk.title}
                    <span class="severity-badge ${risk.severity}">${risk.severity}</span>
                </h4>
                <p>${risk.description}</p>
            </div>
        `).join('');
    }

    document.getElementById('originalTerms').textContent = currentCompany.terms_text || 'No terms text available.';
    document.getElementById('termsContent').style.display = 'none';
    document.getElementById('toggleTermsBtn').classList.remove('active');
}

function populateCookiesTab() {
    const cookieRisks = currentCompany.cookie_risks || [];
    const hasCookiePolicy = currentCompany.cookie_text;

    document.getElementById('modalCookieSummary').textContent = 
        currentCompany.cookie_summary || (hasCookiePolicy ? 'Click "Analyze Cookie Policy" to generate summary.' : 'No cookie policy uploaded yet.');

    const cookieRisksList = document.getElementById('cookieRisksList');
    if (cookieRisks.length === 0) {
        cookieRisksList.innerHTML = hasCookiePolicy 
            ? '<p class="no-risks">No risks analyzed yet. Click "Analyze Cookie Policy" to identify tracking risks.</p>'
            : '<p class="no-risks">Upload a cookie policy to analyze tracking and privacy risks.</p>';
    } else {
        cookieRisksList.innerHTML = cookieRisks.map(risk => `
            <div class="risk-item ${risk.severity}">
                <h4>
                    ${risk.title}
                    <span class="severity-badge ${risk.severity}">${risk.severity}</span>
                </h4>
                <p>${risk.description}</p>
            </div>
        `).join('');
    }

    document.getElementById('originalCookie').textContent = currentCompany.cookie_text || 'No cookie policy available.';
    document.getElementById('cookieContent').style.display = 'none';
    document.getElementById('toggleCookieBtn').classList.remove('active');

    // Show/hide analyze button based on whether cookie policy exists
    document.getElementById('analyzeCookieBtn').style.display = hasCookiePolicy ? 'inline-block' : 'none';
}

function populatePrivacyTab() {
    const privacyRisks = currentCompany.privacy_risks || [];
    const hasPrivacyPolicy = currentCompany.privacy_text;

    document.getElementById('modalPrivacySummary').textContent = 
        currentCompany.privacy_summary || (hasPrivacyPolicy ? 'Click "Analyze Privacy Policy" to generate summary.' : 'No privacy policy uploaded yet.');

    const privacyRisksList = document.getElementById('privacyRisksList');
    if (privacyRisks.length === 0) {
        privacyRisksList.innerHTML = hasPrivacyPolicy 
            ? '<p class="no-risks">No risks analyzed yet. Click "Analyze Privacy Policy" to identify privacy risks.</p>'
            : '<p class="no-risks">Upload a privacy policy to analyze data protection and privacy risks.</p>';
    } else {
        privacyRisksList.innerHTML = privacyRisks.map(risk => `
            <div class="risk-item ${risk.severity}">
                <h4>
                    ${risk.title}
                    <span class="severity-badge ${risk.severity}">${risk.severity}</span>
                </h4>
                <p>${risk.description}</p>
            </div>
        `).join('');
    }

    document.getElementById('originalPrivacy').textContent = currentCompany.privacy_text || 'No privacy policy available.';
    document.getElementById('privacyContent').style.display = 'none';
    document.getElementById('togglePrivacyBtn').classList.remove('active');

    // Show/hide analyze button based on whether privacy policy exists
    document.getElementById('analyzePrivacyBtn').style.display = hasPrivacyPolicy ? 'inline-block' : 'none';
}

function populateAllTab() {
    // Support both old and new schema
    const termsRisks = currentCompany.terms_risks || currentCompany.risks || [];
    const cookieRisks = currentCompany.cookie_risks || [];
    const privacyRisks = currentCompany.privacy_risks || [];
    const allRisks = [...termsRisks, ...cookieRisks, ...privacyRisks];

    // Populate summaries (support both old and new schema)
    document.getElementById('allTermsSummary').textContent = 
        currentCompany.terms_summary || currentCompany.summary || 'No terms analysis available.';
    document.getElementById('allCookieSummary').textContent = 
        currentCompany.cookie_summary || 'No cookie policy analysis available.';
    document.getElementById('allPrivacySummary').textContent = 
        currentCompany.privacy_summary || 'No privacy policy analysis available.';

    // Populate combined risks
    const allRisksList = document.getElementById('allRisksList');
    if (allRisks.length === 0) {
        allRisksList.innerHTML = '<p class="no-risks">No risks analyzed yet. Analyze terms, cookie, and privacy policies to see all privacy risks.</p>';
    } else {
        // Group by severity
        const highRisks = allRisks.filter(r => r.severity === 'high');
        const mediumRisks = allRisks.filter(r => r.severity === 'medium');
        const lowRisks = allRisks.filter(r => r.severity === 'low');

        let html = '';
        
        if (highRisks.length > 0) {
            html += '<div class="risk-group"><h4 class="risk-group-title high">🔴 High Risk</h4>';
            html += highRisks.map(risk => `
                <div class="risk-item ${risk.severity}">
                    <h4>${risk.title}</h4>
                    <p>${risk.description}</p>
                </div>
            `).join('');
            html += '</div>';
        }

        if (mediumRisks.length > 0) {
            html += '<div class="risk-group"><h4 class="risk-group-title medium">🟡 Medium Risk</h4>';
            html += mediumRisks.map(risk => `
                <div class="risk-item ${risk.severity}">
                    <h4>${risk.title}</h4>
                    <p>${risk.description}</p>
                </div>
            `).join('');
            html += '</div>';
        }

        if (lowRisks.length > 0) {
            html += '<div class="risk-group"><h4 class="risk-group-title low">🟢 Low Risk</h4>';
            html += lowRisks.map(risk => `
                <div class="risk-item ${risk.severity}">
                    <h4>${risk.title}</h4>
                    <p>${risk.description}</p>
                </div>
            `).join('');
            html += '</div>';
        }

        allRisksList.innerHTML = html;
    }
}

function switchDocumentTab(tabName) {
    currentTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

function toggleTerms() {
    const btn = document.getElementById('toggleTermsBtn');
    const content = document.getElementById('termsContent');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        btn.classList.add('active');
    } else {
        content.style.display = 'none';
        btn.classList.remove('active');
    }
}

function toggleCookie() {
    const btn = document.getElementById('toggleCookieBtn');
    const content = document.getElementById('cookieContent');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        btn.classList.add('active');
    } else {
        content.style.display = 'none';
        btn.classList.remove('active');
    }
}

function togglePrivacy() {
    const btn = document.getElementById('togglePrivacyBtn');
    const content = document.getElementById('privacyContent');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        btn.classList.add('active');
    } else {
        content.style.display = 'none';
        btn.classList.remove('active');
    }
}

function setInputMode(mode) {
    inputMode = mode;
    const pasteBtn = document.getElementById('togglePaste');
    const urlBtn = document.getElementById('toggleUrl');
    const autoBtn = document.getElementById('toggleAuto');
    const pasteGroup = document.getElementById('pasteGroup');
    const urlGroup = document.getElementById('urlGroup');
    const autoGroup = document.getElementById('autoGroup');

    // Reset all buttons
    [pasteBtn, urlBtn, autoBtn].forEach(btn => btn.classList.remove('active'));
    [pasteGroup, urlGroup, autoGroup].forEach(group => group.style.display = 'none');

    // Activate selected mode
    if (mode === 'paste') {
        pasteBtn.classList.add('active');
        pasteGroup.style.display = 'block';
    } else if (mode === 'url') {
        urlBtn.classList.add('active');
        urlGroup.style.display = 'block';
    } else if (mode === 'auto') {
        autoBtn.classList.add('active');
        autoGroup.style.display = 'block';
    }
}

function setCookieInputMode(mode) {
    cookieInputMode = mode;
    const pasteBtn = document.getElementById('toggleCookiePaste');
    const urlBtn = document.getElementById('toggleCookieUrl');
    const pasteGroup = document.getElementById('cookiePasteGroup');
    const urlGroup = document.getElementById('cookieUrlGroup');

    if (mode === 'paste') {
        pasteBtn.classList.add('active');
        urlBtn.classList.remove('active');
        pasteGroup.style.display = 'block';
        urlGroup.style.display = 'none';
    } else {
        pasteBtn.classList.remove('active');
        urlBtn.classList.add('active');
        pasteGroup.style.display = 'none';
        urlGroup.style.display = 'block';
    }
}

function setPrivacyInputMode(mode) {
    privacyInputMode = mode;
    const pasteBtn = document.getElementById('togglePrivacyPaste');
    const urlBtn = document.getElementById('togglePrivacyUrl');
    const pasteGroup = document.getElementById('privacyPasteGroup');
    const urlGroup = document.getElementById('privacyUrlGroup');

    if (mode === 'paste') {
        pasteBtn.classList.add('active');
        urlBtn.classList.remove('active');
        pasteGroup.style.display = 'block';
        urlGroup.style.display = 'none';
    } else {
        pasteBtn.classList.remove('active');
        urlBtn.classList.add('active');
        pasteGroup.style.display = 'none';
        urlGroup.style.display = 'block';
    }
}

async function seedDatabase() {
    const btn = document.getElementById('seedBtn');
    btn.disabled = true;
    btn.textContent = 'Loading...';

    try {
        await fetch(`${API_URL}/api/seed`, { method: 'POST' });
        await loadCompanies();
    } catch (error) {
        console.error('Error seeding database:', error);
        alert('Error loading sample data. Please try again.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Load Sample Data';
    }
}

async function seedRealData() {
    const btn = document.getElementById('seedRealBtn');
    btn.disabled = true;
    btn.textContent = 'Fetching Real Data...';

    try {
        const response = await fetch(`${API_URL}/api/seed-with-real-data`, { method: 'POST' });
        const result = await response.json();
        
        if (result.errors && result.errors.length > 0) {
            console.warn('Some companies had errors:', result.errors);
        }
        
        await loadCompanies();
        alert(`Successfully loaded ${result.companies_created} companies with real data!`);
    } catch (error) {
        console.error('Error seeding real data:', error);
        alert('Error loading real data. Please try again.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Load Real Data';
    }
}

async function analyzeAllCompanies() {
    const btn = document.getElementById('analyzeAllBtn');
    btn.disabled = true;
    btn.textContent = 'Analyzing...';

    try {
        const response = await fetch(`${API_URL}/api/analyze-all`, { method: 'POST' });
        const result = await response.json();
        
        if (result.errors && result.errors.length > 0) {
            console.warn('Some companies had analysis errors:', result.errors);
        }
        
        await loadCompanies();
        alert(`Successfully analyzed ${result.companies_analyzed} documents! Refresh the page to see the results.`);
    } catch (error) {
        console.error('Error analyzing companies:', error);
        alert('Error analyzing companies. Please try again.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyze All';
    }
}

async function handleAddCompany(e) {
    e.preventDefault();

    const name = document.getElementById('companyName').value;
    const category = document.getElementById('companyCategory').value;

    // Get form data based on input mode
    let requestData = {
        company_name: name,
        category: category
    };

    if (inputMode === 'paste') {
        const termsText = document.getElementById('termsText').value;
        const cookieText = document.getElementById('cookieTextAdd').value;
        const privacyText = document.getElementById('privacyTextAdd').value;

        if (!termsText.trim()) {
            alert('Please paste at least the terms and conditions text.');
            return;
        }

        requestData.terms_text = termsText;
        if (cookieText.trim()) requestData.cookie_text = cookieText;
        if (privacyText.trim()) requestData.privacy_text = privacyText;

    } else if (inputMode === 'url') {
        const termsUrl = document.getElementById('termsUrl').value;
        const cookieUrl = document.getElementById('cookieUrlAdd').value;
        const privacyUrl = document.getElementById('privacyUrlAdd').value;

        if (!termsUrl.trim()) {
            alert('Please enter at least the terms and conditions URL.');
            return;
        }

        requestData.terms_url = termsUrl;
        if (cookieUrl.trim()) requestData.cookie_url = cookieUrl;
        if (privacyUrl.trim()) requestData.privacy_url = privacyUrl;

    } else if (inputMode === 'auto') {
        requestData.auto_fetch = true;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    
    let statusText = 'Analyzing...';
    if (inputMode === 'url') statusText = 'Fetching & Analyzing...';
    if (inputMode === 'auto') statusText = 'Auto-Fetching & Analyzing...';
    submitBtn.textContent = statusText;

    try {
        // For auto mode, use the new enhanced endpoint
        const endpoint = inputMode === 'auto' ? '/api/companies/auto-create' : '/api/companies';
        
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.detail || 'Failed to add company');
        }

        addModal.style.display = 'none';
        document.getElementById('addCompanyForm').reset();
        // Reset all URL fields
        ['termsUrl', 'cookieUrlAdd', 'privacyUrlAdd'].forEach(id => {
            document.getElementById(id).value = '';
        });
        setInputMode('paste'); // Reset to paste mode
        await loadCompanies();

        // Show the newly added company
        showCompanyDetails(responseData.id);

    } catch (error) {
        console.error('Error adding company:', error);
        alert(error.message || 'Error adding company. Please try again.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Add & Analyze';
    }
}

async function analyzeCompany() {
    if (!currentCompany) return;

    const btn = document.getElementById('analyzeBtn');
    const risksList = document.getElementById('risksList');

    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    risksList.innerHTML = '<div class="analyzing"><div class="spinner"></div><span>AI is analyzing the terms...</span></div>';

    try {
        const response = await fetch(`${API_URL}/api/companies/${currentCompany.id}/analyze`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Analysis failed');

        const updatedCompany = await response.json();

        // Update local data
        const index = companies.findIndex(c => c.id === currentCompany.id);
        if (index !== -1) {
            companies[index] = updatedCompany;
        }

        // Refresh the modal
        showCompanyDetails(currentCompany.id);
        renderCompanies();

    } catch (error) {
        console.error('Error analyzing company:', error);
        risksList.innerHTML = '<p class="no-risks" style="color: #f44336;">Analysis failed. Please try again.</p>';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyze with AI';
    }
}

async function deleteCompany() {
    if (!currentCompany) return;

    if (!confirm(`Are you sure you want to delete ${currentCompany.name}?`)) return;

    try {
        await fetch(`${API_URL}/api/companies/${currentCompany.id}`, {
            method: 'DELETE'
        });

        companyModal.style.display = 'none';
        await loadCompanies();

    } catch (error) {
        console.error('Error deleting company:', error);
        alert('Error deleting company. Please try again.');
    }
}

// ==================== Cookie Policy Functions ====================

async function handleUploadCookie(e) {
    e.preventDefault();

    if (!currentCompany) return;

    const cookieText = document.getElementById('cookieText').value;
    const cookieUrl = document.getElementById('cookieUrl').value;

    // Validation
    if (cookieInputMode === 'paste' && !cookieText.trim()) {
        alert('Please paste the cookie policy text.');
        return;
    }
    if (cookieInputMode === 'url' && !cookieUrl.trim()) {
        alert('Please enter the URL for the cookie policy.');
        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = cookieInputMode === 'url' ? 'Fetching & Analyzing...' : 'Analyzing...';

    const requestBody = {};
    if (cookieInputMode === 'paste') {
        requestBody.cookie_text = cookieText;
    } else {
        requestBody.cookie_url = cookieUrl;
    }

    try {
        const response = await fetch(`${API_URL}/api/companies/${currentCompany.id}/cookie`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to upload cookie policy');
        }

        const updatedCompany = await response.json();

        // Update local data
        const index = companies.findIndex(c => c.id === currentCompany.id);
        if (index !== -1) {
            companies[index] = updatedCompany;
        }

        cookieModal.style.display = 'none';
        document.getElementById('uploadCookieForm').reset();
        setCookieInputMode('paste');

        // Refresh the modal
        showCompanyDetails(currentCompany.id);
        switchDocumentTab('cookies');

    } catch (error) {
        console.error('Error uploading cookie policy:', error);
        alert(error.message || 'Error uploading cookie policy. Please try again.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Upload & Analyze';
    }
}

async function analyzeCookiePolicy() {
    if (!currentCompany) return;

    const btn = document.getElementById('analyzeCookieBtn');
    const risksList = document.getElementById('cookieRisksList');

    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    risksList.innerHTML = '<div class="analyzing"><div class="spinner"></div><span>AI is analyzing the cookie policy...</span></div>';

    try {
        const response = await fetch(`${API_URL}/api/companies/${currentCompany.id}/analyze-cookie`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Cookie policy analysis failed');

        const updatedCompany = await response.json();

        // Update local data
        const index = companies.findIndex(c => c.id === currentCompany.id);
        if (index !== -1) {
            companies[index] = updatedCompany;
        }

        // Refresh the modal
        showCompanyDetails(currentCompany.id);
        switchDocumentTab('cookies');

    } catch (error) {
        console.error('Error analyzing cookie policy:', error);
        risksList.innerHTML = '<p class="no-risks" style="color: #f44336;">Analysis failed. Please try again.</p>';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyze Cookie Policy';
    }
}

// ==================== Privacy Policy Functions ====================

async function handleUploadPrivacy(e) {
    e.preventDefault();

    if (!currentCompany) return;

    const privacyText = document.getElementById('privacyText').value;
    const privacyUrl = document.getElementById('privacyUrl').value;

    // Validation
    if (privacyInputMode === 'paste' && !privacyText.trim()) {
        alert('Please paste the privacy policy text.');
        return;
    }
    if (privacyInputMode === 'url' && !privacyUrl.trim()) {
        alert('Please enter the URL for the privacy policy.');
        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = privacyInputMode === 'url' ? 'Fetching & Analyzing...' : 'Analyzing...';

    const requestBody = {};
    if (privacyInputMode === 'paste') {
        requestBody.privacy_text = privacyText;
    } else {
        requestBody.privacy_url = privacyUrl;
    }

    try {
        const response = await fetch(`${API_URL}/api/companies/${currentCompany.id}/privacy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to upload privacy policy');
        }

        const updatedCompany = await response.json();

        // Update local data
        const index = companies.findIndex(c => c.id === currentCompany.id);
        if (index !== -1) {
            companies[index] = updatedCompany;
        }

        privacyModal.style.display = 'none';
        document.getElementById('uploadPrivacyForm').reset();
        setPrivacyInputMode('paste');

        // Refresh the modal
        showCompanyDetails(currentCompany.id);
        switchDocumentTab('privacy');

    } catch (error) {
        console.error('Error uploading privacy policy:', error);
        alert(error.message || 'Error uploading privacy policy. Please try again.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Upload & Analyze';
    }
}

async function analyzePrivacyPolicy() {
    if (!currentCompany) return;

    const btn = document.getElementById('analyzePrivacyBtn');
    const risksList = document.getElementById('privacyRisksList');

    btn.disabled = true;
    btn.textContent = 'Analyzing...';
    risksList.innerHTML = '<div class="analyzing"><div class="spinner"></div><span>AI is analyzing the privacy policy...</span></div>';

    try {
        const response = await fetch(`${API_URL}/api/companies/${currentCompany.id}/analyze-privacy`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Privacy policy analysis failed');

        const updatedCompany = await response.json();

        // Update local data
        const index = companies.findIndex(c => c.id === currentCompany.id);
        if (index !== -1) {
            companies[index] = updatedCompany;
        }

        // Refresh the modal
        showCompanyDetails(currentCompany.id);
        switchDocumentTab('privacy');

    } catch (error) {
        console.error('Error analyzing privacy policy:', error);
        risksList.innerHTML = '<p class="no-risks" style="color: #f44336;">Analysis failed. Please try again.</p>';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Analyze Privacy Policy';
    }
}

// ==================== Chat Widget ====================

let chatHistory = [];
let selectedChatCompanyId = null;

function toggleChat() {
    const chatPanel = document.getElementById('chatPanel');
    const chatToggle = document.getElementById('chatToggle');

    if (chatPanel.style.display === 'none') {
        chatPanel.style.display = 'flex';
        chatToggle.classList.add('active');
        updateChatCompanyFilter();
        document.getElementById('chatInput').focus();
    } else {
        chatPanel.style.display = 'none';
        chatToggle.classList.remove('active');
    }
}

function updateChatCompanyFilter() {
    const select = document.getElementById('chatCompanyFilter');
    const currentValue = select.value;

    select.innerHTML = '<option value="">All Companies</option>';

    companies.forEach(company => {
        const option = document.createElement('option');
        option.value = company.id;
        option.textContent = company.name;
        select.appendChild(option);
    });

    // Restore previous selection if it still exists
    if (currentValue && companies.find(c => c.id === currentValue)) {
        select.value = currentValue;
    }
}

function updateChatFilter() {
    selectedChatCompanyId = document.getElementById('chatCompanyFilter').value || null;
}

function handleChatKeypress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    const typingId = showTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: message,
                company_id: selectedChatCompanyId,
                history: chatHistory.slice(-10) // Send last 10 messages for context
            })
        });

        if (!response.ok) {
            throw new Error('Chat request failed');
        }

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add assistant response
        addChatMessage(data.response, 'assistant');

        // Show sources if available
        if (data.sources && data.sources.length > 0) {
            showChatSources(data.sources);
        } else {
            hideChatSources();
        }

        // Update history
        chatHistory.push({ role: 'user', content: message });
        chatHistory.push({ role: 'assistant', content: data.response });

    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator(typingId);
        addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    }
}

function addChatMessage(content, role) {
    const messagesContainer = document.getElementById('chatMessages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatMessages');
    const id = 'typing-' + Date.now();

    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'chat-message assistant typing';
    typingDiv.innerHTML = `
        <div class="message-content">
            <span class="typing-dots">
                <span></span><span></span><span></span>
            </span>
        </div>
    `;

    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return id;
}

function removeTypingIndicator(id) {
    const typing = document.getElementById(id);
    if (typing) {
        typing.remove();
    }
}

function showChatSources(sources) {
    const sourcesDiv = document.getElementById('chatSources');
    const sourcesList = document.getElementById('sourcesList');

    sourcesList.innerHTML = sources.map(source =>
        `<span class="source-chip" onclick="showCompanyDetails('${source.company_id}')">${source.company_name}</span>`
    ).join('');

    sourcesDiv.style.display = 'flex';
}

function hideChatSources() {
    document.getElementById('chatSources').style.display = 'none';
}
