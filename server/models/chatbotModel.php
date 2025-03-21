<?php
class ChatbotModel {
    private $responses = [
        "hello" => "Hello! How can I assist you with your finances today?",
        "investment options" => "There are several investment options available, including stocks, bonds, real estate, and mutual funds.",
        "budgeting tips" => "A good budget involves tracking your income and expenses, setting saving goals, and cutting unnecessary costs.",
        "loan advice" => "When taking a loan, compare interest rates and ensure you can manage repayments without financial strain.",
        "thank you" => "You're welcome! Let me know if you need more financial guidance."
    ];

    // Process chatbot response
    public function getResponse($userMessage) {
        $userMessage = strtolower(trim($userMessage));

        foreach ($this->responses as $key => $response) {
            if (strpos($userMessage, $key) !== false) {
                return $response;
            }
        }

        return "I'm still learning. Could you provide more details about your question?";
    }
}
?>
