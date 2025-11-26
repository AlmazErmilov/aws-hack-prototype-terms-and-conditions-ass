const API_URL = '';

let companies = [];
let currentCompany = null;
let inputMode = 'paste'; // 'paste' or 'url'
let policyInputMode = 'paste'; // for policy upload modal
let currentPolicyTab = 'terms';

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

    // Close modals
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', () => {
            companyModal.style.display = 'none';
            addModal.style.display = 'none';
        });
    });

    // Click outside modal to close
    const uploadPolicyModal = document.getElementById('uploadPolicyModal');
    window.addEventListener('click', (e) => {
        if (e.target === companyModal) companyModal.style.display = 'none';
        if (e.target === addModal) addModal.style.display = 'none';
        if (e.target === uploadPolicyModal) uploadPolicyModal.style.display = 'none';
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

function populateTermsTab() {
    document.getElementById('modalSummary').textContent = currentCompany.terms_summary || 'No summary available. Click "Analyze with AI" to generate one.';

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
        document.getElementById('cookieSummary').textContent = currentCompany.cookie_summary || 'No summary available. Click "Re-analyze" to generate one.';
        
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
        document.getElementById('privacySummary').textContent = currentCompany.privacy_summary || 'No summary available. Click "Re-analyze" to generate one.';
        
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
    const termsText = document.getElementById('termsText').value;
    const termsUrl = document.getElementById('termsUrl').value;

    // Validation
    if (inputMode === 'paste' && !termsText.trim()) {
        alert('Please paste the terms and conditions text.');
        return;
    }
    if (inputMode === 'url' && !termsUrl.trim()) {
        alert('Please enter the URL for the terms and conditions.');
        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = inputMode === 'url' ? 'Fetching & Analyzing...' : 'Analyzing...';

    // Build request body based on input mode
    const requestBody = {
        company_name: name,
        category: category
    };

    if (inputMode === 'paste') {
        requestBody.terms_text = termsText;
    } else {
        requestBody.terms_url = termsUrl;
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
        document.getElementById('addCompanyForm').reset();
        document.getElementById('termsUrl').value = '';
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
