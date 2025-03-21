@echo off
echo Starting PesaGuru full project initialization...

:: Navigate to the project directory
cd "C:\xampp\htdocs\pesaguru_web app"

:: Initialize Git repository if not already done
if not exist .git (
    echo Initializing Git repository...
    git init
)

:: Create base directory structure
echo Creating directory structure...

:: Create root files
echo Creating root files...
echo ^<?php ^?^> > .env
echo { "name": "ocholla20/pesaguru", "description": "AI-powered personalized financial advisory chatbot for Kenya", "type": "project" } > composer.json
echo. > composer.lock
echo MIT License > LICENSE
echo { "name": "pesaguru", "version": "1.0.0", "description": "AI-powered financial advisory chatbot" } > package.json
echo # PesaGuru - AI-Powered Financial Advisory for Kenya > README.md
echo numpy==1.21.0 > requirements.txt
echo version: '3' > docker-compose.yml

:: Create AI directory structure
mkdir ai
mkdir ai\api
mkdir ai\data
mkdir ai\dialogflow
mkdir ai\dialogflow\intents
mkdir ai\dialogflow\entities
mkdir ai\models
mkdir ai\models\generated
mkdir ai\nlp
mkdir ai\recommenders
mkdir ai\services
mkdir ai\api_integration

:: Create AI files
echo # AI API endpoints > ai\api.py
echo { "terms": [] } > ai\data\financial_terms_dictionary.json
echo intent,examples > ai\data\intent_training_data.csv
echo { "terms": [] } > ai\data\kenyan_financial_corpus.json
echo { "terms": [] } > ai\data\swahili_corpus.json
echo sentiment,text > ai\data\sentiment_training_data.csv
echo # Dialogflow webhook handler > ai\dialogflow\webhook.py
echo # Chatbot model evaluation > ai\models\evaluate_model.py
echo # BERT fine-tuning script > ai\models\fine_tune_bert.py
echo # Chatbot training script > ai\models\train_chatbot.py
echo # Domain-specific BERT implementation > ai\models\financial_bert.py
echo # Intent classification model > ai\models\intent_classifier.py
echo # Entity extraction model > ai\models\entity_extractor.py
echo # Investment recommendation model > ai\models\recommendation_model.py
echo { "models": [] } > ai\models\model_registry.json
echo # Text preprocessing pipeline > ai\nlp\text_preprocessor.py
echo # Tokenization utilities > ai\nlp\tokenizer.py
echo # Language detection module > ai\nlp\language_detector.py
echo # Swahili language processor > ai\nlp\swahili_processor.py
echo # Conversation context manager > ai\nlp\context_manager.py
echo # Investment recommendation engine > ai\recommenders\investment_recommender.py
echo # Risk assessment algorithms > ai\recommenders\risk_analyzer.py
echo # Portfolio optimization engine > ai\recommenders\portfolio_optimizer.py
echo # Market prediction module > ai\recommenders\market_predictor.py
echo # Main chatbot service > ai\services\chatbot_service.py
echo # Market analysis service > ai\services\market_analysis.py
echo # Market data API service > ai\services\market_data_api.py
echo # Portfolio AI service > ai\services\portfolio_ai.py
echo # Risk evaluation service > ai\services\risk_evaluation.py
echo # Sentiment analysis service > ai\services\sentiment_analysis.py
echo # Recommendation engine service > ai\services\recommendation_engine.py
echo # User profiling service > ai\services\user_profiler.py
echo # Conversation manager service > ai\services\conversation_manager.py
echo # NSE API integration > ai\api_integration\nse_api.py
echo # Central Bank of Kenya API > ai\api_integration\cbk_api.py
echo # M-Pesa API integration > ai\api_integration\mpesa_api.py
echo # Crypto API integration > ai\api_integration\crypto_api.py
echo # Forex API integration > ai\api_integration\forex_api.py
echo # Financial news API integration > ai\api_integration\news_api.py

:: Create assets directory structure
mkdir assets
mkdir assets\css
mkdir assets\css\Market_Data_and_Insights
mkdir assets\css\Tools_and_Calculators
mkdir assets\js
mkdir assets\js\charts
mkdir assets\js\market-data
mkdir assets\js\chatbot
mkdir assets\images
mkdir assets\images\icons
mkdir assets\images\illustrations

:: Create assets files
echo /* Interest rates styling */ > assets\css\Market_Data_and_Insights\interest_rates.css
echo /* Investment calculator styling */ > assets\css\Tools_and_Calculators\investment_calculator.css

:: Create client directory structure
mkdir client
mkdir client\assets
mkdir client\assets\css
mkdir client\assets\js
mkdir client\assets\images
mkdir client\pages
mkdir client\pages\Authentication
mkdir client\pages\Chatbot Interaction
mkdir client\pages\Financial_Advisory_Services
mkdir client\pages\Learning_Resources
mkdir client\pages\Market_Data_and_Insights
mkdir client\pages\Support_and_Assistance
mkdir client\pages\Tools_and_Calculators
mkdir client\pages\User_Profile_and_Settings

:: Create client files
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Forgot Password^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Authentication\forgot_password.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Login^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Authentication\login.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Logout^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Authentication\logout.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Register^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Authentication\register.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Reset Password^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Authentication\reset_password.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Chatbot^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Chatbot Interaction\chatbot.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Saved Conversations^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Chatbot Interaction\saved_conversations.html

:: Creating more client files (continuing)
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Accounts^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Financial_Advisory_Services\accounts.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Add Expense^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Financial_Advisory_Services\add_expense.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Budgeting & Savings^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Financial_Advisory_Services\budgeting_savings.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Cards^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Financial_Advisory_Services\cards.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Check Reports^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Financial_Advisory_Services\check_Reports.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Investment Planning^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Financial_Advisory_Services\investment_planning.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Loan & Credit Analysis^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Financial_Advisory_Services\loan_credit_analysis.html
echo ^<!DOCTYPE html^>^<html^>^<head^>^<title^>Set a Savings Goal^</title^>^</head^>^<body^>^</body^>^</html^> > client\pages\Financial_Advisory_Services\Set_a_Savings_Goal.html

:: Create database directory structure
mkdir database
mkdir database\migrations
mkdir database\seeds
mkdir database\models
mkdir database\cache

:: Create database files
echo -- Create users table > database\migrations\create_users_table.sql
echo -- Create risk profiles table > database\migrations\create_risk_profiles_table.sql
echo -- Create portfolios table > database\migrations\create_portfolios_table.sql
echo -- Create transactions table > database\migrations\create_transactions_table.sql
echo -- Create conversation history table > database\migrations\create_conversation_history_table.sql
echo -- Create financial goals table > database\migrations\create_financial_goals_table.sql
echo -- Create market data cache table > database\migrations\create_market_data_cache_table.sql
echo -- Create investment recommendations table > database\migrations\create_investment_recommendations_table.sql
echo -- Create user feedback table > database\migrations\create_user_feedback_table.sql
echo -- Default risk profiles > database\seeds\default_risk_profiles.sql
echo -- Financial product categories > database\seeds\financial_product_categories.sql
echo -- Kenya investment options > database\seeds\kenya_investment_options.sql
echo ^<?php // User data model ^?^> > database\models\UserModel.php
echo ^<?php // Portfolio data model ^?^> > database\models\PortfolioModel.php
echo ^<?php // Transaction data model ^?^> > database\models\TransactionModel.php
echo ^<?php // Risk profile data model ^?^> > database\models\RiskProfileModel.php
echo ^<?php // Conversation history model ^?^> > database\models\ConversationModel.php
echo ^<?php // Financial goals model ^?^> > database\models\FinancialGoalModel.php
echo ^<?php // Redis cache connection ^?^> > database\cache\redis_connector.php
echo ^<?php // Market data caching ^?^> > database\cache\market_data_cache.php
echo ^<?php // Chatbot response caching ^?^> > database\cache\response_cache.php

:: Create docker directory structure
mkdir docker
mkdir docker\api
mkdir docker\ai
mkdir docker\web
mkdir docker\db
mkdir docker\jupyter

:: Create docker files
echo FROM php:7.4-apache > docker\api\Dockerfile
echo FROM python:3.9-slim > docker\ai\Dockerfile
echo FROM nginx:latest > docker\web\Dockerfile
echo FROM mysql:8.0 > docker\db\Dockerfile
echo FROM jupyter/datascience-notebook > docker\jupyter\Dockerfile
echo c.NotebookApp.password = '' > docker\jupyter\jupyter_notebook_config.py

:: Create docs directory
mkdir docs

:: Create docs files
echo # API Documentation > docs\api-docs.md
echo # Chatbot Design > docs\chatbot-design.md
echo # System Architecture > docs\system-architecture.md
echo # Deployment Guide > docs\deployment-guide.md
echo # Developer Guide > docs\developer-guide.md
echo # API Integration Guide > docs\api-integration.md
echo # User Manual > docs\user-manual.md
echo # Notebooks Guide > docs\notebooks-guide.md

:: Create notebooks directory structure
mkdir notebooks
mkdir notebooks\data_analysis
mkdir notebooks\data_analysis\financial_data
mkdir notebooks\data_analysis\user_behavior
mkdir notebooks\data_analysis\sentiment_analysis
mkdir notebooks\ai_model_development
mkdir notebooks\ai_model_development\chatbot_ai
mkdir notebooks\ai_model_development\investment_advisory
mkdir notebooks\predictive_modeling
mkdir notebooks\api_integration
mkdir notebooks\deployment_testing
mkdir notebooks\templates
mkdir notebooks\outputs
mkdir notebooks\data
mkdir notebooks\data\external
mkdir notebooks\data\processed
mkdir notebooks\data\interim

:: Create notebook files (just a few examples)
echo {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 4} > notebooks\data_analysis\financial_data\Market_Trend_Analysis.ipynb
echo {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 4} > notebooks\data_analysis\financial_data\Macroeconomic_Indicators_Analysis.ipynb
echo {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 4} > notebooks\data_analysis\financial_data\Sector_Performance_Analysis.ipynb
echo # Notebooks README > notebooks\README.md
echo { "schedule": [] } > notebooks\schedule_config.json

:: Create server directory structure
mkdir server
mkdir server\config
mkdir server\controllers
mkdir server\middlewares
mkdir server\models
mkdir server\routes
mkdir server\services
mkdir server\services\auth
mkdir server\services\financial
mkdir server\services\integrations
mkdir server\services\notifications
mkdir server\security

:: Create server files
echo ^<?php // Authentication configuration ^?^> > server\config\auth.php
echo ^<?php // Database configuration ^?^> > server\config\db.php
echo ^<?php // API keys configuration ^?^> > server\config\api_keys.php
echo ^<?php // Chatbot configuration ^?^> > server\config\chatbot_config.php
echo ^<?php // Localization configuration ^?^> > server\config\localization.php
echo ^<?php // Security configuration ^?^> > server\config\security_config.php
echo ^<?php // Authentication controller ^?^> > server\controllers\authController.php
echo ^<?php // Chatbot controller ^?^> > server\controllers\chatbotController.php
echo ^<?php // Portfolio controller ^?^> > server\controllers\portfolioController.php
echo ^<?php // Risk assessment controller ^?^> > server\controllers\riskAssessmentController.php
echo ^<?php // Risk profile controller ^?^> > server\controllers\riskProfileController.php
echo ^<?php // Subscription controller ^?^> > server\controllers\subscriptionController.php
echo ^<?php // User controller ^?^> > server\controllers\userController.php
echo ^<?php // Market data controller ^?^> > server\controllers\marketDataController.php
echo ^<?php // Financial goals controller ^?^> > server\controllers\financialGoalController.php
echo ^<?php // Feedback controller ^?^> > server\controllers\feedbackController.php
echo ^<?php // Authentication middleware ^?^> > server\middlewares\auth_middleware.php
echo ^<?php // Security middleware ^?^> > server\middlewares\security_middleware.php
echo ^<?php // Rate limiting middleware ^?^> > server\middlewares\rate_limiting_middleware.php
echo ^<?php // Localization middleware ^?^> > server\middlewares\localization_middleware.php
echo ^<?php // API validation middleware ^?^> > server\middlewares\api_validation_middleware.php

:: Create tests directory structure
mkdir tests
mkdir tests\ai
mkdir tests\client
mkdir tests\server
mkdir tests\integration

:: Create tests files
echo # Chatbot tests > tests\ai\test_chatbot.py
echo # Sentiment analysis tests > tests\ai\test_sentiment_analysis.py
echo # Recommendation engine tests > tests\ai\test_recommendation_engine.py
echo # Language detection tests > tests\ai\test_language_detection.py
echo # Market analysis tests > tests\ai\test_market_analysis.py
echo // UI tests > tests\client\test_ui.js
echo // Chatbot interface tests > tests\client\test_chatbot_interface.js
echo // Calculator tests > tests\client\test_calculators.js
echo # API tests > tests\server\test_api.py
echo # Security tests > tests\server\test_security.py
echo # Authentication tests > tests\server\test_auth.py
echo # Market data tests > tests\server\test_market_data.py
echo # Financial services tests > tests\server\test_financial_services.py
echo # End-to-end tests > tests\integration\test_end_to_end.py
echo # API integration tests > tests\integration\test_api_integrations.py
echo # Performance tests > tests\integration\test_performance.py

:: Create utils directory structure
mkdir utils
mkdir utils\jupyter_helpers
mkdir utils\scripts

:: Create utils files
echo # Package initialization > utils\jupyter_helpers\__init__.py
echo # Data loading utilities > utils\jupyter_helpers\data_loaders.py
echo # Visualization helpers > utils\jupyter_helpers\visualization.py
echo # Model export utilities > utils\jupyter_helpers\model_export.py
echo # Notebook to production conversion > utils\scripts\notebook_to_production.py
echo # Schedule notebook jobs > utils\scripts\schedule_notebook_jobs.py
echo # Sync models > utils\scripts\sync_models.py
echo @echo off > utils\scripts\initialize_notebooks.bat
echo echo Initializing notebooks... >> utils\scripts\initialize_notebooks.bat

:: Create kubernetes directory structure
mkdir kubernetes

:: Create kubernetes files
echo apiVersion: apps/v1 > kubernetes\api-deployment.yaml
echo apiVersion: apps/v1 > kubernetes\ai-deployment.yaml
echo apiVersion: apps/v1 > kubernetes\web-deployment.yaml
echo apiVersion: apps/v1 > kubernetes\db-deployment.yaml
echo apiVersion: apps/v1 > kubernetes\redis-deployment.yaml
echo apiVersion: apps/v1 > kubernetes\jupyter-deployment.yaml
echo apiVersion: networking.k8s.io/v1 > kubernetes\ingress.yaml

:: Create .gitignore file with proper content
echo # XAMPP specific > .gitignore
echo /xampp/ >> .gitignore
echo # Environment files >> .gitignore
echo .env >> .gitignore
echo .env.local >> .gitignore
echo # Dependency directories >> .gitignore
echo /vendor/ >> .gitignore
echo /node_modules/ >> .gitignore
echo # Logs and databases >> .gitignore
echo *.log >> .gitignore
echo *.sql >> .gitignore
echo # OS generated files >> .gitignore
echo .DS_Store >> .gitignore
echo Thumbs.db >> .gitignore
echo # IDE folders >> .gitignore
echo .idea/ >> .gitignore
echo .vscode/ >> .gitignore

:: Add and commit files to Git
echo Adding files to Git...
git add .

echo Committing files...
git commit -m "Initialize PesaGuru full project structure"

echo Full project structure initialization complete!
echo.
echo To push to GitHub, use: git push origin main
echo.
echo Press any key to exit...
pause > nul