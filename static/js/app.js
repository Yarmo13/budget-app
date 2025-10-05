// Global state
let currentBudgets = {};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    initializeTabs();
    initializeExpenseForm();
    initializeSavingsForm();
    initializeLogout();
    loadExpenses();
    setTodayDate();
});

// Check authentication
async function checkAuth() {
    try {
        const response = await fetch('/api/auth/me');
        const data = await response.json();

        if (data.logged_in) {
            document.getElementById('usernameDisplay').textContent = `Welcome, ${data.username}!`;
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login';
    }
}

// Logout functionality
function initializeLogout() {
    document.getElementById('logoutBtn').addEventListener('click', async () => {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            window.location.href = '/login';
        } catch (error) {
            console.error('Logout failed:', error);
        }
    });
}

// Tab navigation
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            // Remove active class from all tabs and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked tab and corresponding content
            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');

            // Load data for specific tabs
            if (targetTab === 'dashboard') {
                loadDashboard();
            } else if (targetTab === 'budget') {
                loadBudgetSetup();
            } else if (targetTab === 'savings') {
                loadSavings();
                initializeSavingsGoals();
                loadSavingsGoals();
            } else if (targetTab === 'reports') {
                loadAvailableMonths();
            } else if (targetTab === 'visualizations') {
                loadVisualizations();
            }
        });
    });
}

// Set today's date as default
function setTodayDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('expenseDate').value = today;
}

// Expense form handling
function initializeExpenseForm() {
    const form = document.getElementById('expenseForm');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const expense = {
            date: document.getElementById('expenseDate').value,
            category: document.getElementById('expenseCategory').value,
            amount: parseFloat(document.getElementById('expenseAmount').value),
            description: document.getElementById('expenseDescription').value
        };

        try {
            const response = await fetch('/api/expenses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(expense)
            });

            if (response.ok) {
                showNotification('Expense added successfully!', 'success');
                form.reset();
                setTodayDate();
                loadExpenses();
            } else {
                showNotification('Error adding expense', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error adding expense', 'error');
        }
    });

    // Filter buttons
    document.getElementById('filterBtn').addEventListener('click', loadExpenses);
    document.getElementById('clearFilterBtn').addEventListener('click', () => {
        document.getElementById('filterStartDate').value = '';
        document.getElementById('filterEndDate').value = '';
        loadExpenses();
    });
}

// Load expenses
async function loadExpenses() {
    const startDate = document.getElementById('filterStartDate').value;
    const endDate = document.getElementById('filterEndDate').value;

    let url = '/api/expenses';
    const params = new URLSearchParams();

    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    if (params.toString()) url += '?' + params.toString();

    try {
        const response = await fetch(url);
        const expenses = await response.json();

        const list = document.getElementById('expensesList');

        if (expenses.length === 0) {
            list.innerHTML = '<p class="no-data">No expenses found</p>';
            return;
        }

        list.innerHTML = expenses.map(exp => `
            <div class="expense-item">
                <div class="expense-info">
                    <div class="expense-date">${formatDate(exp.date)}</div>
                    <div class="expense-category">${exp.category}</div>
                    <div class="expense-description">${exp.description || '-'}</div>
                </div>
                <div class="expense-actions">
                    <div class="expense-amount">$${exp.amount.toFixed(2)}</div>
                    <button onclick="deleteExpense(${exp.id})" class="btn-delete">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading expenses:', error);
    }
}

// Delete expense
async function deleteExpense(id) {
    showConfirmModal(
        'Delete Expense?',
        'Are you sure you want to delete this expense? This action cannot be undone.',
        async () => {
            try {
                const response = await fetch(`/api/expenses/${id}`, { method: 'DELETE' });

                if (response.ok) {
                    showNotification('Expense deleted', 'success');
                    loadExpenses();
                } else {
                    showNotification('Error deleting expense', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('Error deleting expense', 'error');
            }
        }
    );
}

// Load dashboard
async function loadDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        const data = await response.json();

        document.getElementById('totalBudget').textContent = `$${data.total_budget.toFixed(2)}`;
        document.getElementById('totalSpent').textContent = `$${data.total_spent.toFixed(2)}`;
        document.getElementById('totalRemaining').textContent = `$${data.total_remaining.toFixed(2)}`;

        const progressContainer = document.getElementById('categoryProgress');

        if (data.categories.length === 0) {
            document.getElementById('noBudgetMessage').style.display = 'block';
            progressContainer.innerHTML = '';
            return;
        }

        document.getElementById('noBudgetMessage').style.display = 'none';

        progressContainer.innerHTML = data.categories.map(cat => `
            <div class="category-progress ${cat.status}">
                <div class="category-header">
                    <span class="category-name">${cat.category}</span>
                    <span class="category-amount">$${cat.spent.toFixed(2)} / $${cat.budget.toFixed(2)}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(cat.percentage, 100)}%"></div>
                </div>
                <div class="category-details">
                    <span>${cat.percentage.toFixed(1)}% used</span>
                    <span class="remaining">$${cat.remaining.toFixed(2)} remaining</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load budget setup
async function loadBudgetSetup() {
    // Load current budgets
    const budgetResponse = await fetch('/api/budgets');
    const budgets = await budgetResponse.json();
    currentBudgets = budgets;

    populateBudgetInputs(budgets);

    // Save budget button
    document.getElementById('saveBudgetBtn').onclick = saveBudget;
}

function populateBudgetInputs(budgets) {
    const categories = ['Groceries', 'Dining Out', 'Transportation', 'Gas', 'Entertainment', 'Utilities', 'Shopping', 'Healthcare', 'Housing', 'Insurance', 'Subscriptions', 'Other'];

    const inputs = categories.map(cat => `
        <div class="budget-input-group">
            <label for="budget_${cat}">${cat}:</label>
            <input type="number" id="budget_${cat}" step="0.01" min="0"
                   value="${budgets[cat] || 0}" placeholder="0.00">
        </div>
    `).join('');

    document.getElementById('budgetInputs').innerHTML = inputs;
}

async function saveBudget() {
    const categories = ['Groceries', 'Dining Out', 'Transportation', 'Gas', 'Entertainment', 'Utilities', 'Shopping', 'Healthcare', 'Housing', 'Insurance', 'Subscriptions', 'Other'];

    const budgets = {};
    categories.forEach(cat => {
        const value = parseFloat(document.getElementById(`budget_${cat}`).value) || 0;
        if (value > 0) {
            budgets[cat] = value;
        }
    });

    try {
        const response = await fetch('/api/budgets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(budgets)
        });

        if (response.ok) {
            showNotification('Budget saved successfully!', 'success');
            currentBudgets = budgets;
        } else {
            showNotification('Error saving budget', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error saving budget', 'error');
    }
}

// Visualizations
let monthlyTrendsChart, categoryBreakdownChart, budgetVsActualChart;

async function loadVisualizations() {
    await loadMonthlyTrends();
    await loadCategoryBreakdown();
    await loadBudgetVsActual();

    // Set up viz filter
    document.getElementById('vizFilterBtn').addEventListener('click', loadCategoryBreakdown);
}

async function loadMonthlyTrends() {
    try {
        const response = await fetch('/api/visualizations/monthly-trends');
        const data = await response.json();

        const ctx = document.getElementById('monthlyTrendsChart').getContext('2d');

        if (monthlyTrendsChart) monthlyTrendsChart.destroy();

        monthlyTrendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.month),
                datasets: [{
                    label: 'Monthly Spending',
                    data: data.map(d => d.total),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => '$' + value.toFixed(0)
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading monthly trends:', error);
    }
}

async function loadCategoryBreakdown() {
    const startDate = document.getElementById('vizStartDate').value;
    const endDate = document.getElementById('vizEndDate').value;

    let url = '/api/visualizations/category-breakdown';
    const params = new URLSearchParams();

    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    if (params.toString()) url += '?' + params.toString();

    try {
        const response = await fetch(url);
        const data = await response.json();

        const ctx = document.getElementById('categoryBreakdownChart').getContext('2d');

        if (categoryBreakdownChart) categoryBreakdownChart.destroy();

        const colors = [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
            '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
        ];

        categoryBreakdownChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.category),
                datasets: [{
                    data: data.map(d => d.total),
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'right' },
                    tooltip: {
                        callbacks: {
                            label: context => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: $${value.toFixed(2)}`;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading category breakdown:', error);
    }
}

async function loadBudgetVsActual() {
    try {
        const response = await fetch('/api/visualizations/budget-vs-actual');
        const data = await response.json();

        const ctx = document.getElementById('budgetVsActualChart').getContext('2d');

        if (budgetVsActualChart) budgetVsActualChart.destroy();

        budgetVsActualChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.category),
                datasets: [
                    {
                        label: 'Budget',
                        data: data.map(d => d.budget),
                        backgroundColor: '#10b981',
                    },
                    {
                        label: 'Actual',
                        data: data.map(d => d.actual),
                        backgroundColor: '#3b82f6',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: true }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => '$' + value.toFixed(0)
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading budget vs actual:', error);
    }
}

// Savings functionality
function initializeSavingsForm() {
    const form = document.getElementById('savingsForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = {
            date: document.getElementById('savingsDate').value,
            amount: document.getElementById('savingsAmount').value,
            description: document.getElementById('savingsDescription').value
        };

        try {
            const response = await fetch('/api/savings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                showNotification('Savings added successfully!', 'success');
                form.reset();
                setTodayDate();
                loadSavings();
            }
        } catch (error) {
            showNotification('Error adding savings', 'error');
        }
    });

    // Set today's date initially
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('savingsDate').value = today;
}

async function loadSavings() {
    try {
        const response = await fetch('/api/savings');
        const savings = await response.json();

        const savingsList = document.getElementById('savingsList');

        if (savings.length === 0) {
            savingsList.innerHTML = '<p class="no-data">No savings recorded yet</p>';
            return;
        }

        savingsList.innerHTML = savings.map(s => `
            <div class="expense-item">
                <div class="expense-info">
                    <div class="expense-category" style="background: linear-gradient(135deg, #10b981, #059669);">
                        💰 Savings
                    </div>
                    <div class="expense-details">
                        <div class="expense-date">${formatDate(s.date)}</div>
                        ${s.description ? `<div class="expense-description">${s.description}</div>` : ''}
                    </div>
                </div>
                <div class="expense-actions">
                    <div class="expense-amount">$${s.amount.toFixed(2)}</div>
                    <button class="btn-delete" onclick="deleteSaving(${s.id})">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading savings:', error);
    }
}

async function deleteSaving(id) {
    showConfirmModal(
        'Delete Savings?',
        'Are you sure you want to delete this savings entry? This action cannot be undone.',
        async () => {
            try {
                const response = await fetch(`/api/savings/${id}`, { method: 'DELETE' });
                if (response.ok) {
                    showNotification('Savings deleted', 'success');
                    loadSavings();
                }
            } catch (error) {
                showNotification('Error deleting savings', 'error');
            }
        }
    );
}

// Monthly Reports functionality
async function loadAvailableMonths() {
    try {
        const response = await fetch('/api/reports/available-months');
        const months = await response.json();

        const select = document.getElementById('reportMonthSelect');
        select.innerHTML = '<option value="">Select a month...</option>';

        months.reverse().forEach(month => {
            const option = document.createElement('option');
            option.value = month;
            const date = new Date(month + '-01');
            option.textContent = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
            select.appendChild(option);
        });

        select.addEventListener('change', (e) => {
            if (e.target.value) {
                loadMonthlyReport(e.target.value);
            } else {
                document.getElementById('reportContent').style.display = 'none';
            }
        });
    } catch (error) {
        console.error('Error loading available months:', error);
    }
}

async function loadMonthlyReport(yearMonth) {
    try {
        const response = await fetch(`/api/reports/monthly/${yearMonth}`);
        const report = await response.json();

        // Update summary
        const date = new Date(yearMonth + '-01');
        document.getElementById('reportMonth').textContent = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
        document.getElementById('reportTotalBudget').textContent = `$${report.total_budget.toFixed(2)}`;
        document.getElementById('reportTotalSpent').textContent = `$${report.total_spent.toFixed(2)}`;
        document.getElementById('reportTotalSaved').textContent = `$${report.total_saved.toFixed(2)}`;

        const diffElement = document.getElementById('reportDifference');
        diffElement.textContent = `$${Math.abs(report.total_difference).toFixed(2)}`;
        diffElement.className = 'stat-value ' + (report.total_difference >= 0 ? 'success' : 'danger');

        // Update categories
        const categoryList = document.getElementById('reportCategoryList');
        if (report.categories.length === 0) {
            categoryList.innerHTML = '<p class="no-data">No expense data for this month</p>';
        } else {
            categoryList.innerHTML = report.categories.map(cat => `
                <div class="report-category-item ${cat.status}">
                    <div class="report-category-header">
                        <span class="report-category-name">${cat.category}</span>
                        <span style="font-size: 0.9rem; color: var(--text-secondary);">
                            ${cat.transaction_count} transaction${cat.transaction_count !== 1 ? 's' : ''}
                        </span>
                    </div>
                    <div class="report-category-stats">
                        <div class="report-stat">
                            <span>Budget:</span>
                            <strong>$${cat.budget.toFixed(2)}</strong>
                        </div>
                        <div class="report-stat">
                            <span>Spent:</span>
                            <strong>$${cat.spent.toFixed(2)}</strong>
                        </div>
                        <div class="report-stat">
                            <span>${cat.difference >= 0 ? 'Under' : 'Over'}:</span>
                            <strong style="color: ${cat.difference >= 0 ? 'var(--success-color)' : 'var(--danger-color)'}">
                                $${Math.abs(cat.difference).toFixed(2)}
                            </strong>
                        </div>
                        <div class="report-stat">
                            <span>% of Budget:</span>
                            <strong>${cat.percentage.toFixed(1)}%</strong>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        document.getElementById('reportContent').style.display = 'block';
    } catch (error) {
        console.error('Error loading monthly report:', error);
        showNotification('Error loading report', 'error');
    }
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString + 'T00:00:00');
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('show');
    }, 100);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Custom Modal Functions
function showConfirmModal(title, message, onConfirm) {
    const modal = document.getElementById('confirmModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const confirmBtn = document.getElementById('confirmBtn');

    modalTitle.textContent = title;
    modalMessage.textContent = message;
    modal.classList.add('show');

    // Remove old event listeners
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    // Add new event listener
    document.getElementById('confirmBtn').onclick = () => {
        closeModal();
        onConfirm();
    };

    // Close on overlay click
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeModal();
        }
    };
}

function closeModal() {
    const modal = document.getElementById('confirmModal');
    modal.classList.remove('show');
}

// Savings Goals functionality
let showingArchivedGoals = false;
let savingsGoalsInitialized = false;

function initializeSavingsGoals() {
    if (savingsGoalsInitialized) return;

    const createBtn = document.getElementById('createGoalBtn');
    const toggleBtn = document.getElementById('toggleArchivedBtn');

    if (createBtn && toggleBtn) {
        createBtn.addEventListener('click', showCreateGoalModal);
        toggleBtn.addEventListener('click', toggleArchivedGoals);
        savingsGoalsInitialized = true;
    }
}

async function loadSavingsGoals() {
    try {
        const url = `/api/savings-goals?archived=${showingArchivedGoals}`;
        const response = await fetch(url);
        const goals = await response.json();

        const goalsList = document.getElementById('goalsList');

        if (goals.length === 0) {
            goalsList.innerHTML = `<p class="no-data">${showingArchivedGoals ? 'No archived goals' : 'No active goals. Create one to get started!'}</p>`;
            return;
        }

        goalsList.innerHTML = goals.map(goal => `
            <div class="savings-goal-item">
                <div class="goal-header">
                    <h3 class="goal-name">${goal.name}</h3>
                    <div class="goal-amount">$${goal.current_amount.toFixed(2)} / $${goal.target_amount.toFixed(2)}</div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${goal.progress_percentage}%; background: linear-gradient(135deg, #10b981, #059669);"></div>
                </div>
                <div class="goal-footer">
                    <span class="goal-percentage">${goal.progress_percentage}% complete</span>
                    ${!showingArchivedGoals ? `
                        <div class="goal-actions">
                            <button class="btn btn-secondary btn-sm" onclick="showAddToGoalModal(${goal.id}, '${goal.name}')">Add Money</button>
                            <button class="btn btn-secondary btn-sm" onclick="archiveGoal(${goal.id})">Archive</button>
                            <button class="btn-delete btn-sm" onclick="deleteGoal(${goal.id})">Delete</button>
                        </div>
                    ` : `
                        <div class="goal-actions">
                            <span class="goal-completed-date">Archived ${goal.completed_at ? formatDate(goal.completed_at.split('T')[0]) : ''}</span>
                        </div>
                    `}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading savings goals:', error);
    }
}

function toggleArchivedGoals() {
    showingArchivedGoals = !showingArchivedGoals;
    const btn = document.getElementById('toggleArchivedBtn');
    btn.textContent = showingArchivedGoals ? 'View Active Goals' : 'View Archived Goals';
    loadSavingsGoals();
}

function showCreateGoalModal() {
    const name = prompt('What are you saving for?');
    if (!name) return;

    const targetAmount = parseFloat(prompt('Target amount ($):'));
    if (!targetAmount || targetAmount <= 0) {
        showNotification('Please enter a valid target amount', 'error');
        return;
    }

    createSavingsGoal(name, targetAmount);
}

async function createSavingsGoal(name, targetAmount) {
    try {
        const response = await fetch('/api/savings-goals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, target_amount: targetAmount })
        });

        if (response.ok) {
            showNotification('Goal created successfully!', 'success');
            loadSavingsGoals();
        } else {
            showNotification('Error creating goal', 'error');
        }
    } catch (error) {
        console.error('Error creating goal:', error);
        showNotification('Error creating goal', 'error');
    }
}

function showAddToGoalModal(goalId, goalName) {
    const amount = parseFloat(prompt(`How much would you like to add to "${goalName}"?`));
    if (!amount || amount <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }

    addToGoal(goalId, amount);
}

async function addToGoal(goalId, amount) {
    try {
        const response = await fetch(`/api/savings-goals/${goalId}/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount })
        });

        const data = await response.json();

        if (data.success) {
            if (data.completed) {
                showNotification('🎉 Goal completed! Congratulations!', 'success');
            } else {
                showNotification('Amount added successfully!', 'success');
            }
            loadSavingsGoals();
        } else {
            showNotification(data.error || 'Error adding to goal', 'error');
        }
    } catch (error) {
        console.error('Error adding to goal:', error);
        showNotification('Error adding to goal', 'error');
    }
}

async function archiveGoal(goalId) {
    showConfirmModal(
        'Archive Goal?',
        'Are you sure you want to archive this goal? You can view it later in archived goals.',
        async () => {
            try {
                const response = await fetch(`/api/savings-goals/${goalId}/archive`, {
                    method: 'POST'
                });

                if (response.ok) {
                    showNotification('Goal archived', 'success');
                    loadSavingsGoals();
                } else {
                    showNotification('Error archiving goal', 'error');
                }
            } catch (error) {
                console.error('Error archiving goal:', error);
                showNotification('Error archiving goal', 'error');
            }
        }
    );
}

async function deleteGoal(goalId) {
    showConfirmModal(
        'Delete Goal?',
        'Are you sure you want to permanently delete this goal? This action cannot be undone.',
        async () => {
            try {
                const response = await fetch(`/api/savings-goals/${goalId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    showNotification('Goal deleted', 'success');
                    loadSavingsGoals();
                } else {
                    showNotification('Error deleting goal', 'error');
                }
            } catch (error) {
                console.error('Error deleting goal:', error);
                showNotification('Error deleting goal', 'error');
            }
        }
    );
}
