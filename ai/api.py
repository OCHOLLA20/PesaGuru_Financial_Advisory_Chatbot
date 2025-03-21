from flask import Flask, request, jsonify
from services.chatbot_service import handle_chat_request

from services.market_analysis import handle_market_request
from services.risk_evaluation import handle_risk_evaluation
from services.portfolio_ai import handle_portfolio_ai_request

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to PesaGuru AI API"})

# Chatbot API Route
@app.route('/chatbot', methods=['POST'])
def chatbot_api():
    data = request.get_json()
    return handle_chat_request(data)

# Market Analysis API Route
@app.route('/market', methods=['POST'])
def market_api():
    data = request.get_json()
    return handle_market_request(data)

# Risk Evaluation API Route
@app.route('/risk', methods=['POST'])
def risk_api():
    data = request.get_json()
    return handle_risk_evaluation(data)

# AI Portfolio Recommendation API Route
@app.route('/portfolio-ai', methods=['POST'])
def portfolio_ai_api():
    data = request.get_json()
    return handle_portfolio_ai_request(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
