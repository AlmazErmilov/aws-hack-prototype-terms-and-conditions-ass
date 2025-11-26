const API_URL = '';

let companies = [];
let currentCompany = null;
let inputMode = 'paste'; // 'paste' or 'url' for terms in add modal
let policyInputMode = 'paste'; // for policy upload modal
let currentPolicyTab = 'terms';
let addCookieInputMode = 'paste'; // for cookie in add modal
let addPrivacyInputMode = 'paste'; // for privacy in add modal

// DOM Elements
const companiesGrid = document.getElementById('companiesGrid');
const loading = document.getElementById('loading');
const emptyState = document.getElementById('emptyState');
const companyModal = document.getElementById('companyModal');
const addModal = document.getElementById('addModal');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCompanies();
    setupEventListeners();
});

function setupEventListeners() {
    // Seed button
    document.getElementById('seedBtn').addEventListener('click', seedDatabase);

    // Add company button
    document.getElementById('addCompanyBtn').addEventListener('click', () => {
        addModal.style.display = 'block';
    });

    // Analytics button
    document.getElementById('analyticsBtn').addEventListener('click', openAnalyticsModal);

    // Close modals
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', () => {
            companyModal.style.display = 'none';
            addModal.style.display = 'none';
        });
    });

    // Click outside modal to close
    const uploadPolicyModal = document.getElementById('uploadPolicyModal');
    const analyticsModal = document.getElementById('analyticsModal');
    window.addEventListener('click', (e) => {
        if (e.target === companyModal) companyModal.style.display = 'none';
        if (e.target === addModal) addModal.style.display = 'none';
        if (e.target === uploadPolicyModal) uploadPolicyModal.style.display = 'none';
        if (e.target === analyticsModal) closeAnalyticsModal();
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
    
    // Toggle cookie text visibility
    document.getElementById('toggleCookieBtn').addEventListener('click', toggleCookieText);
    
    // Toggle privacy text visibility
    document.getElementById('togglePrivacyBtn').addEventListener('click', togglePrivacyText);
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
        // Combine risks from all three policy types
        const termsRisks = company.terms_risks || [];
        const cookieRisks = company.cookie_risks || [];
        const privacyRisks = company.privacy_risks || [];
        const allRisks = [...termsRisks, ...cookieRisks, ...privacyRisks];
        
        const riskCounts = {
            high: allRisks.filter(r => r.severity === 'high').length,
            medium: allRisks.filter(r => r.severity === 'medium').length,
            low: allRisks.filter(r => r.severity === 'low').length
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
    
    // Populate Terms tab
    populateTermsTab();
    
    // Populate Cookie tab
    populateCookieTab();
    
    // Populate Privacy tab
    populatePrivacyTab();
    
    // Update tab badges
    updateTabBadges();
    
    // Reset to terms tab
    switchPolicyTab('terms');

    companyModal.style.display = 'block';
}

// Helper function to render markdown content
function renderMarkdown(content) {
    if (typeof marked !== 'undefined' && content) {
        return marked.parse(content);
    }
    return content || '';
}

function populateTermsTab() {
    const summaryEl = document.getElementById('modalSummary');
    const summaryContent = currentCompany.terms_summary || 'No summary available. Click "Analyze with AI" to generate one.';
    summaryEl.innerHTML = renderMarkdown(summaryContent);

    const risksList = document.getElementById('risksList');
    const risks = currentCompany.terms_risks || [];

    if (risks.length === 0) {
        risksList.innerHTML = '<p class="no-risks">No risks analyzed yet. Click "Analyze with AI" to identify privacy risks.</p>';
    } else {
        risksList.innerHTML = renderRisksList(risks);
    }

    // Populate and reset terms section
    document.getElementById('originalTerms').textContent = currentCompany.terms_text || 'No terms text available.';
    document.getElementById('termsContent').style.display = 'none';
    document.getElementById('toggleTermsBtn').classList.remove('active');
}

function populateCookieTab() {
    const hasCookiePolicy = currentCompany.cookie_text && currentCompany.cookie_text.trim();
    
    document.getElementById('cookiePolicyEmpty').style.display = hasCookiePolicy ? 'none' : 'block';
    document.getElementById('cookiePolicyData').style.display = hasCookiePolicy ? 'block' : 'none';
    
    if (hasCookiePolicy) {
        const cookieSummaryEl = document.getElementById('cookieSummary');
        const cookieSummaryContent = currentCompany.cookie_summary || 'No summary available. Click "Re-analyze" to generate one.';
        cookieSummaryEl.innerHTML = renderMarkdown(cookieSummaryContent);
        
        const cookieRisksList = document.getElementById('cookieRisksList');
        const cookieRisks = currentCompany.cookie_risks || [];
        
        if (cookieRisks.length === 0) {
            cookieRisksList.innerHTML = '<p class="no-risks">No cookie risks analyzed yet.</p>';
        } else {
            cookieRisksList.innerHTML = renderRisksList(cookieRisks);
        }
        
        document.getElementById('originalCookieText').textContent = currentCompany.cookie_text;
        document.getElementById('cookieTextContent').style.display = 'none';
        document.getElementById('toggleCookieBtn').classList.remove('active');
    }
}

function populatePrivacyTab() {
    const hasPrivacyPolicy = currentCompany.privacy_text && currentCompany.privacy_text.trim();
    
    document.getElementById('privacyPolicyEmpty').style.display = hasPrivacyPolicy ? 'none' : 'block';
    document.getElementById('privacyPolicyData').style.display = hasPrivacyPolicy ? 'block' : 'none';
    
    if (hasPrivacyPolicy) {
        const privacySummaryEl = document.getElementById('privacySummary');
        const privacySummaryContent = currentCompany.privacy_summary || 'No summary available. Click "Re-analyze" to generate one.';
        privacySummaryEl.innerHTML = renderMarkdown(privacySummaryContent);
        
        const privacyRisksList = document.getElementById('privacyRisksList');
        const privacyRisks = currentCompany.privacy_risks || [];
        
        if (privacyRisks.length === 0) {
            privacyRisksList.innerHTML = '<p class="no-risks">No privacy risks analyzed yet.</p>';
        } else {
            privacyRisksList.innerHTML = renderRisksList(privacyRisks);
        }
        
        document.getElementById('originalPrivacyText').textContent = currentCompany.privacy_text;
        document.getElementById('privacyTextContent').style.display = 'none';
        document.getElementById('togglePrivacyBtn').classList.remove('active');
    }
}

function renderRisksList(risks) {
    return risks.map(risk => `
        <div class="risk-item ${risk.severity}">
            <h4>
                ${risk.title}
                <span class="severity-badge ${risk.severity}">${risk.severity}</span>
            </h4>
            <p>${risk.description}</p>
        </div>
    `).join('');
}

function updateTabBadges() {
    const termsRisks = currentCompany.terms_risks || [];
    const cookieRisks = currentCompany.cookie_risks || [];
    const privacyRisks = currentCompany.privacy_risks || [];
    
    updateBadge('termsRiskCount', termsRisks.length);
    updateBadge('cookieRiskCount', cookieRisks.length);
    updateBadge('privacyRiskCount', privacyRisks.length);
}

function updateBadge(elementId, count) {
    const badge = document.getElementById(elementId);
    if (count > 0) {
        badge.textContent = count;
        badge.classList.add('has-risks');
    } else {
        badge.textContent = '';
        badge.classList.remove('has-risks');
    }
}

function switchPolicyTab(tabName) {
    currentPolicyTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.policy-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update tab contents
    document.querySelectorAll('.policy-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}TabContent`).classList.add('active');
}

function toggleTerms() {
    togglePolicyText('toggleTermsBtn', 'termsContent');
}

function toggleCookieText() {
    togglePolicyText('toggleCookieBtn', 'cookieTextContent');
}

function togglePrivacyText() {
    togglePolicyText('togglePrivacyBtn', 'privacyTextContent');
}

function togglePolicyText(btnId, contentId) {
    const btn = document.getElementById(btnId);
    const content = document.getElementById(contentId);

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
    const pasteGroup = document.getElementById('pasteGroup');
    const urlGroup = document.getElementById('urlGroup');

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

function setAddCookieInputMode(mode) {
    addCookieInputMode = mode;
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

function setAddPrivacyInputMode(mode) {
    addPrivacyInputMode = mode;
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

function toggleAddPolicySection(policyType) {
    const body = document.getElementById(`${policyType}PolicyBody`);
    const icon = document.getElementById(`${policyType}ToggleIcon`);

    if (body.classList.contains('collapsed')) {
        body.classList.remove('collapsed');
        icon.textContent = '−';
    } else {
        body.classList.add('collapsed');
        icon.textContent = '+';
    }
}

function resetAddCompanyForm() {
    document.getElementById('addCompanyForm').reset();
    document.getElementById('termsUrl').value = '';
    document.getElementById('addCookieUrl').value = '';
    document.getElementById('addPrivacyUrl').value = '';

    // Reset input modes
    setInputMode('paste');
    setAddCookieInputMode('paste');
    setAddPrivacyInputMode('paste');

    // Reset policy sections - terms open, others collapsed
    document.getElementById('termsPolicyBody').classList.remove('collapsed');
    document.getElementById('termsToggleIcon').textContent = '−';
    document.getElementById('cookiePolicyBody').classList.add('collapsed');
    document.getElementById('cookieToggleIcon').textContent = '+';
    document.getElementById('privacyPolicyBody').classList.add('collapsed');
    document.getElementById('privacyToggleIcon').textContent = '+';
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

async function handleAddCompany(e) {
    e.preventDefault();

    const name = document.getElementById('companyName').value;
    const category = document.getElementById('companyCategory').value;

    // Terms data
    const termsText = document.getElementById('termsText').value;
    const termsUrl = document.getElementById('termsUrl').value;

    // Cookie data
    const cookieText = document.getElementById('addCookieText').value;
    const cookieUrl = document.getElementById('addCookieUrl').value;

    // Privacy data
    const privacyText = document.getElementById('addPrivacyText').value;
    const privacyUrl = document.getElementById('addPrivacyUrl').value;

    // Validation - Terms is required
    if (inputMode === 'paste' && !termsText.trim()) {
        alert('Please paste the terms and conditions text.');
        return;
    }
    if (inputMode === 'url' && !termsUrl.trim()) {
        alert('Please enter the URL for the terms and conditions.');
        return;
    }

    const submitBtn = document.getElementById('addCompanySubmitBtn');
    submitBtn.disabled = true;

    // Determine loading message based on what's being processed
    const hasMultiplePolicies = (cookieText.trim() || cookieUrl.trim() || privacyText.trim() || privacyUrl.trim());
    submitBtn.textContent = hasMultiplePolicies ? 'Analyzing policies...' : 'Analyzing...';

    // Build request body
    const requestBody = {
        company_name: name,
        category: category
    };

    // Add terms
    if (inputMode === 'paste') {
        requestBody.terms_text = termsText;
    } else {
        requestBody.terms_url = termsUrl;
    }

    // Add cookie policy if provided
    if (addCookieInputMode === 'paste' && cookieText.trim()) {
        requestBody.cookie_text = cookieText;
    } else if (addCookieInputMode === 'url' && cookieUrl.trim()) {
        requestBody.cookie_url = cookieUrl;
    }

    // Add privacy policy if provided
    if (addPrivacyInputMode === 'paste' && privacyText.trim()) {
        requestBody.privacy_text = privacyText;
    } else if (addPrivacyInputMode === 'url' && privacyUrl.trim()) {
        requestBody.privacy_url = privacyUrl;
    }

    try {
        const response = await fetch(`${API_URL}/api/companies`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.detail || 'Failed to add company');
        }

        addModal.style.display = 'none';
        resetAddCompanyForm();
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

// ==================== Policy Upload Functions ====================

function showUploadPolicyModal(policyType) {
    document.getElementById('policyType').value = policyType;
    
    const titles = {
        'cookie': 'Upload Cookie Policy',
        'privacy': 'Upload Privacy Policy'
    };
    document.getElementById('uploadPolicyTitle').textContent = titles[policyType] || 'Upload Policy';
    
    // Reset form
    document.getElementById('uploadPolicyForm').reset();
    setPolicyInputMode('paste');
    
    document.getElementById('uploadPolicyModal').style.display = 'block';
}

function closeUploadPolicyModal() {
    document.getElementById('uploadPolicyModal').style.display = 'none';
}

function setPolicyInputMode(mode) {
    policyInputMode = mode;
    const pasteBtn = document.getElementById('policyTogglePaste');
    const urlBtn = document.getElementById('policyToggleUrl');
    const pasteGroup = document.getElementById('policyPasteGroup');
    const urlGroup = document.getElementById('policyUrlGroup');

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

async function handleUploadPolicy(e) {
    e.preventDefault();
    
    if (!currentCompany) return;
    
    const policyType = document.getElementById('policyType').value;
    const policyText = document.getElementById('policyText').value;
    const policyUrl = document.getElementById('policyUrl').value;
    
    // Validation
    if (policyInputMode === 'paste' && !policyText.trim()) {
        alert('Please paste the policy text.');
        return;
    }
    if (policyInputMode === 'url' && !policyUrl.trim()) {
        alert('Please enter the URL for the policy.');
        return;
    }
    
    const submitBtn = document.getElementById('uploadPolicySubmitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = policyInputMode === 'url' ? 'Fetching & Analyzing...' : 'Analyzing...';
    
    // Build request body based on policy type
    const requestBody = {};
    if (policyInputMode === 'paste') {
        requestBody[`${policyType}_text`] = policyText;
    } else {
        requestBody[`${policyType}_url`] = policyUrl;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/companies/${currentCompany.id}/${policyType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData.detail || 'Failed to upload policy');
        }
        
        // Update local data
        const index = companies.findIndex(c => c.id === currentCompany.id);
        if (index !== -1) {
            companies[index] = responseData;
            currentCompany = responseData;
        }
        
        closeUploadPolicyModal();
        
        // Refresh the modal content
        if (policyType === 'cookie') {
            populateCookieTab();
        } else if (policyType === 'privacy') {
            populatePrivacyTab();
        }
        updateTabBadges();
        
    } catch (error) {
        console.error('Error uploading policy:', error);
        alert(error.message || 'Error uploading policy. Please try again.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Upload & Analyze';
    }
}

async function analyzeCookiePolicy() {
    if (!currentCompany) return;
    
    const cookieRisksList = document.getElementById('cookieRisksList');
    cookieRisksList.innerHTML = '<div class="analyzing"><div class="spinner"></div><span>AI is analyzing the cookie policy...</span></div>';
    
    try {
        const response = await fetch(`${API_URL}/api/companies/${currentCompany.id}/analyze-cookie`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const updatedCompany = await response.json();
        
        // Update local data
        const index = companies.findIndex(c => c.id === currentCompany.id);
        if (index !== -1) {
            companies[index] = updatedCompany;
            currentCompany = updatedCompany;
        }
        
        // Refresh the cookie tab
        populateCookieTab();
        updateTabBadges();
        
    } catch (error) {
        console.error('Error analyzing cookie policy:', error);
        cookieRisksList.innerHTML = '<p class="no-risks" style="color: #f44336;">Analysis failed. Please try again.</p>';
    }
}

async function analyzePrivacyPolicy() {
    if (!currentCompany) return;
    
    const privacyRisksList = document.getElementById('privacyRisksList');
    privacyRisksList.innerHTML = '<div class="analyzing"><div class="spinner"></div><span>AI is analyzing the privacy policy...</span></div>';
    
    try {
        const response = await fetch(`${API_URL}/api/companies/${currentCompany.id}/analyze-privacy`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const updatedCompany = await response.json();
        
        // Update local data
        const index = companies.findIndex(c => c.id === currentCompany.id);
        if (index !== -1) {
            companies[index] = updatedCompany;
            currentCompany = updatedCompany;
        }
        
        // Refresh the privacy tab
        populatePrivacyTab();
        updateTabBadges();
        
    } catch (error) {
        console.error('Error analyzing privacy policy:', error);
        privacyRisksList.innerHTML = '<p class="no-risks" style="color: #f44336;">Analysis failed. Please try again.</p>';
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

    // Render markdown for assistant messages, plain text for user
    if (role === 'assistant' && typeof marked !== 'undefined') {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }

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

    sourcesList.innerHTML = sources.map(source => {
        const policyLabel = source.policy_label || 'Terms & Conditions';
        const policyIcon = source.policy_type === 'cookie' ? '🍪' : 
                          source.policy_type === 'privacy' ? '🔒' : '📄';
        return `<span class="source-chip" onclick="showCompanyDetails('${source.company_id}')" title="${policyLabel}">${policyIcon} ${source.company_name}</span>`;
    }).join('');

    sourcesDiv.style.display = 'flex';
}

function hideChatSources() {
    document.getElementById('chatSources').style.display = 'none';
}

// ==================== Analytics Dashboard ====================

let analyticsCharts = {
    severity: null,
    companyRisks: null,
    policyType: null,
    severityByCompany: null,
    category: null
};

const chartColors = {
    high: '#f44336',
    medium: '#ff9800',
    low: '#4CAF50',
    terms: '#667eea',
    cookie: '#ff9800',
    privacy: '#9c27b0',
    gradient: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'],
    blueGradient: ['#0d47a1', '#1565c0', '#1976d2', '#1e88e5', '#2196f3', '#42a5f5', '#64b5f6', '#90caf9'],
    orangeGradient: ['#e65100', '#ef6c00', '#f57c00', '#fb8c00', '#ff9800', '#ffa726', '#ffb74d', '#ffcc80']
};

function openAnalyticsModal() {
    const modal = document.getElementById('analyticsModal');
    modal.style.display = 'block';

    if (companies.length === 0) {
        document.querySelector('.analytics-grid').style.display = 'none';
        document.getElementById('analyticsEmpty').style.display = 'block';
        return;
    }

    document.querySelector('.analytics-grid').style.display = 'grid';
    document.getElementById('analyticsEmpty').style.display = 'none';
    renderAnalytics();
}

function closeAnalyticsModal() {
    document.getElementById('analyticsModal').style.display = 'none';
    Object.values(analyticsCharts).forEach(chart => {
        if (chart) chart.destroy();
    });
    analyticsCharts = { severity: null, companyRisks: null, policyType: null, severityByCompany: null, category: null };
}

function processAnalyticsData() {
    const data = {
        totalCompanies: companies.length,
        totalRisks: 0, highRisks: 0, mediumRisks: 0, lowRisks: 0,
        termsRisks: 0, cookieRisks: 0, privacyRisks: 0,
        byCompany: [], byCategory: {}
    };

    companies.forEach(company => {
        const terms = company.terms_risks || [];
        const cookie = company.cookie_risks || [];
        const privacy = company.privacy_risks || [];
        const allRisks = [...terms, ...cookie, ...privacy];

        const companyData = {
            name: company.name, category: company.category, total: allRisks.length,
            high: allRisks.filter(r => r.severity === 'high').length,
            medium: allRisks.filter(r => r.severity === 'medium').length,
            low: allRisks.filter(r => r.severity === 'low').length,
            terms: terms.length, cookie: cookie.length, privacy: privacy.length
        };

        data.totalRisks += companyData.total;
        data.highRisks += companyData.high;
        data.mediumRisks += companyData.medium;
        data.lowRisks += companyData.low;
        data.termsRisks += companyData.terms;
        data.cookieRisks += companyData.cookie;
        data.privacyRisks += companyData.privacy;
        data.byCompany.push(companyData);

        if (!data.byCategory[company.category]) {
            data.byCategory[company.category] = { total: 0, companies: 0 };
        }
        data.byCategory[company.category].total += companyData.total;
        data.byCategory[company.category].companies += 1;
    });

    data.byCompany.sort((a, b) => b.total - a.total);
    return data;
}

function renderAnalytics() {
    const data = processAnalyticsData();

    document.getElementById('totalCompanies').textContent = data.totalCompanies;
    document.getElementById('totalRisks').textContent = data.totalRisks;
    document.getElementById('highRisks').textContent = data.highRisks;
    document.getElementById('mediumRisks').textContent = data.mediumRisks;
    document.getElementById('lowRisks').textContent = data.lowRisks;
    document.getElementById('avgRisks').textContent = data.totalCompanies > 0
        ? (data.totalRisks / data.totalCompanies).toFixed(1) : '0';

    renderSeverityChart(data);
    renderCompanyRisksChart(data);
    renderPolicyTypeChart(data);
    renderSeverityByCompanyChart(data);
    renderCategoryChart(data);
    renderSeverityLegend(data);
}

function renderSeverityChart(data) {
    const ctx = document.getElementById('severityChart').getContext('2d');
    if (analyticsCharts.severity) analyticsCharts.severity.destroy();

    analyticsCharts.severity = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{ data: [data.highRisks, data.mediumRisks, data.lowRisks],
                backgroundColor: [chartColors.high, chartColors.medium, chartColors.low],
                borderWidth: 0, hoverOffset: 8 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '65%',
            plugins: { legend: { display: false },
                tooltip: { callbacks: { label: (ctx) => {
                    const pct = data.totalRisks > 0 ? ((ctx.raw / data.totalRisks) * 100).toFixed(1) : 0;
                    return `${ctx.label}: ${ctx.raw} (${pct}%)`;
                }}}
            }
        }
    });
}

function renderSeverityLegend(data) {
    const legend = document.getElementById('severityLegend');
    const total = data.totalRisks;
    const items = [
        { label: 'High', count: data.highRisks, color: chartColors.high },
        { label: 'Medium', count: data.mediumRisks, color: chartColors.medium },
        { label: 'Low', count: data.lowRisks, color: chartColors.low }
    ];
    legend.innerHTML = items.map(item => {
        const pct = total > 0 ? ((item.count / total) * 100).toFixed(0) : 0;
        return `<div class="legend-item"><span class="legend-color" style="background: ${item.color}"></span><span>${item.label}: ${item.count} (${pct}%)</span></div>`;
    }).join('');
}

function renderCompanyRisksChart(data) {
    const ctx = document.getElementById('companyRisksChart').getContext('2d');
    if (analyticsCharts.companyRisks) analyticsCharts.companyRisks.destroy();
    const topCompanies = data.byCompany.slice(0, 8);

    analyticsCharts.companyRisks = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topCompanies.map(c => c.name),
            datasets: [{ data: topCompanies.map(c => c.total),
                backgroundColor: chartColors.orangeGradient.slice(0, topCompanies.length),
                borderRadius: 6, barThickness: 24 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, indexAxis: 'y',
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `Total risks: ${ctx.raw}` }}},
            scales: { x: { beginAtZero: true, grid: { display: false }, ticks: { stepSize: 1 }}, y: { grid: { display: false }}}
        }
    });
}

function renderPolicyTypeChart(data) {
    const ctx = document.getElementById('policyTypeChart').getContext('2d');
    if (analyticsCharts.policyType) analyticsCharts.policyType.destroy();

    analyticsCharts.policyType = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Terms & Conditions', 'Cookie Policy', 'Privacy Policy'],
            datasets: [{ data: [data.termsRisks, data.cookieRisks, data.privacyRisks],
                backgroundColor: chartColors.orangeGradient.slice(0, 3),
                borderWidth: 0, hoverOffset: 8 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '65%',
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 12, font: { size: 11 }}},
                tooltip: { callbacks: { label: (ctx) => {
                    const total = data.termsRisks + data.cookieRisks + data.privacyRisks;
                    const pct = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                    return `${ctx.label}: ${ctx.raw} (${pct}%)`;
                }}}
            }
        }
    });
}

function renderSeverityByCompanyChart(data) {
    const ctx = document.getElementById('severityByCompanyChart').getContext('2d');
    if (analyticsCharts.severityByCompany) analyticsCharts.severityByCompany.destroy();

    analyticsCharts.severityByCompany = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.byCompany.map(c => c.name),
            datasets: [
                { label: 'High', data: data.byCompany.map(c => c.high), backgroundColor: chartColors.high, borderRadius: 4 },
                { label: 'Medium', data: data.byCompany.map(c => c.medium), backgroundColor: chartColors.medium, borderRadius: 4 },
                { label: 'Low', data: data.byCompany.map(c => c.low), backgroundColor: chartColors.low, borderRadius: 4 }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'top', labels: { boxWidth: 12, padding: 16 }}},
            scales: { x: { stacked: true, grid: { display: false }}, y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1 }}}
        }
    });
}

function renderCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    if (analyticsCharts.category) analyticsCharts.category.destroy();

    const categories = Object.keys(data.byCategory);
    const categoryData = categories.map(cat => ({
        name: cat.charAt(0).toUpperCase() + cat.slice(1),
        avgRisks: data.byCategory[cat].companies > 0 ? (data.byCategory[cat].total / data.byCategory[cat].companies).toFixed(1) : 0
    })).sort((a, b) => b.avgRisks - a.avgRisks);

    analyticsCharts.category = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categoryData.map(c => c.name),
            datasets: [{ label: 'Avg Risks/Company', data: categoryData.map(c => parseFloat(c.avgRisks)),
                backgroundColor: chartColors.blueGradient.slice(0, categoryData.length), borderRadius: 6, barThickness: 28 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `Avg risks per company: ${ctx.raw}` }}},
            scales: { x: { grid: { display: false }}, y: { beginAtZero: true, grid: { color: '#f0f0f0' }}}
        }
    });
}
