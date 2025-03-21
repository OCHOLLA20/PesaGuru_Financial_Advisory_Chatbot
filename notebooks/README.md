# PesaGuru Notebooks

This directory contains Jupyter notebooks for data analysis, model development, API integrations, and system testing for the PesaGuru Financial Advisory Chatbot project.

## Overview

The notebooks in this repository serve multiple purposes:
- Analyzing financial data from various sources (NSE, CBK, etc.)
- Developing and training AI models for the chatbot
- Testing API integrations with financial services
- Evaluating system performance
- Generating insights for the chatbot's knowledge base

## Directory Structure

```
notebooks/
├── data_analysis/                # Data Analysis & Processing Notebooks
│   ├── financial_data/           # Financial market data analysis
│   ├── user_behavior/            # User interaction analysis
│   └── sentiment_analysis/       # Sentiment analysis of news and social media
│
├── ai_model_development/         # AI Model Development Notebooks
│   ├── chatbot_ai/               # Core chatbot models
│   └── investment_advisory/      # Investment recommendation models
│
├── predictive_modeling/          # Machine Learning & Predictive Modeling
│   ├── Stock_Price_Prediction.ipynb
│   ├── Loan_Credit_Analysis.ipynb
│   └── Anomaly_Detection_Financial_Data.ipynb
│
├── api_integration/              # API & Data Integration Notebooks
│   ├── NSE_Market_Data_Collection.ipynb
│   ├── Forex_Exchange_Analysis.ipynb
│   └── News_API_Scraper.ipynb
│
├── deployment_testing/           # Deployment & Testing Notebooks
│   ├── AI_Model_Performance_Evaluation.ipynb
│   ├── A-B_Testing_Chatbot_Features.ipynb
│   └── End_to_End_System_Testing.ipynb
│
├── templates/                    # Notebook templates
│   ├── analysis_template.ipynb
│   ├── model_development_template.ipynb
│   └── data_integration_template.ipynb
│
├── outputs/                      # Outputs from scheduled runs
├── data/                         # Local data files
│   ├── external/                 # Data from external sources
│   ├── processed/                # Cleaned/processed data
│   └── interim/                  # Intermediate data
│
└── README.md                     # This documentation file
```

## Key Notebooks and Their Purpose

### Financial Data Analysis

- **NSE_Market_Data_Collection.ipynb**: Fetches and analyzes stock market data from the Nairobi Stock Exchange
- **Financial_Chatbot_Survey_Analysis.ipynb**: Analyzes survey data to understand user needs and preferences
- **Sentiment_Analysis_News_Content.ipynb**: Performs sentiment analysis on financial news content

### AI Model Development

- **Investment_Recommendation_Model.ipynb**: Develops models for personalized investment recommendations
- **Risk_Analysis_Model.ipynb**: Creates risk profiling algorithms for users
- **Chatbot_Response_Optimization.ipynb**: Optimizes chatbot responses for accuracy and engagement
- **Swahili_Language_Support.ipynb**: Develops NLP capabilities for Swahili language interactions

### Predictive Modeling

- **Stock_Price_Prediction.ipynb**: Develops algorithms to predict stock price movements
- **Loan_Credit_Analysis.ipynb**: Analyzes loan options and credit risk
- **Anomaly_Detection_Financial_Data.ipynb**: Identifies unusual patterns in financial data

## Setup and Usage

### Prerequisites

To work with these notebooks, you'll need:

1. Python 3.8+
2. Jupyter Lab or Jupyter Notebook
3. Required Python packages (install using `pip install -r ../requirements.txt`)
4. Access to the project API keys and credentials (see below)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-organization/pesaguru.git

# Navigate to the project directory
cd pesaguru

# Install dependencies
pip install -r requirements.txt

# Start Jupyter Lab
jupyter lab
```

### API Credentials

To access the financial APIs used in these notebooks, you'll need to:

1. Create a `.env` file in the root project directory
2. Add your API keys in the following format:

```
NSE_API_KEY=your_nse_api_key
CBK_API_KEY=your_cbk_api_key
NEWS_API_KEY=your_news_api_key
MPESA_CONSUMER_KEY=your_mpesa_consumer_key
MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret
```

The notebooks will automatically use these credentials when needed.

## Working with the Notebooks

### Using the Templates

When creating a new notebook, start with an appropriate template from the `templates/` directory:

1. Copy the template to the appropriate subdirectory
2. Rename it according to your task
3. Fill in the required sections

### Data Storage Guidelines

- Store raw data in `data/external/`
- Store processed data in `data/processed/`
- Store intermediate calculations in `data/interim/`
- Do not commit large data files to Git (use `.gitignore`)

### Converting Notebooks to Production Code

To convert your notebook to production code:

1. Run the notebook from end-to-end to ensure it works correctly
2. Use the utility script to convert to Python modules:

```bash
python ../utils/scripts/notebook_to_production.py your_notebook.ipynb
```

This will create a Python module in the appropriate location in the `ai/` directory.

## Scheduled Notebooks

Some notebooks are scheduled to run automatically to update data and models. These runs are configured in `schedule_config.json` and executed by the scheduler script.

To add a notebook to the schedule:

1. Ensure your notebook can run end-to-end without errors
2. Add an entry to `schedule_config.json` with the path and schedule
3. Test the scheduled run manually:

```bash
python ../utils/scripts/schedule_notebook_jobs.py --test your_notebook.ipynb
```

## Best Practices

1. **Documentation**: Include detailed markdown cells explaining your analysis and decisions
2. **Reproducibility**: Set random seeds for any stochastic processes
3. **Modular Code**: Define functions for reusable code blocks
4. **Error Handling**: Include appropriate try/except blocks to handle errors gracefully
5. **Resource Management**: Close connections and free resources when done
6. **Version Control**: Keep track of model versions and dataset versions
7. **Performance**: Use `%%time` magic to track cell execution time for optimization

## Contributing

When contributing new notebooks:

1. Follow the existing directory structure and naming conventions
2. Start from an appropriate template
3. Document your notebook thoroughly
4. Ensure all code can run from top to bottom without errors
5. Remove any sensitive or personal information before committing
6. Include a summary of the notebook's purpose and findings at the top

## Troubleshooting

Common issues and solutions:

1. **API Access Problems**: Ensure your `.env` file is properly set up with valid credentials
2. **Missing Dependencies**: Ensure all requirements are installed with `pip install -r requirements.txt`
3. **Data Loading Errors**: Check that data paths are correct and files exist
4. **Memory Issues**: For large datasets, consider chunking or sampling data

For further assistance, contact the data science team lead.

## License

This project is licensed under the terms specified in the LICENSE file in the root directory.
