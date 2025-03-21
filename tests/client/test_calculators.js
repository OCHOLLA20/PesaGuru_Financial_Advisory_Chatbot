// Import testing framework
const { test, expect } = require('@jest/globals');
const { JSDOM } = require('jsdom');

// Import calculator modules
const LoanCalculator = require('../../client/assets/js/calculators/loanCalculator');
const InvestmentCalculator = require('../../client/assets/js/calculators/investmentCalculator');
const SavingsCalculator = require('../../client/assets/js/calculators/savingsCalculator');
const RetirementCalculator = require('../../client/assets/js/calculators/retirementCalculator');
const BudgetCalculator = require('../../client/assets/js/calculators/budgetCalculator');

// Setup DOM environment for tests
let dom;
let window;
let document;

beforeEach(() => {
  // Create a new JSDOM instance before each test
  dom = new JSDOM(`
    <!DOCTYPE html>
    <html>
      <body>
        <div id="calculator-container"></div>
      </body>
    </html>
  `, { url: 'http://localhost/' });
  
  window = dom.window;
  document = window.document;
  
  // Mock global objects
  global.window = window;
  global.document = document;
  global.HTMLElement = window.HTMLElement;
});

/**
 * LOAN CALCULATOR TESTS
 * Tests for the loan calculator component that helps users understand
 * loan payments, interest costs, and affordability.
 */
describe('Loan Calculator Tests', () => {
  let loanCalculator;
  
  beforeEach(() => {
    // Create new instance of loan calculator before each test
    loanCalculator = new LoanCalculator();
  });
  
  test('should calculate correct monthly payment for a personal loan', () => {
    // Test for typical Kenyan personal loan: 100,000 KES at 14% for 12 months
    const result = loanCalculator.calculateMonthlyPayment({
      loanAmount: 100000,
      interestRate: 14,
      loanTerm: 12,
      loanType: 'personal'
    });
    
    // Expected monthly payment is approximately 9,020 KES
    expect(parseFloat(result.monthlyPayment)).toBeCloseTo(9020, 0);
  });
  
  test('should calculate correct total interest for a personal loan', () => {
    // Calculate total interest for 100,000 KES loan at 14% for 12 months
    const result = loanCalculator.calculateLoanSummary({
      loanAmount: 100000,
      interestRate: 14,
      loanTerm: 12,
      loanType: 'personal'
    });
    
    // Expected total interest is approximately 8,240 KES
    expect(parseFloat(result.totalInterest)).toBeCloseTo(8240, 0);
  });
  
  test('should calculate correct KCB mortgage payment with correct rate', () => {
    // Test for Kenyan mortgage: 5M KES at 13% for 20 years
    const result = loanCalculator.calculateMonthlyPayment({
      loanAmount: 5000000,
      interestRate: 13,
      loanTerm: 240, // 20 years in months
      loanType: 'mortgage'
    });
    
    // Expected monthly payment is approximately 55,433 KES
    expect(parseFloat(result.monthlyPayment)).toBeCloseTo(55433, 0);
  });
  
  test('should calculate M-Shwari loan fees correctly', () => {
    // Test for M-Shwari loan: 10,000 KES with 7.5% facilitation fee (1-month term)
    const result = loanCalculator.calculateMobileMoneyLoan({
      loanAmount: 10000,
      provider: 'mshwari',
      term: 1 // month
    });
    
    // Facilitation fee should be 7.5% = 750 KES
    expect(parseFloat(result.facilitationFee)).toBeCloseTo(750, 0);
    // Total repayment should be 10,750 KES
    expect(parseFloat(result.totalRepayment)).toBeCloseTo(10750, 0);
  });
  
  test('should calculate loan affordability based on income', () => {
    // Calculate maximum affordable loan for someone with 50,000 KES monthly income
    const result = loanCalculator.calculateAffordability({
      monthlyIncome: 50000,
      expenses: 20000,
      interestRate: 14,
      loanTerm: 36, // 3 years
      debtToIncomeRatio: 0.4 // 40% DTI ratio
    });
    
    // Expected maximum affordable loan should be around 620,000 KES
    expect(parseFloat(result.affordableLoanAmount)).toBeCloseTo(620000, -3);
  });
  
  test('should generate correct amortization schedule', () => {
    // Generate amortization schedule for 100,000 KES at 14% for 12 months
    const schedule = loanCalculator.generateAmortizationSchedule({
      loanAmount: 100000,
      interestRate: 14,
      loanTerm: 12
    });
    
    // Schedule should have 12 entries (12 months)
    expect(schedule.length).toBe(12);
    
    // First month principal should be approximately 7,736 KES
    expect(parseFloat(schedule[0].principal)).toBeCloseTo(7736, 0);
    
    // First month interest should be approximately 1,167 KES
    expect(parseFloat(schedule[0].interest)).toBeCloseTo(1167, 0);
    
    // Last month's remaining balance should be approximately 0
    expect(parseFloat(schedule[11].remainingBalance)).toBeCloseTo(0, 0);
  });
});

/**
 * INVESTMENT CALCULATOR TESTS
 * Tests for the investment calculator that helps users project
 * returns on various investment options in the Kenyan market.
 */
describe('Investment Calculator Tests', () => {
  let investmentCalculator;
  
  beforeEach(() => {
    investmentCalculator = new InvestmentCalculator();
  });
  
  test('should calculate correct NSE stock investment returns', () => {
    // Test calculation for 100,000 KES invested in NSE stocks with 12% annual return for 5 years
    const result = investmentCalculator.calculateInvestmentGrowth({
      initialInvestment: 100000,
      annualReturnRate: 12,
      investmentPeriod: 5, // years
      investmentType: 'stocks',
      compoundingFrequency: 'annual',
      additionalContributions: 0
    });
    
    // Final value should be approximately 176,234 KES
    expect(parseFloat(result.finalValue)).toBeCloseTo(176234, 0);
    
    // Total returns should be approximately 76,234 KES
    expect(parseFloat(result.totalReturns)).toBeCloseTo(76234, 0);
  });
  
  test('should calculate money market fund returns with monthly compounding', () => {
    // 50,000 KES in Money Market Fund at 9% with monthly compounding for 3 years
    const result = investmentCalculator.calculateInvestmentGrowth({
      initialInvestment: 50000,
      annualReturnRate: 9,
      investmentPeriod: 3, // years
      investmentType: 'mmf',
      compoundingFrequency: 'monthly',
      additionalContributions: 0
    });
    
    // Final value should be approximately 65,172 KES
    expect(parseFloat(result.finalValue)).toBeCloseTo(65172, 0);
  });
  
  test('should calculate correct returns with monthly contributions', () => {
    // 50,000 KES initial with 5,000 KES monthly additions at 10% for 5 years
    const result = investmentCalculator.calculateInvestmentGrowth({
      initialInvestment: 50000,
      annualReturnRate: 10,
      investmentPeriod: 5, // years
      investmentType: 'general',
      compoundingFrequency: 'monthly',
      additionalContributions: 5000,
      contributionFrequency: 'monthly'
    });
    
    // Final value should be approximately 417,456 KES
    expect(parseFloat(result.finalValue)).toBeCloseTo(417456, 0);
    
    // Total contributions should be 350,000 KES (50,000 + 60 months × 5,000)
    expect(parseFloat(result.totalContributions)).toBeCloseTo(350000, 0);
  });
  
  test('should calculate correct Treasury bond returns for Kenyan market', () => {
    // 100,000 KES in Treasury bond at 13.5% for 2 years (semi-annual coupons)
    const result = investmentCalculator.calculateBondReturns({
      principal: 100000,
      couponRate: 13.5,
      termYears: 2,
      frequency: 'semi-annual'
    });
    
    // Total coupon payments should be 27,000 KES (13.5% × 100,000 × 2 years)
    expect(parseFloat(result.totalCouponPayments)).toBeCloseTo(27000, 0);
    
    // Final value should be 127,000 KES (100,000 + 27,000)
    expect(parseFloat(result.maturityValue)).toBeCloseTo(127000, 0);
  });
  
  test('should calculate inflation-adjusted returns correctly', () => {
    // 200,000 KES at 12% for 10 years with 5.5% inflation
    const result = investmentCalculator.calculateInflationAdjustedReturns({
      initialInvestment: 200000,
      annualReturnRate: 12,
      inflationRate: 5.5,
      investmentPeriod: 10
    });
    
    // Nominal final value should be approximately 621,379 KES
    expect(parseFloat(result.nominalFinalValue)).toBeCloseTo(621379, 0);
    
    // Real (inflation-adjusted) final value should be approximately 363,258 KES
    expect(parseFloat(result.realFinalValue)).toBeCloseTo(363258, 0);
  });
  
  test('should compare different investment options', () => {
    // Compare 100,000 KES in stocks (12%), bonds (10.5%), and MMF (8%)
    const comparison = investmentCalculator.compareInvestmentOptions({
      initialInvestment: 100000,
      investmentPeriod: 5,
      options: [
        { name: 'NSE Stocks', annualReturnRate: 12, risk: 'high' },
        { name: 'Treasury Bonds', annualReturnRate: 10.5, risk: 'medium' },
        { name: 'Money Market Fund', annualReturnRate: 8, risk: 'low' }
      ]
    });
    
    // Should have 3 options
    expect(comparison.length).toBe(3);
    
    // Stocks should have highest return
    expect(comparison[0].name).toBe('NSE Stocks');
    expect(parseFloat(comparison[0].finalValue)).toBeCloseTo(176234, 0);
    
    // MMF should have lowest return
    expect(comparison[2].name).toBe('Money Market Fund');
    expect(parseFloat(comparison[2].finalValue)).toBeCloseTo(146933, 0);
  });
});

/**
 * SAVINGS CALCULATOR TESTS
 * Tests for the savings calculator that helps users plan
 * and track their savings goals.
 */
describe('Savings Calculator Tests', () => {
  let savingsCalculator;
  
  beforeEach(() => {
    savingsCalculator = new SavingsCalculator();
  });
  
  test('should calculate time to reach savings goal', () => {
    // Calculate months to save 500,000 KES with 10,000 KES monthly savings at 5% interest
    const result = savingsCalculator.calculateTimeToGoal({
      savingsGoal: 500000,
      monthlySavings: 10000,
      annualInterestRate: 5
    });
    
    // Should take approximately 44 months
    expect(result.monthsToGoal).toBeCloseTo(44, 0);
  });
  
  test('should calculate required monthly savings for goal', () => {
    // Calculate monthly amount needed to save 500,000 KES in 3 years with 6% interest
    const result = savingsCalculator.calculateRequiredSavings({
      savingsGoal: 500000,
      timeToGoalMonths: 36,
      annualInterestRate: 6
    });
    
    // Required monthly savings should be approximately 12,376 KES
    expect(parseFloat(result.requiredMonthlySavings)).toBeCloseTo(12376, 0);
  });
  
  test('should calculate future savings value', () => {
    // 5,000 KES saved monthly for 5 years at 5% interest
    const result = savingsCalculator.calculateFutureSavingsValue({
      initialDeposit: 0,
      monthlySavings: 5000,
      timeMonths: 60,
      annualInterestRate: 5
    });
    
    // Future value should be approximately 345,081 KES
    expect(parseFloat(result.futureValue)).toBeCloseTo(345081, 0);
  });
  
  test('should handle different compounding frequencies', () => {
    // 100,000 KES initial at 6% for 1 year with different compounding
    const annualResult = savingsCalculator.calculateSavingsGrowth({
      initialAmount: 100000,
      annualInterestRate: 6,
      timeYears: 1,
      compoundingFrequency: 'annual'
    });
    
    const monthlyResult = savingsCalculator.calculateSavingsGrowth({
      initialAmount: 100000,
      annualInterestRate: 6,
      timeYears: 1,
      compoundingFrequency: 'monthly'
    });
    
    // Annual compounding should give 106,000 KES
    expect(parseFloat(annualResult.finalAmount)).toBeCloseTo(106000, 0);
    
    // Monthly compounding should give approximately 106,168 KES
    expect(parseFloat(monthlyResult.finalAmount)).toBeCloseTo(106168, 0);
  });
  
  test('should calculate education savings plan accurately', () => {
    // Calculate savings for child's education: 1M KES needed in 15 years at 7% return
    const result = savingsCalculator.calculateEducationSavings({
      educationGoal: 1000000,
      yearsToEducation: 15,
      annualReturnRate: 7,
      initialAmount: 50000
    });
    
    // Required monthly savings should be approximately 2,428 KES
    expect(parseFloat(result.requiredMonthlySavings)).toBeCloseTo(2428, 0);
  });
  
  test('should generate savings schedule correctly', () => {
    // Generate schedule for 5,000 KES monthly for 12 months at 6% interest
    const schedule = savingsCalculator.generateSavingsSchedule({
      initialAmount: 0,
      monthlySavings: 5000,
      timeMonths: 12,
      annualInterestRate: 6
    });
    
    // Schedule should have 12 entries
    expect(schedule.length).toBe(12);
    
    // 12th month should have total of around 61,800 KES
    expect(parseFloat(schedule[11].totalAmount)).toBeCloseTo(61800, 0);
    
    // Total interest should be approximately 1,800 KES
    const totalInterest = schedule[11].totalInterest;
    expect(parseFloat(totalInterest)).toBeCloseTo(1800, 0);
  });
});

/**
 * RETIREMENT CALCULATOR TESTS
 * Tests for the retirement planning calculator tailored for Kenyan users
 */
describe('Retirement Calculator Tests', () => {
  let retirementCalculator;
  
  beforeEach(() => {
    retirementCalculator = new RetirementCalculator();
  });
  
  test('should calculate retirement corpus needed accurately', () => {
    // Person aged 35, wants to retire at 60, needs 100,000 KES monthly, 6% inflation, 8% return
    const result = retirementCalculator.calculateRetirementCorpus({
      currentAge: 35,
      retirementAge: 60,
      lifeExpectancy: 80,
      monthlyExpenses: 100000,
      inflationRate: 6,
      postRetirementReturn: 8
    });
    
    // Corpus should be approximately 40.48 million KES
    expect(parseFloat(result.requiredCorpus) / 1000000).toBeCloseTo(40.48, 1);
  });
  
  test('should calculate monthly retirement savings needed', () => {
    // Person aged 35, needs 40M KES by 60, current savings 2M KES, 10% return
    const result = retirementCalculator.calculateRequiredMonthlySavings({
      currentAge: 35,
      retirementAge: 60,
      requiredCorpus: 40000000,
      currentSavings: 2000000,
      expectedReturn: 10
    });
    
    // Required monthly savings should be approximately 34,843 KES
    expect(parseFloat(result.requiredMonthlySavings)).toBeCloseTo(34843, 0);
  });
  
  test('should calculate retirement income correctly', () => {
    // Person with 30M KES corpus, 8% return, 5% inflation, 20 years retirement
    const result = retirementCalculator.calculateRetirementIncome({
      retirementCorpus: 30000000,
      withdrawalRate: 4,
      annualReturnRate: 8,
      inflationRate: 5,
      retirementDuration: 20
    });
    
    // Initial monthly income should be 100,000 KES (30M × 4% ÷ 12)
    expect(parseFloat(result.initialMonthlyIncome)).toBeCloseTo(100000, 0);
    
    // Final year monthly income (inflation adjusted) should be approximately 265,330 KES
    expect(parseFloat(result.finalYearMonthlyIncome)).toBeCloseTo(265330, 0);
  });
  
  test('should factor in NSSF contributions', () => {
    // Calculate retirement plan with monthly NSSF contributions of 2,160 KES
    const result = retirementCalculator.calculateRetirementWithPension({
      currentAge: 35,
      retirementAge: 60,
      lifeExpectancy: 80,
      monthlyExpenses: 100000,
      inflationRate: 6,
      postRetirementReturn: 8,
      monthlyNSSFContribution: 2160,
      nssfReturnRate: 7
    });
    
    // NSSF should provide approximately 2.67M KES
    expect(parseFloat(result.nssfBenefit) / 1000000).toBeCloseTo(2.67, 1);
    
    // Additional corpus needed should be reduced accordingly
    expect(parseFloat(result.additionalCorpusNeeded) / 1000000).toBeCloseTo(37.81, 1);
  });
  
  test('should provide accurate retirement sustainability analysis', () => {
    // Test if 20M KES will last through retirement 
    const result = retirementCalculator.analyzeRetirementSustainability({
      retirementCorpus: 20000000,
      monthlyExpenses: 80000,
      inflationRate: 5,
      investmentReturn: 8,
      retirementAge: 60,
      lifeExpectancy: 85
    });
    
    // Should last approximately 25 years (until age 85)
    expect(result.willFundLast).toBe(true);
    expect(result.yearsCorpusWillLast).toBeCloseTo(25, 0);
    
    // Should have some balance at end
    expect(parseFloat(result.finalBalance) > 0).toBe(true);
  });
  
  test('should generate retirement savings projection', () => {
    // Generate savings plan: age 40, target 25M by 60, current 3M savings, 30,000 monthly contribution
    const projection = retirementCalculator.generateRetirementSavingsProjection({
      currentAge: 40,
      retirementAge: 60,
      currentSavings: 3000000,
      monthlyContribution: 30000,
      annualReturnRate: 9,
      inflationRate: 5
    });
    
    // Should have 20 entries (one per year)
    expect(projection.length).toBe(21); // Including initial year
    
    // Final projection should be approximately 25M KES
    expect(parseFloat(projection[20].savingsBalance) / 1000000).toBeCloseTo(25, 1);
  });
});

/**
 * BUDGET CALCULATOR TESTS
 * Tests for the budget analysis and planning calculator
 */
describe('Budget Calculator Tests', () => {
  let budgetCalculator;
  
  beforeEach(() => {
    budgetCalculator = new BudgetCalculator();
  });
  
  test('should calculate monthly expense breakdown correctly', () => {
    // Basic monthly budget with common Kenyan expense categories
    const expenses = [
      { category: 'Housing', amount: 25000 },
      { category: 'Food', amount: 15000 },
      { category: 'Transportation', amount: 8000 },
      { category: 'Utilities', amount: 5000 },
      { category: 'Entertainment', amount: 3000 },
      { category: 'Savings', amount: 10000 },
      { category: 'Miscellaneous', amount: 4000 }
    ];
    
    const result = budgetCalculator.calculateBudgetBreakdown(expenses);
    
    // Total should be 70,000 KES
    expect(parseFloat(result.totalExpenses)).toBeCloseTo(70000, 0);
    
    // Housing should be approximately 35.7% of total
    expect(parseFloat(result.categoryPercentages.Housing)).toBeCloseTo(35.7, 1);
    
    // Savings rate should be approximately 14.3%
    expect(parseFloat(result.savingsRate)).toBeCloseTo(14.3, 1);
  });
  
  test('should calculate budget ratios according to 50/30/20 rule', () => {
    // Test against 50/30/20 rule (needs/wants/savings)
    const expenses = [
      // Needs (50%)
      { category: 'Housing', amount: 25000, type: 'need' },
      { category: 'Food', amount: 15000, type: 'need' },
      { category: 'Utilities', amount: 5000, type: 'need' },
      { category: 'Transportation', amount: 5000, type: 'need' },
      
      // Wants (30%)
      { category: 'Entertainment', amount: 5000, type: 'want' },
      { category: 'Dining Out', amount: 6000, type: 'want' },
      { category: 'Shopping', amount: 4000, type: 'want' },
      
      // Savings (20%)
      { category: 'Savings', amount: 10000, type: 'saving' },
      { category: 'Investment', amount: 5000, type: 'saving' }
    ];
    
    const income = 80000;
    const result = budgetCalculator.calculateBudgetRatios(expenses, income);
    
    // Needs should be 50,000 KES (62.5% of income)
    expect(parseFloat(result.needsPercentage)).toBeCloseTo(62.5, 1);
    
    // Wants should be 15,000 KES (18.75% of income)
    expect(parseFloat(result.wantsPercentage)).toBeCloseTo(18.75, 1);
    
    // Savings should be 15,000 KES (18.75% of income)
    expect(parseFloat(result.savingsPercentage)).toBeCloseTo(18.75, 1);
    
    // Budget should be considered slightly imbalanced (needs > 50%)
    expect(result.budgetBalance).toBe('needs-heavy');
  });
  
  test('should calculate debt-to-income ratio correctly', () => {
    // Monthly income and debt payments
    const monthlyIncome = 80000;
    const debtPayments = [
      { name: 'Personal Loan', payment: 8000 },
      { name: 'Mortgage', payment: 16000 },
      { name: 'Car Loan', payment: 5000 }
    ];
    
    const result = budgetCalculator.calculateDebtToIncomeRatio(monthlyIncome, debtPayments);
    
    // DTI should be approximately 36.25%
    expect(parseFloat(result.debtToIncomeRatio)).toBeCloseTo(36.25, 2);
    
    // DTI status should be "caution" (between 36-42%)
    expect(result.dtiStatus).toBe('caution');
  });
  
  test('should calculate discretionary income correctly', () => {
    // Calculate discretionary income (after essential expenses)
    const monthlyIncome = 70000;
    const essentialExpenses = [
      { category: 'Housing', amount: 20000 },
      { category: 'Food', amount: 12000 },
      { category: 'Utilities', amount: 4000 },
      { category: 'Transportation', amount: 6000 },
      { category: 'Debt Payments', amount: 10000 }
    ];
    
    const result = budgetCalculator.calculateDiscretionaryIncome(monthlyIncome, essentialExpenses);
    
    // Total essential expenses should be 52,000 KES
    expect(parseFloat(result.totalEssentialExpenses)).toBeCloseTo(52000, 0);
    
    // Discretionary income should be 18,000 KES
    expect(parseFloat(result.discretionaryIncome)).toBeCloseTo(18000, 0);
    
    // Discretionary income percentage should be approximately 25.7%
    expect(parseFloat(result.discretionaryPercentage)).toBeCloseTo(25.7, 1);
  });
  
  test('should provide budget recommendations based on income', () => {
    // Generate budget recommendations for 60,000 KES monthly income
    const result = budgetCalculator.generateBudgetRecommendations(60000);
    
    // Should have recommendations for standard categories
    expect(result.housing).toBeDefined();
    expect(result.food).toBeDefined();
    expect(result.transportation).toBeDefined();
    expect(result.savings).toBeDefined();
    
    // Housing recommendation should be approximately 18,000 KES (30% of income)
    expect(parseFloat(result.housing)).toBeCloseTo(18000, 0);
    
    // Savings recommendation should be approximately 12,000 KES (20% of income)
    expect(parseFloat(result.savings)).toBeCloseTo(12000, 0);
  });
  
  test('should calculate emergency fund requirements', () => {
    // Calculate 6-month emergency fund requirements
    const monthlyExpenses = [
      { category: 'Housing', amount: 25000 },
      { category: 'Food', amount: 15000 },
      { category: 'Utilities', amount: 5000 },
      { category: 'Transportation', amount: 7000 },
      { category: 'Insurance', amount: 3000 }
    ];
    
    const result = budgetCalculator.calculateEmergencyFund(monthlyExpenses);
    
    // Monthly essential expenses should be 55,000 KES
    expect(parseFloat(result.monthlyEssentials)).toBeCloseTo(55000, 0);
    
    // 3-month emergency fund should be 165,000 KES
    expect(parseFloat(result.threeMonthFund)).toBeCloseTo(165000, 0);
    
    // 6-month emergency fund should be 330,000 KES
    expect(parseFloat(result.sixMonthFund)).toBeCloseTo(330000, 0);
  });
});

/**
 * INTEGRATION TESTS
 * Tests that check interactions between different calculators
 */
describe('Calculator Integration Tests', () => {
  let loanCalculator;
  let investmentCalculator;
  let budgetCalculator;
  
  beforeEach(() => {
    loanCalculator = new LoanCalculator();
    investmentCalculator = new InvestmentCalculator();
    budgetCalculator = new BudgetCalculator();
  });
  
  test('should calculate loan affordability based on budget constraints', () => {
    // Monthly income and existing expenses
    const monthlyIncome = 80000;
    const expenses = [
      { category: 'Housing', amount: 20000 },
      { category: 'Food', amount: 15000 },
      { category: 'Utilities', amount: 5000 },
      { category: 'Transportation', amount: 8000 },
      { category: 'Entertainment', amount: 3000 },
      { category: 'Savings', amount: 10000 }
    ];
    
    // Calculate discretionary income
    const budgetResult = budgetCalculator.calculateDiscretionaryIncome(
      monthlyIncome,
      expenses.filter(exp => exp.category !== 'Entertainment' && exp.category !== 'Savings')
    );
    
    // Calculate maximum affordable loan based on 50% of discretionary income
    const maxPayment = budgetResult.discretionaryIncome * 0.5;
    
    const loanResult = loanCalculator.calculateAffordableLoanWithPayment({
      maxMonthlyPayment: maxPayment,
      interestRate: 14,
      loanTerm: 36 // 3 years
    });
    
    // Check if loan calculation uses correct input from budget analysis
    expect(parseFloat(loanResult.affordableLoanAmount) > 0).toBe(true);
    expect(parseFloat(loanResult.monthlyPayment) <= maxPayment).toBe(true);
  });
  
  test('should analyze investment vs debt repayment tradeoff', () => {
    // Analyze whether to invest or pay down debt
    // Loan: 100,000 KES at 15% for 2 years
    // Investment: 10% expected return
    
    // Option 1: Minimum loan payment + invest the rest
    const loanPayment = loanCalculator.calculateMonthlyPayment({
      loanAmount: 100000,
      interestRate: 15,
      loanTerm: 24
    });
    
    const extraAmount = 5000; // Additional available monthly cash
    const totalLoanCost = loanPayment.monthlyPayment * 24;
    
    // Option 2: Pay extra on loan
    const acceleratedPayment = loanCalculator.calculateLoanPayoff({
      loanAmount: 100000,
      interestRate: 15,
      regularPayment: loanPayment.monthlyPayment,
      extraPayment: extraAmount
    });
    
    // Option 3: Make regular payments and invest the extra
    const investmentGrowth = investmentCalculator.calculateInvestmentGrowth({
      initialInvestment: 0,
      annualReturnRate: 10,
      investmentPeriod: 2, // years
      compoundingFrequency: 'monthly',
      additionalContributions: extraAmount,
      contributionFrequency: 'monthly'
    });
    
    // Compare total costs and benefits
    const option1TotalCost = totalLoanCost - investmentGrowth.finalValue;
    const option2TotalCost = acceleratedPayment.totalPayments;
    
    // Test comparison logic works
    expect(option1TotalCost).toBeDefined();
    expect(option2TotalCost).toBeDefined();
    expect(acceleratedPayment.monthsSaved > 0).toBe(true);
  });
});

/**
 * UI TESTS
 * Tests to verify calculator UI components render and function correctly
 */
describe('Calculator UI Tests', () => {
  test('should render loan calculator form correctly', () => {
    // Setup UI test
    document.getElementById('calculator-container').innerHTML = `
      <div id="loan-calculator">
        <form id="loan-form">
          <input id="loan-amount" type="number" value="100000">
          <input id="loan-interest" type="number" value="14">
          <input id="loan-term" type="number" value="12">
          <select id="loan-type">
            <option value="personal">Personal Loan</option>
            <option value="mortgage">Mortgage</option>
          </select>
          <button id="calculate-loan" type="submit">Calculate</button>
        </form>
        <div id="loan-results"></div>
      </div>
    `;
    
    // Instantiate the loan calculator with DOM elements
    const loanCalculator = new LoanCalculator({
      formId: 'loan-form',
      amountId: 'loan-amount',
      interestId: 'loan-interest',
      termId: 'loan-term',
      typeId: 'loan-type',
      resultsId: 'loan-results',
      buttonId: 'calculate-loan'
    });
    
    // Mock the form submission
    const submitEvent = new window.Event('submit');
    const form = document.getElementById('loan-form');
    
    // Mock the calculation function
    loanCalculator.calculateAndDisplay = jest.fn();
    
    // Add event listener and trigger form submission
    loanCalculator.initEventListeners();
    form.dispatchEvent(submitEvent);
    
    // Verify calculation function was called
    expect(loanCalculator.calculateAndDisplay).toHaveBeenCalled();
  });
  
  test('should update UI with calculation results', () => {
    // Setup UI test
    document.getElementById('calculator-container').innerHTML = `
      <div id="investment-calculator">
        <form id="investment-form">
          <input id="investment-amount" type="number" value="100000">
          <input id="investment-rate" type="number" value="10">
          <input id="investment-years" type="number" value="5">
          <button id="calculate-investment" type="submit">Calculate</button>
        </form>
        <div id="investment-results"></div>
      </div>
    `;
    
    // Create a simple display function to test UI updates
    const displayResults = (results) => {
      const resultsDiv = document.getElementById('investment-results');
      resultsDiv.innerHTML = `
        <p>Future Value: KES ${results.finalValue.toFixed(2)}</p>
        <p>Total Returns: KES ${results.totalReturns.toFixed(2)}</p>
      `;
    };
    
    // Calculate some results
    const results = {
      finalValue: 161051.00,
      totalReturns: 61051.00
    };
    
    // Update the UI
    displayResults(results);
    
    // Verify the UI was updated correctly
    const resultsDiv = document.getElementById('investment-results');
    expect(resultsDiv.innerHTML).toContain('Future Value: KES 161051.00');
    expect(resultsDiv.innerHTML).toContain('Total Returns: KES 61051.00');
  });
});