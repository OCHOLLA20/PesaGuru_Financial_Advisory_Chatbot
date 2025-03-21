// assets/js/services/chatbotService.js
import apiClient from '../apiClient.js';

export default {
  // Send message to chatbot
  async sendMessage(message) {
    return apiClient.post('/chatbot/message', { message });
  },
  
  // Get conversation history
  async getConversationHistory() {
    return apiClient.get('/chatbot/history');
  },
  
  // Save a conversation
  async saveConversation(conversationId, title) {
    return apiClient.post('/chatbot/save', { conversationId, title });
  },
  
  // Get saved conversations
  async getSavedConversations() {
    return apiClient.get('/chatbot/saved');
  },
  
  // Rate a chatbot response
  async rateResponse(responseId, rating, feedback) {
    return apiClient.post('/chatbot/rate', { responseId, rating, feedback });
  }
};