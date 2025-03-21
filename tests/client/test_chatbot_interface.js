// Import testing framework
const { test, expect } = require('@jest/globals');
const { JSDOM } = require('jsdom');
const fetchMock = require('jest-fetch-mock');

// Import chatbot modules
const ChatbotInterface = require('../../client/assets/js/chatbot/chatbotInterface');
const ChatbotAPI = require('../../client/assets/js/chatbot/chatbotAPI');
const MessageRenderer = require('../../client/assets/js/chatbot/messageRenderer');
const LanguageProcessor = require('../../client/assets/js/chatbot/languageProcessor');

// Setup DOM environment for tests
let dom;
let window;
let document;
let chatbotInterface;

beforeEach(() => {
  // Setup fetch mock
  fetchMock.resetMocks();
  
  // Create a new JSDOM instance before each test
  dom = new JSDOM(`
    <!DOCTYPE html>
    <html>
      <body>
        <div id="pesaguru-chatbot-container">
          <div id="chatbot-messages"></div>
          <form id="chatbot-form">
            <input type="text" id="chatbot-input" placeholder="Ask me about financial advice...">
            <button type="submit" id="chatbot-submit">Send</button>
          </form>
          <div id="chatbot-suggestions"></div>
          <div id="chatbot-language-selector">
            <button id="lang-en" class="active">English</button>
            <button id="lang-sw">Swahili</button>
          </div>
        </div>
      </body>
    </html>
  `, { url: 'http://localhost/' });
  
  window = dom.window;
  document = window.document;
  
  // Mock global objects
  global.window = window;
  global.document = document;
  global.HTMLElement = window.HTMLElement;
  global.fetch = fetchMock;
  global.localStorage = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn()
  };
  
  // Initialize chatbot interface
  chatbotInterface = new ChatbotInterface({
    containerSelector: '#pesaguru-chatbot-container',
    messagesSelector: '#chatbot-messages',
    formSelector: '#chatbot-form',
    inputSelector: '#chatbot-input',
    submitSelector: '#chatbot-submit',
    suggestionsSelector: '#chatbot-suggestions',
    languageSelectorSelector: '#chatbot-language-selector'
  });
});

/**
 * UI RENDERING TESTS
 * Tests for proper rendering of the chatbot interface elements
 */
describe('Chatbot UI Rendering Tests', () => {
  test('should initialize chatbot interface with correct elements', () => {
    // Check if interface elements exist
    expect(document.getElementById('chatbot-messages')).not.toBeNull();
    expect(document.getElementById('chatbot-form')).not.toBeNull();
    expect(document.getElementById('chatbot-input')).not.toBeNull();
    expect(document.getElementById('chatbot-submit')).not.toBeNull();
    
    // Check if chatbot interface properly initialized
    expect(chatbotInterface.isInitialized()).toBe(true);
  });
  
  test('should render welcome message on initialization', () => {
    // Trigger initialization
    chatbotInterface.initialize();
    
    // Check if welcome message is rendered
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('Welcome to PesaGuru');
    expect(messagesContainer.innerHTML).toContain('financial advisory chatbot');
  });
  
  test('should display typing indicator when bot is responding', () => {
    // Show typing indicator
    chatbotInterface.showTypingIndicator();
    
    // Check if typing indicator is visible
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('chatbot-typing-indicator');
    
    // Hide typing indicator
    chatbotInterface.hideTypingIndicator();
    
    // Check if typing indicator is removed
    expect(messagesContainer.innerHTML).not.toContain('chatbot-typing-indicator');
  });
  
  test('should render user message with correct styling', () => {
    // Add a user message
    chatbotInterface.addUserMessage('How do I invest in stocks in Kenya?');
    
    // Check if message is rendered with user styling
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('user-message');
    expect(messagesContainer.innerHTML).toContain('How do I invest in stocks in Kenya?');
  });
  
  test('should render bot message with correct styling', () => {
    // Add a bot message
    chatbotInterface.addBotMessage('To invest in stocks in Kenya, you need to open a CDS account through a registered stockbroker.');
    
    // Check if message is rendered with bot styling
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('bot-message');
    expect(messagesContainer.innerHTML).toContain('To invest in stocks in Kenya');
  });
  
  test('should render suggestion chips correctly', () => {
    const suggestions = [
      'NSE investment strategies',
      'Best performing stocks',
      'How to open a CDS account'
    ];
    
    // Display suggestions
    chatbotInterface.displaySuggestions(suggestions);
    
    // Check if suggestions are rendered
    const suggestionsContainer = document.getElementById('chatbot-suggestions');
    expect(suggestionsContainer.innerHTML).toContain('NSE investment strategies');
    expect(suggestionsContainer.innerHTML).toContain('Best performing stocks');
    expect(suggestionsContainer.innerHTML).toContain('How to open a CDS account');
    expect(suggestionsContainer.children.length).toBe(3);
  });
  
  test('should display error message when API fails', () => {
    // Simulate API error
    chatbotInterface.handleError(new Error('Failed to connect to server'));
    
    // Check if error message is displayed
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('error-message');
    expect(messagesContainer.innerHTML).toContain('Failed to connect');
  });
});

/**
 * USER INTERACTION TESTS
 * Tests for user interactions with the chatbot
 */
describe('Chatbot User Interaction Tests', () => {
  test('should handle form submission and send user message', () => {
    // Mock the sendMessage function
    chatbotInterface.sendMessage = jest.fn();
    
    // Set input value
    const input = document.getElementById('chatbot-input');
    input.value = 'What is the best way to save money?';
    
    // Submit the form
    const form = document.getElementById('chatbot-form');
    form.dispatchEvent(new window.Event('submit'));
    
    // Check if sendMessage was called with correct text
    expect(chatbotInterface.sendMessage).toHaveBeenCalledWith('What is the best way to save money?');
    
    // Check if input was cleared
    expect(input.value).toBe('');
  });
  
  test('should not send empty messages', () => {
    // Mock the sendMessage function
    chatbotInterface.sendMessage = jest.fn();
    
    // Submit form with empty input
    const input = document.getElementById('chatbot-input');
    input.value = '';
    
    const form = document.getElementById('chatbot-form');
    form.dispatchEvent(new window.Event('submit'));
    
    // Check that sendMessage was not called
    expect(chatbotInterface.sendMessage).not.toHaveBeenCalled();
  });
  
  test('should handle suggestion chip clicks', () => {
    // Mock the sendMessage function
    chatbotInterface.sendMessage = jest.fn();
    
    // Display suggestions
    const suggestions = ['Investment options', 'Savings accounts', 'Retirement planning'];
    chatbotInterface.displaySuggestions(suggestions);
    
    // Click on a suggestion
    const suggestionsContainer = document.getElementById('chatbot-suggestions');
    const suggestionChip = suggestionsContainer.children[1]; // "Savings accounts"
    suggestionChip.click();
    
    // Check if sendMessage was called with suggestion text
    expect(chatbotInterface.sendMessage).toHaveBeenCalledWith('Savings accounts');
    
    // Check if suggestions were cleared
    expect(suggestionsContainer.children.length).toBe(0);
  });
  
  test('should disable input during bot response', () => {
    // Simulate bot responding
    chatbotInterface.setBotResponding(true);
    
    // Check if input and submit button are disabled
    const input = document.getElementById('chatbot-input');
    const submitButton = document.getElementById('chatbot-submit');
    
    expect(input.disabled).toBe(true);
    expect(submitButton.disabled).toBe(true);
    
    // Simulate bot response complete
    chatbotInterface.setBotResponding(false);
    
    // Check if input and submit button are enabled
    expect(input.disabled).toBe(false);
    expect(submitButton.disabled).toBe(false);
  });
  
  test('should toggle language when language selector is clicked', () => {
    // Mock the setLanguage function
    chatbotInterface.setLanguage = jest.fn();
    
    // Click on Swahili language button
    const swahiliButton = document.getElementById('lang-sw');
    swahiliButton.click();
    
    // Check if language was changed to Swahili
    expect(chatbotInterface.setLanguage).toHaveBeenCalledWith('sw');
    
    // Check if button classes are updated
    expect(swahiliButton.classList.contains('active')).toBe(true);
    expect(document.getElementById('lang-en').classList.contains('active')).toBe(false);
  });
  
  test('should handle scroll to bottom of chat history', () => {
    // Mock scrollToBottom function
    chatbotInterface.scrollToBottom = jest.fn();
    
    // Add multiple messages to create scrollable content
    for (let i = 0; i < 10; i++) {
      chatbotInterface.addUserMessage(`Test message ${i}`);
      chatbotInterface.addBotMessage(`Response to message ${i}`);
    }
    
    // Check if scrollToBottom was called after adding messages
    expect(chatbotInterface.scrollToBottom).toHaveBeenCalled();
  });
});

/**
 * API INTEGRATION TESTS
 * Tests for integration with the chatbot backend API
 */
describe('Chatbot API Integration Tests', () => {
  test('should send message to API and handle response', async () => {
    // Mock API response
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'To save for retirement in Kenya, consider NSSF, pension schemes, and personal investments.',
      suggestions: ['NSSF benefits', 'Pension options', 'Investment strategies'],
      intent: 'retirement_planning'
    }));
    
    // Send a message
    await chatbotInterface.sendMessageToAPI('How can I save for retirement in Kenya?');
    
    // Check if fetch was called with correct parameters
    expect(fetchMock).toHaveBeenCalledWith('/api/chatbot', expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'Content-Type': 'application/json'
      }),
      body: expect.stringContaining('How can I save for retirement in Kenya?')
    }));
    
    // Check if bot message was added with API response
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('To save for retirement in Kenya');
    
    // Check if suggestions were displayed
    const suggestionsContainer = document.getElementById('chatbot-suggestions');
    expect(suggestionsContainer.innerHTML).toContain('NSSF benefits');
  });
  
  test('should handle API errors gracefully', async () => {
    // Mock API error
    fetchMock.mockRejectOnce(new Error('Network error'));
    
    // Mock error handler
    chatbotInterface.handleError = jest.fn();
    
    // Send a message that will trigger an error
    await chatbotInterface.sendMessageToAPI('What are the best investment options?');
    
    // Check if error handler was called
    expect(chatbotInterface.handleError).toHaveBeenCalled();
  });
  
  test('should send correct language preference to API', async () => {
    // Set language to Swahili
    chatbotInterface.setLanguage('sw');
    
    // Mock API response
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'Kwa kuwekeza katika hisa nchini Kenya, unahitaji kufungua akaunti ya CDS kupitia wakala wa hisa aliyesajiliwa.',
      suggestions: ['Mikakati ya uwekezaji NSE', 'Hisa zinazofanya vyema'],
      intent: 'stock_investment'
    }));
    
    // Send a message in Swahili
    await chatbotInterface.sendMessageToAPI('Ninawezaje kuwekeza katika hisa Kenya?');
    
    // Check if API request included language preference
    expect(fetchMock).toHaveBeenCalledWith('/api/chatbot', expect.objectContaining({
      body: expect.stringContaining('"language":"sw"')
    }));
    
    // Check if response in Swahili was correctly displayed
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('Kwa kuwekeza katika hisa');
  });
  
  test('should handle conversation context and maintain session', async () => {
    // First message to establish context
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'Safaricom is one of the most traded stocks on the NSE.',
      suggestions: ['Safaricom stock performance', 'Other telecom stocks'],
      intent: 'stock_info',
      conversationId: 'chat123456'
    }));
    
    await chatbotInterface.sendMessageToAPI('Tell me about Safaricom stock');
    
    // Clear mock to set up for second message
    fetchMock.resetMocks();
    
    // Second message should include conversation context
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'Safaricom stock has had a 5-year average return of approximately 15%.',
      suggestions: ['Current Safaricom price', 'Buy Safaricom stock'],
      intent: 'stock_performance',
      conversationId: 'chat123456'
    }));
    
    await chatbotInterface.sendMessageToAPI('What has been its performance?');
    
    // Check if second request included conversation ID
    expect(fetchMock).toHaveBeenCalledWith('/api/chatbot', expect.objectContaining({
      body: expect.stringContaining('"conversationId":"chat123456"')
    }));
  });
  
  test('should correctly process financial data and numbers in responses', async () => {
    // Mock API response with financial data
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'Based on your income of KES 50,000, you could save approximately KES 10,000 per month (20% of income).',
      financialData: {
        income: 50000,
        recommendedSavings: 10000,
        savingsPercentage: 20
      },
      intent: 'savings_recommendation'
    }));
    
    // Send message about savings
    await chatbotInterface.sendMessageToAPI('How much should I save from my 50,000 KES salary?');
    
    // Check if financial data was properly formatted in the response
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('KES 50,000');
    expect(messagesContainer.innerHTML).toContain('KES 10,000');
    expect(messagesContainer.innerHTML).toContain('20%');
  });
});

/**
 * MULTILINGUAL SUPPORT TESTS
 * Tests for English and Swahili language support
 */
describe('Chatbot Multilingual Support Tests', () => {
  test('should initialize with correct language based on user preference', () => {
    // Mock localStorage to return Swahili as preferred language
    global.localStorage.getItem.mockReturnValueOnce('sw');
    
    // Initialize chatbot with language preference
    chatbotInterface.initializeLanguage();
    
    // Check if language was set to Swahili
    expect(chatbotInterface.getCurrentLanguage()).toBe('sw');
    
    // Check if Swahili button is active
    const swahiliButton = document.getElementById('lang-sw');
    expect(swahiliButton.classList.contains('active')).toBe(true);
  });
  
  test('should update UI text when language is changed to Swahili', () => {
    // Set language to Swahili
    chatbotInterface.setLanguage('sw');
    
    // Check if placeholder text is updated
    const input = document.getElementById('chatbot-input');
    expect(input.placeholder).toBe('Niulize kuhusu ushauri wa kifedha...');
    
    // Check if submit button text is updated
    const submitButton = document.getElementById('chatbot-submit');
    expect(submitButton.textContent).toBe('Tuma');
  });
  
  test('should handle financial terminology translation correctly', () => {
    // Mock language processor translations
    const languageProcessor = new LanguageProcessor();
    languageProcessor.translateFinancialTerm = jest.fn().mockImplementation((term, language) => {
      const translations = {
        'stock': { 'en': 'stock', 'sw': 'hisa' },
        'savings': { 'en': 'savings', 'sw': 'akiba' },
        'interest rate': { 'en': 'interest rate', 'sw': 'kiwango cha riba' }
      };
      return translations[term][language] || term;
    });
    
    // Check English terms
    expect(languageProcessor.translateFinancialTerm('stock', 'en')).toBe('stock');
    expect(languageProcessor.translateFinancialTerm('savings', 'en')).toBe('savings');
    expect(languageProcessor.translateFinancialTerm('interest rate', 'en')).toBe('interest rate');
    
    // Check Swahili terms
    expect(languageProcessor.translateFinancialTerm('stock', 'sw')).toBe('hisa');
    expect(languageProcessor.translateFinancialTerm('savings', 'sw')).toBe('akiba');
    expect(languageProcessor.translateFinancialTerm('interest rate', 'sw')).toBe('kiwango cha riba');
  });
  
  test('should handle English to Swahili number formatting', () => {
    const languageProcessor = new LanguageProcessor();
    
    // Test currency formatting in different languages
    expect(languageProcessor.formatCurrency(5000, 'en')).toBe('KES 5,000');
    expect(languageProcessor.formatCurrency(5000, 'sw')).toBe('KES 5,000');
    
    // Test percentage formatting
    expect(languageProcessor.formatPercentage(15.5, 'en')).toBe('15.5%');
    expect(languageProcessor.formatPercentage(15.5, 'sw')).toBe('15.5%');
  });
  
  test('should store language preference in localStorage', () => {
    // Set language to Swahili
    chatbotInterface.setLanguage('sw');
    
    // Check if preference was stored in localStorage
    expect(global.localStorage.setItem).toHaveBeenCalledWith('pesaguru_language', 'sw');
  });
});

/**
 * FINANCIAL ADVICE TESTS
 * Tests to verify correct financial advice responses
 */
describe('Chatbot Financial Advice Tests', () => {
  test('should provide accurate NSE stock investment advice', async () => {
    // Mock API response for NSE investment query
    fetchMock.mockResponseOnce(JSON.stringify({
      response: `To invest in NSE stocks in Kenya, follow these steps:
        1. Choose a stockbroker registered with NSE
        2. Open a CDSC account
        3. Fund your account
        4. Place orders to buy stocks
        Popular brokers include Dyer & Blair, Faida Investment Bank, and AIB-AXYS Africa.`,
      intent: 'stock_investment_process'
    }));
    
    // Send query about stock investment
    await chatbotInterface.sendMessageToAPI('How do I invest in NSE stocks?');
    
    // Check if response contains key information
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('Choose a stockbroker');
    expect(messagesContainer.innerHTML).toContain('CDSC account');
    expect(messagesContainer.innerHTML).toContain('Dyer & Blair');
  });
  
  test('should provide accurate mobile money loan advice', async () => {
    // Mock API response for loan query
    fetchMock.mockResponseOnce(JSON.stringify({
      response: `Mobile money loans in Kenya include:
        1. M-Shwari: 7.5% facilitation fee (equivalent to 90% APR)
        2. KCB M-Pesa: 8.6% interest rate on 1-month loans
        3. Fuliza: 1% daily fee
        Always compare fees and ensure you can repay on time to avoid penalties.`,
      intent: 'loan_comparison'
    }));
    
    // Send query about mobile loans
    await chatbotInterface.sendMessageToAPI('What are the interest rates for mobile loans in Kenya?');
    
    // Check if response contains accurate loan information
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('M-Shwari: 7.5% facilitation fee');
    expect(messagesContainer.innerHTML).toContain('KCB M-Pesa: 8.6%');
    expect(messagesContainer.innerHTML).toContain('Fuliza: 1% daily fee');
  });
  
  test('should provide retirement planning advice specific to Kenya', async () => {
    // Mock API response for retirement planning
    fetchMock.mockResponseOnce(JSON.stringify({
      response: `For retirement planning in Kenya, consider:
        1. National Social Security Fund (NSSF) - mandatory contribution
        2. Occupational pension schemes through your employer
        3. Individual pension plans from providers like Britam, CIC, or Sanlam
        4. Investment in real estate, stocks, or government securities
        The earlier you start saving, the more comfortable your retirement will be.`,
      intent: 'retirement_planning'
    }));
    
    // Send query about retirement planning
    await chatbotInterface.sendMessageToAPI('How should I plan for retirement in Kenya?');
    
    // Check if response contains Kenya-specific retirement information
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('NSSF');
    expect(messagesContainer.innerHTML).toContain('Occupational pension');
    expect(messagesContainer.innerHTML).toContain('Britam');
  });
  
  test('should handle Kenyan tax-related questions accurately', async () => {
    // Mock API response for tax question
    fetchMock.mockResponseOnce(JSON.stringify({
      response: `Current income tax rates in Kenya (as of 2024):
        - Up to KES 24,000: 10%
        - KES 24,001 to KES 32,333: 25% 
        - Above KES 32,333: 30%
        Tax relief of KES 2,400 per month applies to all taxpayers.
        Consult with a tax professional for specific advice about your situation.`,
      intent: 'tax_information'
    }));
    
    // Send query about tax rates
    await chatbotInterface.sendMessageToAPI('What are the current income tax rates in Kenya?');
    
    // Check if response contains accurate tax information
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('Up to KES 24,000: 10%');
    expect(messagesContainer.innerHTML).toContain('KES 2,400 per month');
  });
  
  test('should integrate with NSE market data for stock information', async () => {
    // Mock API response with real-time stock data
    fetchMock.mockResponseOnce(JSON.stringify({
      response: `Safaricom (SCOM) stock information:
        Current price: KES 35.75
        52-week range: KES 31.20 - KES 42.00
        Market cap: KES 1.43 trillion
        Dividend yield: 3.9%
        
        Safaricom is the largest telecommunications provider in Kenya and a component of the NSE-20 Share Index.`,
      intent: 'stock_information',
      stockData: {
        symbol: 'SCOM',
        price: 35.75,
        change: -0.25,
        changePercent: -0.69,
        dayHigh: 36.00,
        dayLow: 35.60
      }
    }));
    
    // Send query about Safaricom stock
    await chatbotInterface.sendMessageToAPI('What is the current price of Safaricom stock?');
    
    // Check if response contains stock information
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('KES 35.75');
    expect(messagesContainer.innerHTML).toContain('KES 31.20 - KES 42.00');
    expect(messagesContainer.innerHTML).toContain('3.9%');
  });
});

/**
 * MESSAGE HISTORY TESTS
 * Tests for conversation history and persistence
 */
describe('Chatbot Message History Tests', () => {
  test('should maintain conversation history during session', () => {
    // Add multiple messages
    chatbotInterface.addUserMessage('How can I invest in NSE?');
    chatbotInterface.addBotMessage('To invest in NSE, you need to open a CDS account through a broker.');
    chatbotInterface.addUserMessage('Which broker is recommended?');
    chatbotInterface.addBotMessage('Popular brokers include Dyer & Blair, Faida, and AIB-AXYS Africa.');
    
    // Get conversation history
    const history = chatbotInterface.getConversationHistory();
    
    // Check if history contains all messages in correct order
    expect(history.length).toBe(4);
    expect(history[0].text).toContain('How can I invest in NSE?');
    expect(history[1].text).toContain('To invest in NSE');
    expect(history[2].text).toContain('Which broker is recommended?');
    expect(history[3].text).toContain('Popular brokers include');
    
    // Check if messages are displayed in the UI
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.children.length).toBe(4);
  });
  
  test('should save conversation history to localStorage', () => {
    // Add messages to conversation
    chatbotInterface.addUserMessage('What are money market funds?');
    chatbotInterface.addBotMessage('Money market funds are low-risk investment vehicles that invest in short-term debt securities.');
    
    // Save conversation to localStorage
    chatbotInterface.saveConversationHistory();
    
    // Check if localStorage.setItem was called with conversation data
    expect(global.localStorage.setItem).toHaveBeenCalledWith(
      'pesaguru_conversation_history',
      expect.stringContaining('Money market funds are low-risk investment')
    );
  });
  
  test('should load conversation history from localStorage', () => {
    // Mock localStorage to return saved conversation
    const savedConversation = JSON.stringify([
      { type: 'user', text: 'What are Treasury bonds?', timestamp: Date.now() - 1000 },
      { type: 'bot', text: 'Treasury bonds are long-term government securities with a fixed interest rate.', timestamp: Date.now() }
    ]);
    
    global.localStorage.getItem.mockReturnValueOnce(savedConversation);
    
    // Load conversation history
    chatbotInterface.loadConversationHistory();
    
    // Check if messages are displayed in the UI
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('What are Treasury bonds?');
    expect(messagesContainer.innerHTML).toContain('Treasury bonds are long-term government securities');
  });
  
  test('should create new conversation when clearing history', () => {
    // Add messages to conversation
    chatbotInterface.addUserMessage('How do I create a budget?');
    chatbotInterface.addBotMessage('To create a budget, start by tracking your income and expenses...');
    
    // Clear conversation history
    chatbotInterface.clearConversationHistory();
    
    // Check if messages container is empty
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.children.length).toBe(0);
    
    // Check if localStorage.removeItem was called
    expect(global.localStorage.removeItem).toHaveBeenCalledWith('pesaguru_conversation_history');
    
    // Check if new welcome message was added
    chatbotInterface.initialize();
    expect(messagesContainer.innerHTML).toContain('Welcome to PesaGuru');
  });
  
  test('should timestamp messages correctly', () => {
    // Mock date
    const mockDate = new Date('2024-03-15T14:30:00Z');
    const originalDate = global.Date;
    global.Date = jest.fn(() => mockDate);
    global.Date.now = jest.fn(() => mockDate.getTime());
    
    // Add a message
    chatbotInterface.addUserMessage('What is a good savings rate?');
    
    // Get the most recent message
    const history = chatbotInterface.getConversationHistory();
    const lastMessage = history[history.length - 1];
    
    // Check if message has correct timestamp
    expect(lastMessage.timestamp).toBe(mockDate.getTime());
    
    // Check if timestamp is displayed in the UI
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('14:30');
    
    // Restore original Date
    global.Date = originalDate;
  });
});

/**
 * ERROR HANDLING TESTS
 * Tests for error handling and recovery
 */
describe('Chatbot Error Handling Tests', () => {
  test('should handle network connectivity issues', async () => {
    // Mock network error
    fetchMock.mockRejectOnce(new Error('Failed to fetch'));
    
    // Send message that will trigger network error
    await chatbotInterface.sendMessageToAPI('What are the best investment options?');
    
    // Check if error message is displayed
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('network connection');
    expect(messagesContainer.innerHTML).toContain('Please check your internet connection');
  });
  
  test('should handle API error responses', async () => {
    // Mock API error response
    fetchMock.mockResponseOnce(JSON.stringify({
      error: true,
      message: 'Internal server error',
      code: 500
    }), { status: 500 });
    
    // Send message that will trigger server error
    await chatbotInterface.sendMessageToAPI('Tell me about investment options');
    
    // Check if error message is displayed
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('server error');
    expect(messagesContainer.innerHTML).toContain('Please try again later');
  });
  
  test('should recover after error and continue conversation', async () => {
    // First request fails
    fetchMock.mockRejectOnce(new Error('Network error'));
    
    // Send message that will trigger error
    await chatbotInterface.sendMessageToAPI('What are good investment options?');
    
    // Second request succeeds
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'Good investment options in Kenya include Treasury bills, bonds, stocks, and real estate.',
      intent: 'investment_options'
    }));
    
    // Send another message
    await chatbotInterface.sendMessageToAPI('Tell me about Treasury bills');
    
    // Check if successful response is displayed after error
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('Good investment options in Kenya');
  });
  
  test('should handle unexpected message format from API', async () => {
    // Mock malformed API response
    fetchMock.mockResponseOnce('{"malformed json');
    
    // Send message that will trigger parsing error
    await chatbotInterface.sendMessageToAPI('What are the current interest rates?');
    
    // Check if error message is displayed
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('system error');
    expect(messagesContainer.innerHTML).toContain('try again');
  });
  
  test('should handle timeout errors gracefully', async () => {
    // Mock timeout error
    fetchMock.mockResponseOnce(() => new Promise((resolve) => {
      setTimeout(() => { resolve({ body: 'Timeout!' }); }, 30000);
    }));
    
    // Set timeout for test
    chatbotInterface.apiTimeout = 100; // 100ms timeout for testing
    
    // Send message that will trigger timeout
    const timeoutPromise = chatbotInterface.sendMessageToAPI('What are the best savings accounts?');
    
    // Fast-forward timers
    jest.advanceTimersByTime(200);
    
    // Wait for the promise to reject
    await expect(timeoutPromise).rejects.toThrow();
    
    // Check if timeout message is displayed
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('request timed out');
    expect(messagesContainer.innerHTML).toContain('try again');
  });
});

/**
 * INTEGRATION TESTS
 * Tests for integration with other PesaGuru components
 */
describe('Chatbot Integration with Other Components', () => {
  test('should link to calculator tools when relevant', async () => {
    // Mock API response with calculator link
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'To calculate how much you need to save for retirement, you can use our Retirement Calculator tool.',
      intent: 'retirement_planning',
      actions: [
        {
          type: 'calculator_link',
          calculator: 'retirement',
          text: 'Open Retirement Calculator'
        }
      ]
    }));
    
    // Send message about retirement calculation
    await chatbotInterface.sendMessageToAPI('How much should I save for retirement?');
    
    // Check if calculator link is displayed
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('Open Retirement Calculator');
    expect(messagesContainer.innerHTML).toContain('calculator-link');
  });
  
  test('should display stock performance charts when discussing stocks', async () => {
    // Mock API response with stock chart data
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'Here is the performance of Safaricom stock over the past year:',
      intent: 'stock_performance',
      actions: [
        {
          type: 'stock_chart',
          symbol: 'SCOM',
          timeframe: '1y',
          chartId: 'safaricom-chart'
        }
      ]
    }));
    
    // Mock chart rendering function
    chatbotInterface.renderStockChart = jest.fn();
    
    // Send message about stock performance
    await chatbotInterface.sendMessageToAPI('Show me Safaricom stock performance');
    
    // Check if chart rendering function was called with correct parameters
    expect(chatbotInterface.renderStockChart).toHaveBeenCalledWith(
      expect.objectContaining({
        symbol: 'SCOM',
        timeframe: '1y',
        chartId: 'safaricom-chart'
      })
    );
  });
  
  test('should provide budget templates when discussing budgeting', async () => {
    // Mock API response with budget template
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'Here is a sample monthly budget for a Kenyan earning KES 50,000:',
      intent: 'budgeting',
      actions: [
        {
          type: 'budget_template',
          income: 50000,
          expenses: [
            { category: 'Housing', amount: 15000, percentage: 30 },
            { category: 'Food', amount: 10000, percentage: 20 },
            { category: 'Transportation', amount: 5000, percentage: 10 },
            { category: 'Utilities', amount: 3000, percentage: 6 },
            { category: 'Savings', amount: 7500, percentage: 15 },
            { category: 'Others', amount: 9500, percentage: 19 }
          ]
        }
      ]
    }));
    
    // Mock budget template rendering function
    chatbotInterface.renderBudgetTemplate = jest.fn();
    
    // Send message about budgeting
    await chatbotInterface.sendMessageToAPI('Help me create a budget for 50,000 KES salary');
    
    // Check if budget template rendering function was called
    expect(chatbotInterface.renderBudgetTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        income: 50000,
        expenses: expect.arrayContaining([
          expect.objectContaining({ category: 'Housing', amount: 15000 })
        ])
      })
    );
  });
  
  test('should open resource links in new tabs when provided', async () => {
    // Mock API response with external resource link
    fetchMock.mockResponseOnce(JSON.stringify({
      response: 'You can learn more about investing in Treasury bills on the Central Bank of Kenya website.',
      intent: 'treasury_bills',
      actions: [
        {
          type: 'external_link',
          url: 'https://www.centralbank.go.ke/securities/treasury-bills/',
          text: 'CBK Treasury Bills Information'
        }
      ]
    }));
    
    // Mock window.open function
    window.open = jest.fn();
    
    // Send message about Treasury bills
    await chatbotInterface.sendMessageToAPI('How do I invest in Treasury bills?');
    
    // Check if link is displayed in the message
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.innerHTML).toContain('CBK Treasury Bills Information');
    expect(messagesContainer.innerHTML).toContain('external-link');
    
    // Click on the link
    const linkElement = messagesContainer.querySelector('.external-link');
    linkElement.click();
    
    // Check if window.open was called with correct URL
    expect(window.open).toHaveBeenCalledWith(
      'https://www.centralbank.go.ke/securities/treasury-bills/',
      '_blank'
    );
  });
});

/**
 * ACCESSIBILITY TESTS
 * Tests for chatbot accessibility features
 */
describe('Chatbot Accessibility Tests', () => {
  test('should handle keyboard navigation properly', () => {
    // Mock form submission via keyboard (Enter key)
    const input = document.getElementById('chatbot-input');
    input.value = 'What are Treasury bills?';
    
    // Mock the sendMessage function
    chatbotInterface.sendMessage = jest.fn();
    
    // Create keyboard event (Enter key)
    const enterKeyEvent = new window.KeyboardEvent('keydown', {
      key: 'Enter',
      code: 'Enter',
      keyCode: 13,
      bubbles: true
    });
    
    // Dispatch event on input
    input.dispatchEvent(enterKeyEvent);
    
    // Check if sendMessage was called
    expect(chatbotInterface.sendMessage).toHaveBeenCalledWith('What are Treasury bills?');
  });
  
  test('should have proper ARIA attributes for screen readers', () => {
    // Initialize chatbot with ARIA attributes
    chatbotInterface.initialize();
    
    // Check if messages container has proper ARIA attributes
    const messagesContainer = document.getElementById('chatbot-messages');
    expect(messagesContainer.getAttribute('aria-live')).toBe('polite');
    expect(messagesContainer.getAttribute('role')).toBe('log');
    
    // Check if input has proper label and description
    const input = document.getElementById('chatbot-input');
    expect(input.getAttribute('aria-label')).toBe('Message to PesaGuru chatbot');
    
    // Check if button has proper attributes
    const submitButton = document.getElementById('chatbot-submit');
    expect(submitButton.getAttribute('aria-label')).toBe('Send message');
  });
  
  test('should support text-to-speech for chatbot responses', () => {
    // Mock window.speechSynthesis
    window.speechSynthesis = {
      speak: jest.fn(),
      cancel: jest.fn()
    };
    window.SpeechSynthesisUtterance = jest.fn().mockImplementation((text) => ({
      text,
      voice: null,
      rate: 1,
      pitch: 1,
      volume: 1
    }));
    
    // Enable text-to-speech
    chatbotInterface.enableTextToSpeech();
    
    // Add bot message
    chatbotInterface.addBotMessage('The current inflation rate in Kenya is 5.7%');
    
    // Check if speech synthesis was called
    expect(window.speechSynthesis.speak).toHaveBeenCalled();
    
    // Disable text-to-speech
    chatbotInterface.disableTextToSpeech();
    
    // Add another bot message
    chatbotInterface.addBotMessage('You should diversify your investments');
    
    // Check if speech synthesis was not called this time
    expect(window.speechSynthesis.speak).toHaveBeenCalledTimes(1);
  });
  
  test('should adjust font size for readability', () => {
    // Set initial font size
    document.documentElement.style.fontSize = '16px';
    
    // Increase font size
    chatbotInterface.increaseFontSize();
    
    // Check if font size was increased
    expect(document.documentElement.style.fontSize).toBe('18px');
    
    // Increase again
    chatbotInterface.increaseFontSize();
    
    // Check if font size was increased further
    expect(document.documentElement.style.fontSize).toBe('20px');
    
    // Decrease font size
    chatbotInterface.decreaseFontSize();
    
    // Check if font size was decreased
    expect(document.documentElement.style.fontSize).toBe('18px');
  });
  
  test('should support high contrast mode for visually impaired users', () => {
    // Enable high contrast mode
    chatbotInterface.enableHighContrastMode();
    
    // Check if high contrast class was added to container
    const container = document.getElementById('pesaguru-chatbot-container');
    expect(container.classList.contains('high-contrast')).toBe(true);
    
    // Disable high contrast mode
    chatbotInterface.disableHighContrastMode();
    
    // Check if high contrast class was removed
    expect(container.classList.contains('high-contrast')).toBe(false);
  });
});