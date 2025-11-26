const API_URL = '';

let companies = [];
let currentCompany = null;

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
    window.addEventListener('click', (e) => {
        if (e.target === companyModal) companyModal.style.display = 'none';
        if (e.target === addModal) addModal.style.display = 'none';
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
        const risks = company.risks || [];
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
    document.getElementById('modalSummary').textContent = currentCompany.summary || 'No summary available. Click "Analyze with AI" to generate one.';

    const risksList = document.getElementById('risksList');
    const risks = currentCompany.risks || [];

    if (risks.length === 0) {
        risksList.innerHTML = '<p class="no-risks">No risks analyzed yet. Click "Analyze with AI" to identify privacy risks.</p>';
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

    companyModal.style.display = 'block';
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

    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Analyzing...';

    try {
        const response = await fetch(`${API_URL}/api/companies`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: name,
                category: category,
                terms_text: termsText
            })
        });

        if (!response.ok) throw new Error('Failed to add company');

        addModal.style.display = 'none';
        document.getElementById('addCompanyForm').reset();
        await loadCompanies();

        // Show the newly added company
        const newCompany = await response.json();
        showCompanyDetails(newCompany.id);

    } catch (error) {
        console.error('Error adding company:', error);
        alert('Error adding company. Please try again.');
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
