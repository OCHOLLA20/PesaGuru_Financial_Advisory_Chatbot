import json
import logging
import os
from datetime import datetime
from flask import Flask, request, jsonify
import requests
from functools import wraps

# Import PesaGuru services
import sys
sys.path.append('../../')
from ai.services.chatbot_service import ChatbotService
from ai.services.market_analysis import MarketAnalysisService
from ai.services.market_data_api import MarketDataAPI
from ai.services.portfolio_ai import PortfolioAI
from ai.services.risk_evaluation import RiskEvaluator
from ai.services.sentiment_analysis import SentimentAnalyzer
from ai.nlp.language_detector import LanguageDetector
from ai.api_integration.nse_api import NSEApi
from ai.api_integration.cbk_api import CBKApi
from ai.api_integration.mpesa_api import MPesaApi
from ai.api_integration.crypto_api import CryptoApi
from ai.api_integration.forex_api import ForexApi

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("webhook.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize services
chatbot_service = ChatbotService()
market_analysis = MarketAnalysisService()
market_data_api = MarketDataAPI()
portfolio_ai = PortfolioAI()
risk_evaluator = RiskEvaluator()
sentiment_analyzer = SentimentAnalyzer()
language_detector = LanguageDetector()
nse_api = NSEApi()
cbk_api = CBKApi()
mpesa_api = MPesaApi()
crypto_api = CryptoApi()
forex_api = ForexApi()

# Security middleware
def require_auth(f):
    """Authentication decorator for API endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_token = request.headers.get('Authorization', '')
        
        if not auth_token.startswith('Bearer '):
            logger.warning("Missing or invalid authorization token")
            return jsonify({'error': 'Unauthorized access'}), 401
        
        token = auth_token.split(' ')[1]
        # In production, validate the token with proper JWT verification
        if not token:
            logger.warning("Empty authorization token")
            return jsonify({'error': 'Unauthorized access'}), 401
            
        return f(*args, **kwargs)
    return decorated

# Helper functions
def get_intent_handler(intent_name):
    """Maps intent names to their handler functions"""
    intent_handlers = {
        'Investment.Advice': handle_investment_advice,
        'Loan.Comparison': handle_loan_comparison,
        'Market.Data': handle_market_data,
        'Risk.Assessment': handle_risk_assessment,
        'Budget.Planning': handle_budget_planning,
        'Savings.Goals': handle_savings_goals,
        'Financial.Education': handle_financial_education,
        'Crypto.Trends': handle_crypto_trends,
        'Forex.Rates': handle_forex_rates,
        'Default.Fallback': handle_fallback
    }
    
    return intent_handlers.get(intent_name, handle_fallback)

def extract_parameters(req):
    """Extract parameters from Dialogflow request"""
    try:
        parameters = req.get('queryResult', {}).get('parameters', {})
        return parameters
    except Exception as e:
        logger.error(f"Error extracting parameters: {str(e)}")
        return {}

def extract_contexts(req):
    """Extract active contexts from Dialogflow request"""
    try:
        output_contexts = req.get('queryResult', {}).get('outputContexts', [])
        contexts = {}
        
        for context in output_contexts:
            name = context.get('name', '').split('/')[-1]
            parameters = context.get('parameters', {})
            contexts[name] = parameters
            
        return contexts
    except Exception as e:
        logger.error(f"Error extracting contexts: {str(e)}")
        return {}

def detect_language(text):
    """Detect whether the text is in English or Swahili"""
    return language_detector.detect(text)

def create_response(fulfillment_text, fulfillment_messages=None, output_contexts=None):
    """Create a properly formatted Dialogflow webhook response"""
    response = {
        'fulfillmentText': fulfillment_text
    }
    
    if fulfillment_messages:
        response['fulfillmentMessages'] = fulfillment_messages
        
    if output_contexts:
        response['outputContexts'] = output_contexts
        
    return response

def log_interaction(session_id, intent, parameters, language, response):
    """Log chatbot interactions for analysis and improvement"""
    interaction = {
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        'intent': intent,
        'parameters': parameters,
        'language': language,
        'response': response
    }
    
    logger.info(f"Chatbot interaction: {json.dumps(interaction)}")
    # In a production environment, we would store this in a database

# Intent handlers
def handle_investment_advice(parameters, contexts, language):
    """Handle investment advice requests"""
    investment_type = parameters.get('investment_type', '')
    amount = parameters.get('amount', 0)
    risk_level = parameters.get('risk_level', 'medium')
    
    # Get user profile from context if available
    user_profile = contexts.get('userprofile', {})
    user_id = user_profile.get('user_id')
    
    try:
        # Get stock recommendations based on parameters
        if investment_type == 'stocks':
            stock_data = nse_api.get_top_performing_stocks(limit=5)
            recommendations = portfolio_ai.recommend_stocks(
                amount=amount, 
                risk_level=risk_level,
                user_id=user_id
            )
            
            # Format response based on language
            if language == 'swahili':
                fulfillment_text = f"Hapa kuna mapendekezo ya hisa kulingana na mapendeleo yako: {', '.join(recommendations)}"
            else:
                fulfillment_text = f"Here are stock recommendations based on your preferences: {', '.join(recommendations)}"
                
            # Create rich response with stock cards
            fulfillment_messages = [
                {
                    "card": {
                        "title": "Investment Recommendations",
                        "subtitle": f"For KES {amount} investment with {risk_level} risk",
                        "imageUri": "https://pesaguru.com/assets/images/stock_chart.png",
                        "buttons": [
                            {
                                "text": "View Details",
                                "postback": "https://pesaguru.com/investments/details"
                            }
                        ]
                    }
                }
            ]
            
            for stock in recommendations[:3]:
                fulfillment_messages.append({
                    "card": {
                        "title": stock,
                        "subtitle": "NSE Stock",
                        "imageUri": f"https://pesaguru.com/assets/images/stocks/{stock.lower()}.png",
                        "buttons": [
                            {
                                "text": "Buy",
                                "postback": f"https://pesaguru.com/stocks/buy/{stock}"
                            }
                        ]
                    }
                })
                
            return create_response(fulfillment_text, fulfillment_messages)
            
        elif investment_type == 'bonds':
            bond_data = cbk_api.get_treasury_bonds()
            recommendations = portfolio_ai.recommend_bonds(amount, risk_level)
            
            if language == 'swahili':
                fulfillment_text = f"Hapa kuna mapendekezo ya hati za serikali: {', '.join(recommendations)}"
            else:
                fulfillment_text = f"Here are treasury bond recommendations: {', '.join(recommendations)}"
            
            return create_response(fulfillment_text)
            
        elif investment_type == 'mutual_funds':
            fund_data = market_data_api.get_mutual_funds()
            recommendations = portfolio_ai.recommend_mutual_funds(amount, risk_level)
            
            if language == 'swahili':
                fulfillment_text = f"Mapendekezo ya fedha za pamoja: {', '.join(recommendations)}"
            else:
                fulfillment_text = f"Mutual fund recommendations: {', '.join(recommendations)}"
            
            return create_response(fulfillment_text)
            
        else:
            # General investment advice if no specific type mentioned
            if language == 'swahili':
                fulfillment_text = "Ningependekeza upate ushauri wa kifedha kulingana na malengo yako ya kifedha na kiwango cha hatari unachoweza kuvumilia."
            else:
                fulfillment_text = "I would recommend getting personalized investment advice based on your financial goals and risk tolerance."
            
            return create_response(fulfillment_text)
            
    except Exception as e:
        logger.error(f"Error in investment advice handler: {str(e)}")
        if language == 'swahili':
            return create_response("Samahani, kumekuwa na hitilafu katika kupata mapendekezo ya uwekezaji.")
        else:
            return create_response("Sorry, there was an error fetching investment recommendations.")

def handle_loan_comparison(parameters, contexts, language):
    """Handle loan comparison requests"""
    loan_type = parameters.get('loan_type', '')
    loan_amount = parameters.get('amount', 0)
    loan_term = parameters.get('duration', {}).get('amount', 12)  # Default to 12 months
    
    try:
        if loan_type == 'personal':
            loan_options = market_data_api.get_personal_loan_rates()
            
            # Format response
            if language == 'swahili':
                fulfillment_text = f"Viwango vya mikopo ya binafsi kwa KES {loan_amount} kwa miezi {loan_term}:\n"
            else:
                fulfillment_text = f"Personal loan rates for KES {loan_amount} for {loan_term} months:\n"
                
            # Format loan options into a readable format
            for provider, details in loan_options.items():
                interest_rate = details.get('interest_rate', 0)
                monthly_payment = (loan_amount * (interest_rate/100/12) * (1 + interest_rate/100/12)**(loan_term)) / ((1 + interest_rate/100/12)**(loan_term) - 1)
                
                if language == 'swahili':
                    fulfillment_text += f"- {provider}: {interest_rate}% kwa mwaka, malipo ya kila mwezi KES {monthly_payment:.2f}\n"
                else:
                    fulfillment_text += f"- {provider}: {interest_rate}% per annum, monthly payment KES {monthly_payment:.2f}\n"
            
            # Add a recommendation
            cheapest_option = min(loan_options.items(), key=lambda x: x[1]['interest_rate'])
            if language == 'swahili':
                fulfillment_text += f"\nPendekezo: {cheapest_option[0]} ina kiwango cha chini zaidi cha riba."
            else:
                fulfillment_text += f"\nRecommendation: {cheapest_option[0]} has the lowest interest rate."
                
            return create_response(fulfillment_text)
            
        elif loan_type == 'mortgage':
            mortgage_options = market_data_api.get_mortgage_rates()
            
            # Format response
            if language == 'swahili':
                fulfillment_text = f"Viwango vya mikopo ya nyumba kwa KES {loan_amount}:\n"
            else:
                fulfillment_text = f"Mortgage rates for KES {loan_amount}:\n"
                
            # Format mortgage options
            for provider, details in mortgage_options.items():
                if language == 'swahili':
                    fulfillment_text += f"- {provider}: {details['interest_rate']}% kwa mwaka, muda wa miaka {details['max_term']}\n"
                else:
                    fulfillment_text += f"- {provider}: {details['interest_rate']}% per annum, maximum term {details['max_term']} years\n"
            
            return create_response(fulfillment_text)
            
        elif loan_type == 'mobile':
            # Get mobile loan options from M-Pesa API
            mobile_loan_options = mpesa_api.get_loan_products()
            
            if language == 'swahili':
                fulfillment_text = f"Chaguo za mikopo ya simu kwa KES {loan_amount}:\n"
            else:
                fulfillment_text = f"Mobile loan options for KES {loan_amount}:\n"
                
            for product in mobile_loan_options:
                if language == 'swahili':
                    fulfillment_text += f"- {product['name']}: {product['interest_rate']}% kwa mwezi, muda wa kulipa siku {product['term']}\n"
                else:
                    fulfillment_text += f"- {product['name']}: {product['interest_rate']}% per month, repayment period {product['term']} days\n"
            
            return create_response(fulfillment_text)
            
        else:
            # General loan advice
            if language == 'swahili':
                return create_response("Tafadhali taja aina ya mkopo unaotaka kulinganisha (binafsi, nyumba, au simu).")
            else:
                return create_response("Please specify the type of loan you want to compare (personal, mortgage, or mobile).")
    
    except Exception as e:
        logger.error(f"Error in loan comparison handler: {str(e)}")
        if language == 'swahili':
            return create_response("Samahani, kumekuwa na hitilafu katika kupata taarifa za mkopo.")
        else:
            return create_response("Sorry, there was an error fetching loan information.")

def handle_market_data(parameters, contexts, language):
    """Handle market data requests"""
    data_type = parameters.get('data_type', '')
    stock_symbol = parameters.get('stock_symbol', '')
    
    try:
        if data_type == 'stock_price' and stock_symbol:
            # Get stock price data
            stock_data = nse_api.get_stock_price(stock_symbol)
            
            if not stock_data:
                if language == 'swahili':
                    return create_response(f"Samahani, sikuweza kupata bei ya hisa ya {stock_symbol}.")
                else:
                    return create_response(f"Sorry, I couldn't fetch the stock price for {stock_symbol}.")
            
            current_price = stock_data.get('current_price', 0)
            change = stock_data.get('change', 0)
            change_percent = stock_data.get('change_percent', 0)
            
            if language == 'swahili':
                if change >= 0:
                    fulfillment_text = f"Bei ya sasa ya {stock_symbol} ni KES {current_price}, imeongezeka kwa KES {change} ({change_percent}%) leo."
                else:
                    fulfillment_text = f"Bei ya sasa ya {stock_symbol} ni KES {current_price}, imepungua kwa KES {abs(change)} ({abs(change_percent)}%) leo."
            else:
                if change >= 0:
                    fulfillment_text = f"The current price of {stock_symbol} is KES {current_price}, up KES {change} ({change_percent}%) today."
                else:
                    fulfillment_text = f"The current price of {stock_symbol} is KES {current_price}, down KES {abs(change)} ({abs(change_percent)}%) today."
            
            # Create rich response with stock chart
            fulfillment_messages = [
                {
                    "card": {
                        "title": f"{stock_symbol} Stock Price",
                        "subtitle": f"KES {current_price} ({'+' if change >= 0 else ''}{change_percent}%)",
                        "imageUri": f"https://pesaguru.com/api/charts/stock/{stock_symbol}",
                        "buttons": [
                            {
                                "text": "View Details",
                                "postback": f"https://pesaguru.com/stocks/{stock_symbol}"
                            },
                            {
                                "text": "Buy/Sell",
                                "postback": f"https://pesaguru.com/stocks/trade/{stock_symbol}"
                            }
                        ]
                    }
                }
            ]
            
            return create_response(fulfillment_text, fulfillment_messages)
            
        elif data_type == 'market_index':
            # Get NSE index data
            index_data = nse_api.get_market_indices()
            
            if language == 'swahili':
                fulfillment_text = "Viwango vya sasa vya soko:\n"
            else:
                fulfillment_text = "Current market indices:\n"
                
            for index_name, index_value in index_data.items():
                change = index_value.get('change', 0)
                change_percent = index_value.get('change_percent', 0)
                
                if language == 'swahili':
                    fulfillment_text += f"- {index_name}: {index_value['value']}, {'imeongezeka' if change >= 0 else 'imepungua'} kwa {abs(change)} ({abs(change_percent)}%)\n"
                else:
                    fulfillment_text += f"- {index_name}: {index_value['value']}, {'up' if change >= 0 else 'down'} {abs(change)} ({abs(change_percent)}%)\n"
            
            return create_response(fulfillment_text)
            
        elif data_type == 'interest_rates':
            # Get interest rate data from Central Bank
            interest_data = cbk_api.get_interest_rates()
            
            if language == 'swahili':
                fulfillment_text = "Viwango vya riba vya sasa:\n"
            else:
                fulfillment_text = "Current interest rates:\n"
                
            for rate_name, rate_value in interest_data.items():
                if language == 'swahili':
                    fulfillment_text += f"- {rate_name}: {rate_value}%\n"
                else:
                    fulfillment_text += f"- {rate_name}: {rate_value}%\n"
            
            return create_response(fulfillment_text)
            
        else:
            # General market overview
            market_overview = market_analysis.get_market_overview()
            
            if language == 'swahili':
                fulfillment_text = "Muhtasari wa soko la sasa:\n"
                fulfillment_text += f"- NSE 20: {market_overview['nse20']['value']}, {'imeongezeka' if market_overview['nse20']['change'] >= 0 else 'imepungua'} kwa {abs(market_overview['nse20']['change'])}%\n"
                fulfillment_text += f"- Hisa zinazofanya vizuri: {', '.join(market_overview['top_performers'])}\n"
                fulfillment_text += f"- Hisa zinazofanya vibaya: {', '.join(market_overview['worst_performers'])}\n"
            else:
                fulfillment_text = "Current market overview:\n"
                fulfillment_text += f"- NSE 20: {market_overview['nse20']['value']}, {'up' if market_overview['nse20']['change'] >= 0 else 'down'} {abs(market_overview['nse20']['change'])}%\n"
                fulfillment_text += f"- Top performers: {', '.join(market_overview['top_performers'])}\n"
                fulfillment_text += f"- Worst performers: {', '.join(market_overview['worst_performers'])}\n"
            
            return create_response(fulfillment_text)
            
    except Exception as e:
        logger.error(f"Error in market data handler: {str(e)}")
        if language == 'swahili':
            return create_response("Samahani, kumekuwa na hitilafu katika kupata data ya soko.")
        else:
            return create_response("Sorry, there was an error fetching market data.")

def handle_risk_assessment(parameters, contexts, language):
    """Handle risk assessment requests"""
    # Extract parameters for risk assessment
    investment_horizon = parameters.get('investment_horizon', 'medium')
    investment_purpose = parameters.get('investment_purpose', '')
    existing_investments = parameters.get('existing_investments', [])
    
    try:
        # Get user profile from context if available
        user_profile = contexts.get('userprofile', {})
        user_id = user_profile.get('user_id')
        
        # Perform risk assessment
        risk_profile = risk_evaluator.assess_risk_profile(
            investment_horizon=investment_horizon,
            investment_purpose=investment_purpose,
            existing_investments=existing_investments,
            user_id=user_id
        )
        
        # Format response
        if language == 'swahili':
            fulfillment_text = f"Tathmini ya hatari yako:\n"
            fulfillment_text += f"- Kiwango cha hatari: {risk_profile['risk_level']}\n"
            fulfillment_text += f"- Mapendekezo ya mali: {risk_profile['asset_allocation']}\n"
            fulfillment_text += f"- Maelekezo: {risk_profile['guidance']}\n"
        else:
            fulfillment_text = f"Your risk assessment:\n"
            fulfillment_text += f"- Risk level: {risk_profile['risk_level']}\n"
            fulfillment_text += f"- Recommended asset allocation: {risk_profile['asset_allocation']}\n"
            fulfillment_text += f"- Guidance: {risk_profile['guidance']}\n"
        
        # Create rich response
        fulfillment_messages = [
            {
                "card": {
                    "title": "Risk Assessment Results",
                    "subtitle": f"Risk Level: {risk_profile['risk_level']}",
                    "imageUri": f"https://pesaguru.com/assets/images/risk/{risk_profile['risk_level'].lower()}.png",
                    "buttons": [
                        {
                            "text": "View Detailed Report",
                            "postback": "https://pesaguru.com/risk-assessment/report"
                        },
                        {
                            "text": "Get Investment Recommendations",
                            "postback": "https://pesaguru.com/investments/recommendations"
                        }
                    ]
                }
            }
        ]
        
        return create_response(fulfillment_text, fulfillment_messages)
        
    except Exception as e:
        logger.error(f"Error in risk assessment handler: {str(e)}")
        if language == 'swahili':
            return create_response("Samahani, kumekuwa na hitilafu katika kufanya tathmini ya hatari.")
        else:
            return create_response("Sorry, there was an error performing the risk assessment.")

def handle_budget_planning(parameters, contexts, language):
    """Handle budget planning requests"""
    income = parameters.get('income', 0)
    expense_categories = parameters.get('expense_categories', [])
    
    try:
        # Generate budget recommendations
        budget_plan = market_analysis.generate_budget_plan(income, expense_categories)
        
        # Format response
        if language == 'swahili':
            fulfillment_text = f"Mpango wa bajeti kwa mapato ya KES {income}:\n"
            for category, amount in budget_plan.items():
                fulfillment_text += f"- {category}: KES {amount}\n"
                
            fulfillment_text += "\nPendekezo: Unaweza kutumia 50% ya mapato yako kwa mahitaji ya msingi, 30% kwa matumizi ya kibinafsi, na kuweka 20% kama akiba."
        else:
            fulfillment_text = f"Budget plan for income of KES {income}:\n"
            for category, amount in budget_plan.items():
                fulfillment_text += f"- {category}: KES {amount}\n"
                
            fulfillment_text += "\nRecommendation: You can allocate 50% of your income to essential needs, 30% to personal spending, and save 20%."
        
        return create_response(fulfillment_text)
        
    except Exception as e:
        logger.error(f"Error in budget planning handler: {str(e)}")
        if language == 'swahili':
            return create_response("Samahani, kumekuwa na hitilafu katika kuunda mpango wa bajeti.")
        else:
            return create_response("Sorry, there was an error creating a budget plan.")

def handle_savings_goals(parameters, contexts, language):
    """Handle savings goal requests"""
    goal_type = parameters.get('goal_type', '')
    target_amount = parameters.get('target_amount', 0)
    time_frame = parameters.get('time_frame', {}).get('amount', 12)  # Default to 12 months
    
    try:
        # Calculate monthly savings requirement
        monthly_savings = target_amount / time_frame
        
        # Generate savings plan
        savings_plan = market_analysis.generate_savings_plan(
            goal_type=goal_type,
            target_amount=target_amount,
            time_frame=time_frame
        )
        
        # Format response
        if language == 'swahili':
            fulfillment_text = f"Mpango wa kuweka akiba kwa {goal_type}:\n"
            fulfillment_text += f"- Lengo: KES {target_amount}\n"
            fulfillment_text += f"- Muda: miezi {time_frame}\n"
            fulfillment_text += f"- Akiba ya kila mwezi inayohitajika: KES {monthly_savings:.2f}\n\n"
            fulfillment_text += "Mapendekezo:\n"
            
            for product, details in savings_plan.items():
                fulfillment_text += f"- {product}: {details['description']}, riba ya {details['interest_rate']}%\n"
        else:
            fulfillment_text = f"Savings plan for {goal_type}:\n"
            fulfillment_text += f"- Target: KES {target_amount}\n"
            fulfillment_text += f"- Time frame: {time_frame} months\n"
            fulfillment_text += f"- Required monthly savings: KES {monthly_savings:.2f}\n\n"
            fulfillment_text += "Recommendations:\n"
            
            for product, details in savings_plan.items():
                fulfillment_text += f"- {product}: {details['description']}, {details['interest_rate']}% interest\n"
        
        # Create rich response
        fulfillment_messages = [
            {
                "card": {
                    "title": f"{goal_type.title()} Savings Plan",
                    "subtitle": f"KES {target_amount} in {time_frame} months",
                    "imageUri": "https://pesaguru.com/assets/images/savings_goal.png",
                    "buttons": [
                        {
                            "text": "Create Savings Goal",
                            "postback": "https://pesaguru.com/savings/create-goal"
                        },
                        {
                            "text": "Explore Savings Products",
                            "postback": "https://pesaguru.com/savings/products"
                        }
                    ]
                }
            }
        ]
        
        return create_response(fulfillment_text, fulfillment_messages)
        
    except Exception as e:
        logger.error(f"Error in savings goals handler: {str(e)}")
        if language == 'swahili':
            return create_response("Samahani, kumekuwa na hitilafu katika kuunda mpango wa kuweka akiba.")
        else:
            return create_response("Sorry, there was an error creating a savings plan.")

def handle_financial_education(parameters, contexts, language):
    """Handle financial education requests"""
    topic = parameters.get('finance_topic', '')
    
    try:
        # Get educational content from chatbot service
        education_content = chatbot_service.get_financial_education_content(topic, language)
        
        if not education_content:
            if language == 'swahili':
                return create_response(f"Samahani, sina taarifa kuhusu {topic} kwa sasa. Unaweza kuuliza swali lingine?")
            else:
                return create_response(f"Sorry, I don't have information about {topic} at the moment. Would you like to ask about something else?")
        
        # Format response
        if language == 'swahili':
            fulfillment_text = f"Kuhusu {topic}:\n\n{education_content['content']}"
            
            if education_content.get('resources'):
                fulfillment_text += "\n\nVyanzo zaidi:\n"
                for resource in education_content['resources']:
                    fulfillment_text += f"- {resource}\n"
        else:
            fulfillment_text = f"About {topic}:\n\n{education_content['content']}"
            
            if education_content.get('resources'):
                fulfillment_text += "\n\nAdditional resources:\n"
                for resource in education_content['resources']:
                    fulfillment_text += f"- {resource}\n"
        
        # Create rich response with educational content
        fulfillment_messages = [
            {
                "card": {
                    "title": f"Learn About {topic.title()}",
                    "subtitle": education_content.get('summary', ''),
                    "imageUri": education_content.get('image_url', ''),
                    "buttons": [
                        {
                            "text": "Learn More",
                            "postback": education_content.get('learn_more_url', '')
                        },
                        {
                            "text": "Watch Tutorial",
                            "postback": education_content.get('video_url', '')
                        }
                    ]
                }
            }
        ]
        
        return create_response(fulfillment_text, fulfillment_messages)
        
    except Exception as e:
        logger.error(f"Error in financial education handler: {str(e)}")
        if language == 'swahili':
            return create_response("Samahani, kumekuwa na hitilafu katika kupata maudhui ya elimu ya fedha.")
        else:
            return create_response("Sorry, there was an error fetching financial education content.")

def handle_crypto_trends(parameters, contexts, language):
    """Handle cryptocurrency trend requests"""
    crypto_name = parameters.get('crypto_name', '')
    
    try:
        if crypto_name:
            # Get specific cryptocurrency data
            crypto_data = crypto_api.get_crypto_price(crypto_name)
            
            if not crypto_data:
                if language == 'swahili':
                    return create_response(f"Samahani, sikuweza kupata data ya {crypto_name}.")
                else:
                    return create_response(f"Sorry, I couldn't fetch data for {crypto_name}.")
            
            price_kes = crypto_data.get('price_kes', 0)
            change_24h = crypto_data.get('change_24h', 0)
            
            if language == 'swahili':
                fulfillment_text = f"Bei ya sasa ya {crypto_name} ni KES {price_kes:,.2f}, {'imeongezeka' if change_24h >= 0 else 'imepungua'} kwa {abs(change_24h)}% katika masaa 24 yaliyopita."
            else:
                fulfillment_text = f"The current price of {crypto_name} is KES {price_kes:,.2f}, {'up' if change_24h >= 0 else 'down'} {abs(change_24h)}% in the last 24 hours."
                
            # Create rich response with crypto chart
            fulfillment_messages = [
                {
                    "card": {
                        "title": f"{crypto_name} Price",
                        "subtitle": f"KES {price_kes:,.2f} ({'+' if change_24h >= 0 else ''}{change_24h}%)",
                        "imageUri": f"https://pesaguru.com/api/charts/crypto/{crypto_name.lower()}",
                        "buttons": [
                            {
                                "text": "View Details",
                                "postback": f"https://pesaguru.com/crypto/{crypto_name.lower()}"
                            }
                        ]
                    }
                }
            ]
            
            return create_response(fulfillment_text, fulfillment_messages)
            
        else:
            # Get top cryptocurrencies
            top_cryptos = crypto_api.get_top_cryptocurrencies(limit=5)
            
            if language == 'swahili':
                fulfillment_text = "Mwelekeo wa sasa wa sarafu za kidijitali:\n"
            else:
                fulfillment_text = "Current cryptocurrency trends:\n"
                
            for crypto in top_cryptos:
                if language == 'swahili':
                    fulfillment_text += f"- {crypto['name']}: KES {crypto['price_kes']:,.2f}, {'imeongezeka' if crypto['change_24h'] >= 0 else 'imepungua'} kwa {abs(crypto['change_24h'])}%\n"
                else:
                    fulfillment_text += f"- {crypto['name']}: KES {crypto['price_kes']:,.2f}, {'up' if crypto['change_24h'] >= 0 else 'down'} {abs(crypto['change_24h'])}%\n"
            
            # Add market sentiment
            market_sentiment = crypto_api.get_market_sentiment()
            
            if language == 'swahili':
                fulfillment_text += f"\nHali ya soko: {market_sentiment['sentiment']}"
                fulfillment_text += f"\nMaoni: {market_sentiment['opinion']}"
            else:
                fulfillment_text += f"\nMarket sentiment: {market_sentiment['sentiment']}"
                fulfillment_text += f"\nOutlook: {market_sentiment['opinion']}"
                
            return create_response(fulfillment_text)
            
    except Exception as e:
        logger.error(f"Error in crypto trends handler: {str(e)}")
        if language == 'swahili':
            return create_response("Samahani, kumekuwa na hitilafu katika kupata mielekeo ya sarafu za kidijitali.")
        else:
            return create_response("Sorry, there was an error fetching cryptocurrency trends.")

def handle_forex_rates(parameters, contexts, language):
    """Handle forex exchange rate requests"""
    base_currency = parameters.get('base_currency', 'KES')
    target_currency = parameters.get('target_currency', 'USD')
    
    try:
        exchange_rate = forex_api.get_exchange_rate(base_currency, target_currency)
        
        if not exchange_rate:
            if language == 'swahili':
                return create_response(f"Samahani, sikuweza kupata viwango vya ubadilishaji kati ya {base_currency} na {target_currency}.")
            else:
                return create_response(f"Sorry, I couldn't fetch exchange rates between {base_currency} and {target_currency}.")
        
        # Format response
        if language == 'swahili':
            fulfillment_text = f"Kiwango cha sasa cha ubadilishaji:\n1 {base_currency} = {exchange_rate} {target_currency}"
            
            # Add trend information if available
            trend = forex_api.get_exchange_rate_trend(base_currency, target_currency)
            if trend:
                fulfillment_text += f"\n\nMwelekeo wa wiki iliyopita: {'imepanda' if trend > 0 else 'imeshuka'} kwa {abs(trend)}%"
        else:
            fulfillment_text = f"Current exchange rate:\n1 {base_currency} = {exchange_rate} {target_currency}"
            
            # Add trend information if available
            trend = forex_api.get_exchange_rate_trend(base_currency, target_currency)
            if trend:
                fulfillment_text += f"\n\nTrend over the past week: {'up' if trend > 0 else 'down'} {abs(trend)}%"
        
        # Create rich response with forex chart
        fulfillment_messages = [
            {
                "card": {
                    "title": f"{base_currency}/{target_currency} Exchange Rate",
                    "subtitle": f"1 {base_currency} = {exchange_rate} {target_currency}",
                    "imageUri": f"https://pesaguru.com/api/charts/forex/{base_currency.lower()}_{target_currency.lower()}",
                    "buttons": [
                        {
                            "text": "View Historical Rates",
                            "postback": f"https://pesaguru.com/forex/{base_currency.lower()}_{target_currency.lower()}"
                        }
                    ]
                }
            }
        ]
        
        return create_response(fulfillment_text, fulfillment_messages)
        
    except Exception as e:
        logger.error(f"Error in forex rates handler: {str(e)}")
        if language == 'swahili':
            return create_response("Samahani, kumekuwa na hitilafu katika kupata viwango vya ubadilishaji fedha.")
        else:
            return create_response("Sorry, there was an error fetching forex exchange rates.")

def handle_fallback(parameters, contexts, language):
    """Handle fallback intent when no other intent matches"""
    user_query = parameters.get('text', '')
    
    # Try to understand the query using sentiment analysis
    sentiment = sentiment_analyzer.analyze(user_query)
    
    # Generate a helpful fallback response
    if language == 'swahili':
        if sentiment == 'positive':
            fulfillment_text = "Samahani, sijaeleweka kikamilifu swali lako. Unaweza kuuliza kwa njia nyingine? Ninaweza kukusaidia kuhusu ushauri wa uwekezaji, kulinganisha mikopo, au data ya soko."
        elif sentiment == 'negative':
            fulfillment_text = "Pole kwa kutokufahamu swali lako. Ninajaribu kujifunza na kuboreka. Unaweza kuuliza kuhusu bajeti, kuweka akiba, au mikopo."
        else:
            fulfillment_text = "Samahani, sikuelewa kabisa. Ninaweza kukusaidia na ushauri wa kifedha, data ya soko, au mpango wa kuweka akiba. Unaweza kuuliza swali jipya?"
    else:
        if sentiment == 'positive':
            fulfillment_text = "I'm sorry, I didn't fully understand your question. Could you phrase it differently? I can help you with investment advice, loan comparisons, or market data."
        elif sentiment == 'negative':
            fulfillment_text = "I apologize for not understanding your query. I'm continuously learning and improving. You can ask me about budgeting, savings, or loans."
        else:
            fulfillment_text = "Sorry, I didn't quite get that. I can assist you with financial advice, market data, or savings plans. Would you like to try a different question?"
    
    # Suggest some possible topics
    suggestions = [
        "Investment advice",
        "Loan comparison",
        "Stock prices",
        "Savings goals",
        "Budget planning"
    ]
    
    if language == 'swahili':
        suggestions = [
            "Ushauri wa uwekezaji",
            "Kulinganisha mikopo",
            "Bei za hisa",
            "Malengo ya kuweka akiba",
            "Mpango wa bajeti"
        ]
    
    # Create quick replies
    fulfillment_messages = [
        {
            "quickReplies": {
                "title": fulfillment_text,
                "quickReplies": suggestions
            }
        }
    ]
    
    return create_response(fulfillment_text, fulfillment_messages)

# Main webhook handler
@app.route('/webhook', methods=['POST'])
@require_auth
def webhook():
    """Main webhook handler for Dialogflow requests"""
    try:
        # Get request data
        req = request.get_json(silent=True, force=True)
        logger.info(f"Webhook request: {json.dumps(req)}")
        
        # Extract session ID
        session_id = req.get('session', '').split('/')[-1]
        
        # Get intent name
        intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName', '')
        
        # Get original query text
        query_text = req.get('queryResult', {}).get('queryText', '')
        
        # Detect language (English or Swahili)
        language = detect_language(query_text)
        
        # Extract parameters and contexts
        parameters = extract_parameters(req)
        contexts = extract_contexts(req)
        
        # Get the appropriate handler for the intent
        handler = get_intent_handler(intent_name)
        
        # Process the intent and get response
        response = handler(parameters, contexts, language)
        
        # Log the interaction for analysis
        log_interaction(session_id, intent_name, parameters, language, response)
        
        logger.info(f"Webhook response: {json.dumps(response)}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({
            'fulfillmentText': 'Sorry, there was an error processing your request. Please try again later.'
        })

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))# Dialogflow webhook handler 
