document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeApp();
});

function initializeApp() {
    // Set user name (could be retrieved from localStorage or API)
    setUserName();

    // Load placeholder content
    loadCalendar();
    loadTaxRates();
    loadComplianceStatus();
    loadNewsUpdates();
    loadWebinars();
    
    // Set up event listeners
    setupEventListeners();
    
    // Check for saved theme preference
    checkThemePreference();
}

function setUserName() {
    // This would typically come from a user authentication system
    // For now, we'll use a placeholder or retrieve from localStorage
    const userName = localStorage.getItem('userName') || 'User';
    document.getElementById('userName').textContent = userName;
}

function setupEventListeners() {
    // Dark mode toggle
    const darkModeToggle = document.querySelector('.dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
    
    // Mobile menu toggle (add if not in HTML)
    const menuToggle = document.querySelector('.menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', toggleMobileMenu);
    }
    
    // Modal open buttons
    const calculatorButtons = document.querySelectorAll('.calculator .btn-primary');
    calculatorButtons.forEach(button => {
        button.addEventListener('click', openCalculatorModal);
    });
    
    // Modal close button
    const closeModalButton = document.querySelector('.close-modal');
    if (closeModalButton) {
        closeModalButton.addEventListener('click', closeModal);
    }
    
    // Close modal if clicked outside the modal content
    const modalContainer = document.querySelector('.modal-container');
    if (modalContainer) {
        modalContainer.addEventListener('click', function(event) {
            if (event.target === modalContainer) {
                closeModal();
            }
        });
    }
    
    // Setup other interactive buttons
    setupQuickActionButtons();
    setupAIFeatureButtons();
}

function toggleDarkMode() {
    const body = document.body;
    
    // Toggle the data-theme attribute
    if (body.getAttribute('data-theme') === 'dark') {
        body.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        document.querySelector('.dark-mode-toggle i').className = 'fas fa-moon';
    } else {
        body.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        document.querySelector('.dark-mode-toggle i').className = 'fas fa-sun';
    }
}

function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
}

function openCalculatorModal(event) {
    const calculatorId = event.currentTarget.closest('.calculator').id;
    const modal = document.getElementById('calculatorModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    
    // Set modal title and content based on which calculator was clicked
    switch(calculatorId) {
        case 'income-tax-calc':
            modalTitle.textContent = 'Income Tax Calculator';
            loadIncomeTaxCalculator(modalContent);
            break;
        case 'business-tax-calc':
            modalTitle.textContent = 'Business Tax Estimator';
            loadBusinessTaxCalculator(modalContent);
            break;
        case 'vat-calc':
            modalTitle.textContent = 'VAT & Sales Tax Calculator';
            loadVATCalculator(modalContent);
            break;
        case 'withholding-tax-calc':
            modalTitle.textContent = 'Withholding Tax Estimator';
            loadWithholdingTaxCalculator(modalContent);
            break;
        default:
            modalTitle.textContent = 'Calculator';
            modalContent.innerHTML = '<p>Calculator content not available.</p>';
    }
    
    // Show the modal
    modal.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('calculatorModal');
    modal.classList.remove('active');
}

// Calendar data loading
function loadCalendar() {
    const calendarElement = document.querySelector('.calendar-view');
    if (!calendarElement) return;
    
    // Sample tax deadlines
    const taxDeadlines = [
        { date: '2025-03-31', title: 'End of FY 2024-25' },
        { date: '2025-04-15', title: 'Income Tax Filing Due' },
        { date: '2025-05-15', title: 'Quarterly VAT Return' },
        { date: '2025-06-30', title: 'Corporate Tax Filing Due' }
    ];
    
    // Calculate days until each deadline
    const today = new Date();
    const deadlinesWithDaysLeft = taxDeadlines.map(deadline => {
        const deadlineDate = new Date(deadline.date);
        const timeDiff = deadlineDate.getTime() - today.getTime();
        const daysLeft = Math.ceil(timeDiff / (1000 * 3600 * 24));
        return {
            ...deadline,
            daysLeft: daysLeft
        };
    });
    
    // Sort by days left and filter only upcoming deadlines
    const upcomingDeadlines = deadlinesWithDaysLeft
        .filter(deadline => deadline.daysLeft > 0)
        .sort((a, b) => a.daysLeft - b.daysLeft)
        .slice(0, 3); // Show top 3 upcoming deadlines
    
    if (upcomingDeadlines.length === 0) {
        calendarElement.innerHTML = '<p>No upcoming tax deadlines.</p>';
        return;
    }
    
    // Create HTML for the deadlines
    let calendarHTML = '<ul class="deadline-list">';
    
    upcomingDeadlines.forEach(deadline => {
        const deadlineDate = new Date(deadline.date);
        const formattedDate = deadlineDate.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });
        
        let urgencyClass = 'deadline-normal';
        if (deadline.daysLeft <= 7) {
            urgencyClass = 'deadline-urgent';
        } else if (deadline.daysLeft <= 30) {
            urgencyClass = 'deadline-warning';
        }
        
        calendarHTML += `
            <li class="deadline-item ${urgencyClass}">
                <div class="deadline-date">${formattedDate}</div>
                <div class="deadline-title">${deadline.title}</div>
                <div class="deadline-countdown">${deadline.daysLeft} days left</div>
            </li>
        `;
    });
    
    calendarHTML += '</ul>';
    calendarElement.innerHTML = calendarHTML;
}

// Tax rates data loading
function loadTaxRates() {
    const taxRatesElement = document.querySelector('.tax-rates');
    if (!taxRatesElement) return;
    
    // Sample tax rates data
    const taxRates = [
        { category: 'Income Tax', rate: '10-30%', notes: 'Progressive rates' },
        { category: 'VAT', rate: '16%', notes: 'Standard rate for goods & services' },
        { category: 'Corporate Tax', rate: '30%', notes: 'For resident companies' },
        { category: 'Withholding Tax', rate: '5-15%', notes: 'Varies by payment type' }
    ];
    
    // Create HTML for the tax rates
    let taxRatesHTML = '<table class="tax-rates-table">';
    taxRatesHTML += `
        <thead>
            <tr>
                <th>Category</th>
                <th>Rate</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    taxRates.forEach(tax => {
        taxRatesHTML += `
            <tr>
                <td>${tax.category}</td>
                <td>${tax.rate}</td>
                <td>${tax.notes}</td>
            </tr>
        `;
    });
    
    taxRatesHTML += '</tbody></table>';
    taxRatesElement.innerHTML = taxRatesHTML;
}

// Compliance status loading
function loadComplianceStatus() {
    const complianceMeterElement = document.querySelector('.compliance-meter');
    if (!complianceMeterElement) return;
    
    // Sample compliance data - in a real app, this would come from a user's actual financial data
    const complianceScore = 85; // percentage
    let complianceStatus = 'Good';
    let statusClass = 'status-good';
    
    if (complianceScore < 50) {
        complianceStatus = 'At Risk';
        statusClass = 'status-risk';
    } else if (complianceScore < 80) {
        complianceStatus = 'Needs Attention';
        statusClass = 'status-warning';
    }
    
    // Create HTML for the compliance meter
    let complianceHTML = `
        <div class="compliance-score-container">
            <div class="compliance-score-label">Compliance Score</div>
            <div class="compliance-score">${complianceScore}%</div>
            <div class="compliance-meter-bar">
                <div class="compliance-meter-fill" style="width: ${complianceScore}%"></div>
            </div>
            <div class="compliance-status ${statusClass}">Status: ${complianceStatus}</div>
        </div>
        <div class="compliance-details">
            <p>Last updated: ${new Date().toLocaleDateString()}</p>
            <p>Based on your recent financial activity and filing status.</p>
        </div>
    `;
    
    complianceMeterElement.innerHTML = complianceHTML;
}

// News updates loading
function loadNewsUpdates() {
    const newsFeedElement = document.querySelector('.news-feed');
    if (!newsFeedElement) return;
    
    // Sample news data
    const newsUpdates = [
        {
            title: 'New Tax Relief Measures Announced',
            date: '2025-02-28',
            summary: 'Government announces new tax relief measures for small businesses.'
        },
        {
            title: 'Digital Service Tax Implementation',
            date: '2025-02-15',
            summary: 'New digital service tax to be implemented from April 1, 2025.'
        },
        {
            title: 'Tax Filing Deadline Extended',
            date: '2025-01-30',
            summary: 'The deadline for annual tax returns has been extended by one month.'
        }
    ];
    
    // Create HTML for the news feed
    let newsHTML = '<ul class="news-list">';
    
    newsUpdates.forEach(news => {
        const newsDate = new Date(news.date);
        const formattedDate = newsDate.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
        });
        
        newsHTML += `
            <li class="news-item">
                <div class="news-date">${formattedDate}</div>
                <div class="news-content">
                    <h4 class="news-title">${news.title}</h4>
                    <p class="news-summary">${news.summary}</p>
                </div>
            </li>
        `;
    });
    
    newsHTML += '</ul>';
    newsFeedElement.innerHTML = newsHTML;
}

// Webinars loading
function loadWebinars() {
    const webinarListElement = document.querySelector('.webinar-list');
    if (!webinarListElement) return;
    
    // Sample webinar data
    const webinars = [
        {
            title: 'Understanding Tax Deductions for Entrepreneurs',
            date: '2025-03-15T14:00:00',
            duration: '60', // minutes
            presenter: 'Jane Smith, CPA'
        },
        {
            title: 'Digital Taxation in the Modern Economy',
            date: '2025-03-22T10:00:00',
            duration: '90', // minutes
            presenter: 'John Doe, Tax Consultant'
        }
    ];
    
    // Create HTML for the webinar list
    let webinarHTML = '<ul class="webinar-list">';
    
    webinars.forEach(webinar => {
        const webinarDate = new Date(webinar.date);
        const formattedDate = webinarDate.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });
        const formattedTime = webinarDate.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        webinarHTML += `
            <li class="webinar-item">
                <div class="webinar-details">
                    <h4 class="webinar-title">${webinar.title}</h4>
                    <p class="webinar-datetime">
                        <i class="far fa-calendar-alt"></i> ${formattedDate} at ${formattedTime}
                    </p>
                    <p class="webinar-duration">
                        <i class="far fa-clock"></i> ${webinar.duration} minutes
                    </p>
                    <p class="webinar-presenter">
                        <i class="far fa-user"></i> ${webinar.presenter}
                    </p>
                </div>
                <button class="btn-secondary webinar-register-btn">Register</button>
            </li>
        `;
    });
    
    webinarHTML += '</ul>';
    webinarListElement.innerHTML = webinarHTML;
    
    // Add event listeners to register buttons
    const registerButtons = webinarListElement.querySelectorAll('.webinar-register-btn');
    registerButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Registration logic would go here
            alert('Registration form will open.');
            // In a real app, this would open a registration form or modal
        });
    });
}

// Calculator form loaders
function loadIncomeTaxCalculator(container) {
    container.innerHTML = `
        <form id="incomeTaxForm" class="calculator-form">
            <div class="form-group">
                <label for="annualIncome">Annual Income (KES)</label>
                <input type="number" id="annualIncome" name="annualIncome" min="0" step="1000" required>
            </div>
            
            <div class="form-group">
                <label for="allowableDeductions">Allowable Deductions (KES)</label>
                <input type="number" id="allowableDeductions" name="allowableDeductions" min="0" step="1000" value="0">
            </div>
            
            <div class="form-group">
                <label for="nhifContributions">NHIF Contributions (KES)</label>
                <input type="number" id="nhifContributions" name="nhifContributions" min="0" step="100" value="0">
            </div>
            
            <div class="form-group">
                <label for="nssfContributions">NSSF Contributions (KES)</label>
                <input type="number" id="nssfContributions" name="nssfContributions" min="0" step="100" value="0">
            </div>
            
            <div class="form-group">
                <label for="insurancePremiums">Life Insurance Premiums (KES)</label>
                <input type="number" id="insurancePremiums" name="insurancePremiums" min="0" step="1000" value="0">
            </div>
            
            <div class="form-group">
                <label for="homeLoanInterest">Home Loan Interest (KES)</label>
                <input type="number" id="homeLoanInterest" name="homeLoanInterest" min="0" step="1000" value="0">
            </div>
            
            <button type="button" class="btn-primary calculate-btn" onclick="calculateIncomeTax()">Calculate Tax</button>
        </form>
        
        <div id="taxResults" class="tax-results"></div>
    `;
}

function loadBusinessTaxCalculator(container) {
    container.innerHTML = `
        <form id="businessTaxForm" class="calculator-form">
            <div class="form-group">
                <label for="businessIncome">Annual Business Income (KES)</label>
                <input type="number" id="businessIncome" name="businessIncome" min="0" step="1000" required>
            </div>
            
            <div class="form-group">
                <label for="businessExpenses">Business Expenses (KES)</label>
                <input type="number" id="businessExpenses" name="businessExpenses" min="0" step="1000" value="0">
            </div>
            
            <div class="form-group">
                <label for="capitalAllowances">Capital Allowances (KES)</label>
                <input type="number" id="capitalAllowances" name="capitalAllowances" min="0" step="1000" value="0">
            </div>
            
            <div class="form-group">
                <label for="businessType">Business Type</label>
                <select id="businessType" name="businessType">
                    <option value="sole">Sole Proprietorship</option>
                    <option value="partnership">Partnership</option>
                    <option value="limited">Limited Company</option>
                </select>
            </div>
            
            <button type="button" class="btn-primary calculate-btn" onclick="calculateBusinessTax()">Calculate Tax</button>
        </form>
        
        <div id="businessTaxResults" class="tax-results"></div>
    `;
}

function loadVATCalculator(container) {
    container.innerHTML = `
        <form id="vatForm" class="calculator-form">
            <div class="form-group">
                <label for="purchaseAmount">Purchase Amount (KES)</label>
                <input type="number" id="purchaseAmount" name="purchaseAmount" min="0" step="1" required>
            </div>
            
            <div class="form-group">
                <label for="vatRate">VAT Rate (%)</label>
                <select id="vatRate" name="vatRate">
                    <option value="16">Standard Rate (16%)</option>
                    <option value="8">Reduced Rate (8%)</option>
                    <option value="0">Zero Rated (0%)</option>
                </select>
            </div>
            
            <div class="radio-group">
                <span class="radio-label">Price includes VAT?</span>
                <div class="radio-options">
                    <label>
                        <input type="radio" name="vatIncluded" value="yes" checked> Yes
                    </label>
                    <label>
                        <input type="radio" name="vatIncluded" value="no"> No
                    </label>
                </div>
            </div>
            
            <button type="button" class="btn-primary calculate-btn" onclick="calculateVAT()">Calculate VAT</button>
        </form>
        
        <div id="vatResults" class="tax-results"></div>
    `;
}

function loadWithholdingTaxCalculator(container) {
    container.innerHTML = `
        <form id="withholdingTaxForm" class="calculator-form">
            <div class="form-group">
                <label for="paymentType">Payment Type</label>
                <select id="paymentType" name="paymentType">
                    <option value="dividends">Dividends</option>
                    <option value="interest">Interest</option>
                    <option value="royalties">Royalties</option>
                    <option value="professional">Professional/Management Fees</option>
                    <option value="rent">Rent - Immovable Property</option>
                    <option value="contractual">Contractual Fee</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="paymentAmount">Payment Amount (KES)</label>
                <input type="number" id="paymentAmount" name="paymentAmount" min="0" step="1" required>
            </div>
            
            <div class="form-group">
                <label for="recipientType">Recipient Type</label>
                <select id="recipientType" name="recipientType">
                    <option value="resident">Resident</option>
                    <option value="non-resident">Non-Resident</option>
                </select>
            </div>
            
            <button type="button" class="btn-primary calculate-btn" onclick="calculateWithholdingTax()">Calculate Tax</button>
        </form>
        
        <div id="withholdingTaxResults" class="tax-results"></div>
    `;
}

// Calculator logic functions
function calculateIncomeTax() {
    // Get values from form
    const annualIncome = parseFloat(document.getElementById('annualIncome').value) || 0;
    const allowableDeductions = parseFloat(document.getElementById('allowableDeductions').value) || 0;
    const nhifContributions = parseFloat(document.getElementById('nhifContributions').value) || 0;
    const nssfContributions = parseFloat(document.getElementById('nssfContributions').value) || 0;
    const insurancePremiums = parseFloat(document.getElementById('insurancePremiums').value) || 0;
    const homeLoanInterest = parseFloat(document.getElementById('homeLoanInterest').value) || 0;
    
    // Calculate taxable income
    const totalDeductions = allowableDeductions + nhifContributions + nssfContributions + 
                            insurancePremiums + homeLoanInterest;
    const taxableIncome = Math.max(0, annualIncome - totalDeductions);
    
    // Sample progressive tax rates (these should be updated with current rates)
    let incomeTax = 0;
    
    // First 288,000 KES (24,000 per month * 12)
    if (taxableIncome <= 288000) {
        incomeTax = taxableIncome * 0.1;
    } else {
        incomeTax = 288000 * 0.1;
        
        // Next 100,000 KES
        if (taxableIncome <= 388000) {
            incomeTax += (taxableIncome - 288000) * 0.25;
        } else {
            incomeTax += 100000 * 0.25;
            
            // Over 388,000 KES
            incomeTax += (taxableIncome - 388000) * 0.3;
        }
    }
    
    // Apply personal relief (if applicable)
    const personalRelief = 28800; // 2400 per month * 12
    const finalTax = Math.max(0, incomeTax - personalRelief);
    
    // Display results
    const resultsDiv = document.getElementById('taxResults');
    resultsDiv.innerHTML = `
        <h3>Tax Calculation Results</h3>
        <table class="tax-results-table">
            <tr>
                <td>Annual Income:</td>
                <td>KES ${annualIncome.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Total Deductions:</td>
                <td>KES ${totalDeductions.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Taxable Income:</td>
                <td>KES ${taxableIncome.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Gross Tax:</td>
                <td>KES ${incomeTax.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Personal Relief:</td>
                <td>KES ${personalRelief.toLocaleString()}</td>
            </tr>
            <tr class="tax-payable">
                <td>Final Tax Payable:</td>
                <td>KES ${finalTax.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Monthly PAYE:</td>
                <td>KES ${(finalTax / 12).toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
            </tr>
            <tr>
                <td>Effective Tax Rate:</td>
                <td>${((finalTax / annualIncome) * 100).toFixed(2)}%</td>
            </tr>
        </table>
        
        <div class="tax-summary">
            <p>Based on the current tax brackets and rates for the fiscal year 2024-2025.</p>
            <p>This is an estimate. Consult with a tax professional for detailed advice.</p>
        </div>
    `;
}

function calculateBusinessTax() {
    // Get values from form
    const businessIncome = parseFloat(document.getElementById('businessIncome').value) || 0;
    const businessExpenses = parseFloat(document.getElementById('businessExpenses').value) || 0;
    const capitalAllowances = parseFloat(document.getElementById('capitalAllowances').value) || 0;
    const businessType = document.getElementById('businessType').value;
    
    // Calculate taxable profit
    const totalDeductions = businessExpenses + capitalAllowances;
    const taxableProfit = Math.max(0, businessIncome - totalDeductions);
    
    let taxRate = 0.3; // 30% corporate tax rate
    let taxName = "Corporate Tax";
    
    // Adjust tax rate based on business type
    if (businessType === 'sole' || businessType === 'partnership') {
        // Use personal income tax rate for sole proprietorships and partnerships
        taxRate = 0.3; // Simplified to 30% for this example
        taxName = "Income Tax";
    }
    
    const taxPayable = taxableProfit * taxRate;
    
    // Display results
    const resultsDiv = document.getElementById('businessTaxResults');
    resultsDiv.innerHTML = `
        <h3>Business Tax Calculation Results</h3>
        <table class="tax-results-table">
            <tr>
                <td>Business Income:</td>
                <td>KES ${businessIncome.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Business Expenses:</td>
                <td>KES ${businessExpenses.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Capital Allowances:</td>
                <td>KES ${capitalAllowances.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Taxable Profit:</td>
                <td>KES ${taxableProfit.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Tax Rate:</td>
                <td>${(taxRate * 100).toFixed(0)}%</td>
            </tr>
            <tr class="tax-payable">
                <td>${taxName} Payable:</td>
                <td>KES ${taxPayable.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Net Profit After Tax:</td>
                <td>KES ${(taxableProfit - taxPayable).toLocaleString()}</td>
            </tr>
            <tr>
                <td>Effective Tax Rate:</td>
                <td>${((taxPayable / businessIncome) * 100).toFixed(2)}%</td>
            </tr>
        </table>
        
        <div class="tax-summary">
            <p>Based on the current tax rates for the fiscal year 2024-2025.</p>
            <p>This is an estimate. Consult with a tax professional for detailed advice.</p>
        </div>
    `;
}

function calculateVAT() {
    // Get values from form
    const purchaseAmount = parseFloat(document.getElementById('purchaseAmount').value) || 0;
    const vatRate = parseFloat(document.getElementById('vatRate').value) || 16;
    const vatIncluded = document.querySelector('input[name="vatIncluded"]:checked').value === 'yes';
    
    let netAmount, vatAmount, grossAmount;
    
    if (vatIncluded) {
        // VAT already included in the price
        grossAmount = purchaseAmount;
        netAmount = grossAmount / (1 + (vatRate / 100));
        vatAmount = grossAmount - netAmount;
    } else {
        // VAT not included in the price
        netAmount = purchaseAmount;
        vatAmount = netAmount * (vatRate / 100);
        grossAmount = netAmount + vatAmount;
    }
    
    // Display results
    const resultsDiv = document.getElementById('vatResults');
    resultsDiv.innerHTML = `
        <h3>VAT Calculation Results</h3>
        <table class="tax-results-table">
            <tr>
                <td>Net Amount (Excl. VAT):</td>
                <td>KES ${netAmount.toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
            </tr>
            <tr>
                <td>VAT (${vatRate}%):</td>
                <td>KES ${vatAmount.toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
            </tr>
            <tr class="tax-payable">
                <td>Gross Amount (Incl. VAT):</td>
                <td>KES ${grossAmount.toLocaleString(undefined, {maximumFractionDigits: 2})}</td>
            </tr>
        </table>
    `;
}

function calculateWithholdingTax() {
    // Get values from form
    const paymentType = document.getElementById('paymentType').value;
    const paymentAmount = parseFloat(document.getElementById('paymentAmount').value) || 0;
    const recipientType = document.getElementById('recipientType').value;
    
    // Withholding tax rates based on payment type and recipient type
    const taxRates = {
        dividends: { resident: 0.05, 'non-resident': 0.15 },
        interest: { resident: 0.15, 'non-resident': 0.15 },
        royalties: { resident: 0.05, 'non-resident': 0.20 },
        professional: { resident: 0.05, 'non-resident': 0.20 },
        rent: { resident: 0.10, 'non-resident': 0.30 },
        contractual: { resident: 0.03, 'non-resident': 0.20 }
    };
    
    const taxRate = taxRates[paymentType][recipientType];
    const withholdingTaxAmount = paymentAmount * taxRate;
    const netPayment = paymentAmount - withholdingTaxAmount;
    
    // Display results
    const resultsDiv = document.getElementById('withholdingTaxResults');
    resultsDiv.innerHTML = `
        <h3>Withholding Tax Calculation Results</h3>
        <table class="tax-results-table">
            <tr>
                <td>Gross Payment:</td>
                <td>KES ${paymentAmount.toLocaleString()}</td>
            </tr>
            <tr>
                <td>Withholding Tax Rate:</td>
                <td>${(taxRate * 100).toFixed(0)}%</td>
            </tr>
            <tr>
                <td>Withholding Tax Amount:</td>
                <td>KES ${withholdingTaxAmount.toLocaleString()}</td>
            </tr>
            <tr class="tax-payable">
                <td>Net Payment (After Tax):</td>
                <td>KES ${netPayment.toLocaleString()}</td>
            </tr>
        </table>
        
        <div class="tax-summary">
            <p>As a payer, you should remit KES ${withholdingTaxAmount.toLocaleString()} to the tax authority.</p>
            <p>The recipient will receive KES ${netPayment.toLocaleString()} after tax deduction.</p>
        </div>
    `;
}

// AI feature buttons functionality
function setupAIFeatureButtons() {
    // Tax Deduction Optimizer
    const taxOptimizerBtn = document.querySelector('#tax-optimizer .btn-ai');
    if (taxOptimizerBtn) {
        taxOptimizerBtn.addEventListener('click', showTaxOptimizationTips);
    }
    
    // Compliance Status Check
    const complianceStatusBtn = document.querySelector('#compliance-status .btn-ai');
    if (complianceStatusBtn) {
        complianceStatusBtn.addEventListener('click', checkComplianceStatus);
    }
    
    // Tax Refund Estimator
    const refundEstimatorBtn = document.querySelector('#refund-estimator .btn-ai');
    if (refundEstimatorBtn) {
        refundEstimatorBtn.addEventListener('click', estimateTaxRefund);
    }
}

function showTaxOptimizationTips() {
    // In a real app, this would analyze the user's financial data
    // and provide personalized tax-saving recommendations
    alert('AI Tax Optimization Tips: Based on your profile, consider maximizing retirement contributions, documenting business expenses, and exploring available tax credits.');
}

function checkComplianceStatus() {
    // In a real app, this would analyze the user's tax filing history
    // and provide a detailed compliance status report
    alert('Compliance Status Check: Your tax compliance status is currently Good. All filings are up to date, and you have no outstanding tax liabilities.');
}

function estimateTaxRefund() {
    // In a real app, this would analyze the user's tax payments and deductions
    // to estimate potential refund
    alert('Tax Refund Estimation: Based on your current withholding and estimated deductions, you may be eligible for a refund of approximately KES 12,500.');
}

// Quick action buttons functionality
function setupQuickActionButtons() {
    // Set Tax Filing Reminders
    const remindersBtn = document.getElementById('reminders');
    if (remindersBtn) {
        remindersBtn.addEventListener('click', setTaxReminders);
    }
    
    // Download Tax Reports
    const downloadReportsBtn = document.getElementById('download-reports');
    if (downloadReportsBtn) {
        downloadReportsBtn.addEventListener('click', downloadTaxReports);
    }
    
    // Compare Tax Brackets
    const compareBracketsBtn = document.getElementById('compare-brackets');
    if (compareBracketsBtn) {
        compareBracketsBtn.addEventListener('click', compareTaxBrackets);
    }
    
    // Get Expert Tax Help
    const expertHelpBtn = document.getElementById('expert-help');
    if (expertHelpBtn) {
        expertHelpBtn.addEventListener('click', getTaxHelp);
    }
}

function setTaxReminders() {
    // In a real app, this would open a calendar integration or a form to set reminders
    alert('Tax Filing Reminder: You can now set up notifications for upcoming tax deadlines.');
}

function downloadTaxReports() {
    // In a real app, this would generate and download tax reports
    alert('Tax Reports: Downloading your annual tax summary report.');
}

function compareTaxBrackets() {
    // In a real app, this would show a comparison of tax brackets
    alert('Tax Bracket Comparison: Showing current tax bracket rates compared to previous years.');
}

function getTaxHelp() {
    // In a real app, this would connect to a tax advisor or show contact information
    alert('Tax Advisory Help: Connecting you with a tax professional. Please check your email for further instructions.');
}

// Check for saved theme preference when the page loads
function checkThemePreference() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        document.querySelector('.dark-mode-toggle i').className = 'fas fa-sun';
    }
}

// Add mobile menu toggle button if it doesn't exist in HTML
function createMobileMenuToggle() {
    if (!document.querySelector('.menu-toggle') && window.innerWidth <= 992) {
        const topBar = document.querySelector('.top-bar');
        const userControls = document.querySelector('.user-controls');
        
        if (topBar && userControls) {
            const menuToggle = document.createElement('button');
            menuToggle.className = 'menu-toggle';
            menuToggle.setAttribute('aria-label', 'Toggle navigation menu');
            menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
            
            topBar.insertBefore(menuToggle, userControls);
            
            menuToggle.addEventListener('click', toggleMobileMenu);
        }
    }
}

// Add necessary CSS for the elements created dynamically
function addDynamicStyles() {
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        /* Styles for compliance meter */
        .compliance-score-container {
            text-align: center;
            margin-bottom: var(--spacing-md);
        }
        
        .compliance-score {
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary-color);
            margin: var(--spacing-sm) 0;
        }
        
        .compliance-meter-bar {
            height: 20px;
            background-color: var(--border-color);
            border-radius: var(--border-radius-sm);
            overflow: hidden;
            margin: var(--spacing-md) 0;
        }
        
        .compliance-meter-fill {
            height: 100%;
            background-color: var(--success-color);
            transition: width 0.5s ease;
        }
        
        .compliance-status {
            display: inline-block;
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: var(--border-radius-sm);
            font-weight: 500;
        }
        
        .status-good {
            background-color: var(--success-color);
            color: white;
        }
        
        .status-warning {
            background-color: var(--warning-color);
            color: white;
        }
        
        .status-risk {
            background-color: var(--danger-color);
            color: white;
        }
        
        /* Styles for deadline list */
        .deadline-list {
            list-style: none;
            padding: 0;
        }
        
        .deadline-item {
            border-left: 4px solid var(--info-color);
            padding: var(--spacing-sm) var(--spacing-md);
            margin-bottom: var(--spacing-sm);
            background-color: var(--card-bg-color);
        }
        
        .deadline-urgent {
            border-left-color: var(--danger-color);
        }
        
        .deadline-warning {
            border-left-color: var(--warning-color);
        }
        
        .deadline-date {
            font-weight: 500;
        }
        
        .deadline-countdown {
            color: var(--text-light);
            font-size: var(--font-size-sm);
        }
        
        /* Styles for news list */
        .news-list {
            list-style: none;
            padding: 0;
        }
        
        .news-item {
            display: flex;
            margin-bottom: var(--spacing-md);
            padding-bottom: var(--spacing-md);
            border-bottom: 1px solid var(--border-color);
        }
        
        .news-date {
            min-width: 60px;
            color: var(--text-light);
        }
        
        .news-title {
            margin-bottom: var(--spacing-xs);
        }
        
        .news-summary {
            color: var(--text-light);
            font-size: var(--font-size-sm);
        }
        
        /* Styles for webinar list */
        .webinar-item {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: var(--spacing-md);
            margin-bottom: var(--spacing-md);
            background-color: var(--card-bg-color);
            border-radius: var(--border-radius-sm);
            box-shadow: var(--shadow-sm);
        }
        
        .webinar-title {
            margin-bottom: var(--spacing-sm);
        }
        
        .webinar-datetime, .webinar-duration, .webinar-presenter {
            color: var(--text-light);
            font-size: var(--font-size-sm);
            margin-bottom: var(--spacing-xs);
        }
        
        /* Styles for calculator forms */
        .calculator-form {
            margin-bottom: var(--spacing-lg);
        }
        
        .form-group {
            margin-bottom: var(--spacing-md);
        }
        
        .form-group label {
            display: block;
            margin-bottom: var(--spacing-xs);
            font-weight: 500;
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: var(--spacing-sm) var(--spacing-md);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius-sm);
            font-size: var(--font-size-md);
        }
        
        .radio-group {
            margin-bottom: var(--spacing-md);
        }
        
        .radio-label {
            display: block;
            margin-bottom: var(--spacing-xs);
            font-weight: 500;
        }
        
        .radio-options {
            display: flex;
            gap: var(--spacing-md);
        }
        
        /* Styles for tax results */
        .tax-results {
            background-color: var(--background-color);
            padding: var(--spacing-md);
            border-radius: var(--border-radius-sm);
            margin-top: var(--spacing-lg);
        }
        
        .tax-results h3 {
            margin-bottom: var(--spacing-md);
        }
        
        .tax-results-table {
            width: 100%;
            margin-bottom: var(--spacing-md);
        }
        
        .tax-results-table td {
            padding: var(--spacing-sm) 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .tax-results-table td:first-child {
            font-weight: 500;
        }
        
        .tax-results-table td:last-child {
            text-align: right;
        }
        
        .tax-payable td {
            font-weight: 700;
            color: var(--primary-color);
        }
        
        .tax-summary {
            color: var(--text-light);
            font-size: var(--font-size-sm);
            font-style: italic;
        }
    `;
    
    document.head.appendChild(styleElement);
}

// Initialize mobile menu toggle on window resize
window.addEventListener('resize', function() {
    if (window.innerWidth <= 992) {
        createMobileMenuToggle();
    }
});

// Add additional initialization tasks
document.addEventListener('DOMContentLoaded', function() {
    createMobileMenuToggle();
    addDynamicStyles();
});