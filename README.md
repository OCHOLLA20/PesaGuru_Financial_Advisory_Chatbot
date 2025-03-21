# PesaGuru - AI-Powered Financial Advisory for Kenya 

## 📊 Overview

PesaGuru is an AI-powered chatbot designed to provide personalized financial advisory and investment planning services to Kenyan users. It aims to democratize financial advice through technology, making it accessible to low and middle-income consumers who traditionally have limited access to such services.

The chatbot leverages natural language processing, user profiling, and integration with real-time financial data to deliver tailored recommendations across various financial domains.

## 🚀 Key Features

- **Personalized Investment Advisory**: Tailored investment recommendations based on user's risk profile, financial goals, and market conditions
- **Financial Market Analysis**: Real-time NSE stock data, trends, and sector performance insights
- **Loan Comparison**: Compare rates and terms across various financial institutions and mobile lenders
- **Portfolio Management**: Track, analyze, and optimize investment portfolios
- **Financial Education**: Learn financial concepts through interactive modules and simplified explanations
- **Multilingual Support**: Interface in both English and Swahili with support for code-switching
- **Goal Setting & Tracking**: Set and monitor progress toward various financial objectives
- **Risk Profiling**: Assessment of risk tolerance to guide investment decisions

## 🛠️ Technologies

- **Backend**: Python, FastAPI
- **AI/ML**: BERT, GPT, TensorFlow, PyTorch
- **NLP Framework**: Hugging Face Transformers, SpaCy, NLTK
- **Frontend**: React.js, Tailwind CSS
- **Database**: PostgreSQL
- **API Integrations**: NSE API, CBK API, M-Pesa API, Yahoo Finance, Alpha Vantage
- **DevOps**: Docker, Kubernetes
- **Security**: OAuth2, JWT, AES-256 encryption

## 📋 Project Structure

The project follows a detailed, modular architecture:

```
PesaGuru/
├── ai/
│   ├── api.py                           # Main API interface
│   ├── data/                            # Training and reference data
│   │   ├── financial_terms_dictionary.json
│   │   ├── kenyan_financial_corpus.json # Kenya-specific terms
│   │   └── swahili_corpus.json          # Swahili language data
│   ├── dialogflow/                      # Dialogflow integration
│   ├── models/                          # ML models
│   │   ├── financial_bert.py            # Domain-specific BERT model
│   │   ├── sentiment_model.pkl          # Sentiment analysis
│   │   ├── intent_classifier.py         # Intent classification
│   │   └── recommendation_model.pkl     # Investment recommendations
│   ├── nlp/                             # NLP components
│   │   ├── text_preprocessor.py         # Preprocessing pipeline
│   │   ├── language_detector.py         # English/Swahili detection
│   │   └── context_manager.py           # Conversation context
│   ├── recommenders/                    # Recommendation engines
│   │   ├── investment_recommender.py    # Investment products
│   │   ├── risk_analyzer.py             # Risk assessment
│   │   └── portfolio_optimizer.py       # Portfolio optimization
│   ├── services/                        # Core services
│   │   ├── market_analysis.py
│   │   ├── recommendation_engine.py     # Personalized recommendations
│   │   └── user_profiler.py             # User profiling
│   └── api_integration/                 # External API integrations
│       ├── nse_api.py                   # Nairobi Stock Exchange API
│       ├── cbk_api.py                   # Central Bank of Kenya API
│       ├── mpesa_api.py                 # M-Pesa API integration
│       └── forex_api.py                 # Forex exchange rates API
├── client/
│   └── pages/
│       ├── Authentication/              # Auth pages
│       ├── Chatbot Interaction/         # Main chatbot UI
│       ├── Financial_Advisory_Services/ # Core services pages
│       ├── Learning_Resources/          # Educational content
│       ├── Market_Data_and_Insights/    # Market trends and data
│       ├── Tools_and_Calculators/       # Financial calculators
│       └── User_Profile_and_Settings/   # User settings
├── database/
│   ├── migrations/                      # DB schema migrations
│   ├── seeds/                           # Seed data
│   ├── models/                          # Database models
│   └── cache/                           # Caching layer
├── docker/                              # Docker configurations
│   ├── api/
│   ├── ai/
│   ├── web/
│   ├── db/
│   └── jupyter/
├── docs/                                # Documentation
├── notebooks/                           # Jupyter notebooks
│   ├── data_analysis/                   # Data analysis notebooks
│   ├── ai_model_development/            # Model development
│   ├── predictive_modeling/             # ML prediction models
│   └── api_integration/                 # API testing
├── server/
│   ├── config/                          # Server configurations
│   ├── controllers/                     # Request controllers
│   ├── middlewares/                     # API middlewares
│   ├── models/                          # Data models
│   ├── routes/                          # API routes
│   ├── services/                        # Core server services
│   │   ├── auth/                        # Authentication
│   │   ├── financial/                   # Financial analysis
│   │   ├── integrations/                # External services
│   │   └── notifications/               # User notifications
│   └── security/                        # Security services
├── tests/                               # Test suites
│   ├── ai/                              # AI model tests
│   ├── client/                          # Frontend tests
│   ├── server/                          # Backend tests
│   └── integration/                     # End-to-end tests
├── utils/                               # Utility scripts
└── kubernetes/                          # Kubernetes configs
```

## 🔧 Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- Docker and Docker Compose
- PostgreSQL 13+

### Setup

1. Clone the repository
```bash
git clone https://github.com/username/pesaguru.git
cd pesaguru
```

2. Set up environment variables
```bash 
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. Start the application using Docker
```bash
docker-compose up -d
```

4. Access the application
```
Frontend: http://localhost:3000
API: http://localhost:8000
```

## 💡 Usage Examples

### Investment Advisory
```
User: "I have 50,000 KES to invest for 2 years. What are my options?"

PesaGuru: "Based on your risk profile (moderate) and timeframe (2 years), 
here are some options:

1. Treasury Bills (91-day): Current rate 9.2% p.a. - Low risk
2. Money Market Fund: Average return 9.8% p.a. - Low-moderate risk
3. NSE Blue-chip stocks: Potential 15-20% p.a. - Moderate risk

Would you like more details on any of these options?"
```

### Loan Comparison
```
User: "Compare M-Shwari and KCB-M-Pesa loan rates"

PesaGuru: "Here's a comparison of mobile loan options:

M-Shwari:
- Interest rate: 7.5% per month
- Loan limit: Based on M-Pesa usage
- Repayment period: 30 days

KCB-M-Pesa:
- Interest rate: 6.3% per month
- Loan limit: Up to KES 250,000
- Repayment period: 30-180 days

KCB-M-Pesa offers a lower interest rate and flexible repayment options."
```

## 📊 API Integrations

PesaGuru integrates with various financial APIs to provide real-time data:

- **NSE API**: Real-time stock quotes, market indices, and historical data
- **CBK API**: Interest rates, forex exchange rates, and monetary policy updates
- **M-Pesa API**: Payment integration and mobile loan data
- **Yahoo Finance API**: Global market data and stock information
- **CoinGecko API**: Cryptocurrency market data
- **Alpha Vantage API**: Financial market data and technical indicators

## 📝 Development Roadmap

- [x] Core NLP engine implementation
- [x] User profiling system
- [x] NSE data integration
- [x] Basic financial advisory functionality
- [ ] Multi-language support expansion
- [ ] Voice interface integration
- [ ] M-Pesa transaction analysis
- [ ] Advanced portfolio optimization

## 🤝 Contributing

Contributions are welcome! Please check out our [contributing guidelines](CONTRIBUTING.md).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- Strathmore University School of Computing & Engineering Sciences
- Kenya Capital Markets Authority
- Central Bank of Kenya
- Nairobi Securities Exchange
- Financial Sector Deepening Kenya

---


