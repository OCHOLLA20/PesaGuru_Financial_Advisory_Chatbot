<?php

require_once '../models/FeedbackModel.php';

class FeedbackController {
    
    // Method to submit feedback
    public function submitFeedback($request) {
        // Validate the request data
        // Assuming $request is an associative array
        if (empty($request['feedback'])) {
            return json_encode(['error' => 'Feedback cannot be empty.']);
        }

        // Save feedback to the database (using FeedbackModel)
        $feedbackModel = new FeedbackModel();
        $result = $feedbackModel->saveFeedback($request['feedback']);

        if ($result) {
            return json_encode(['success' => 'Feedback submitted successfully.']);
        } else {
            return json_encode(['error' => 'Failed to submit feedback.']);
        }
    }

    // Method to get feedback
    public function getFeedback() {
        $feedbackModel = new FeedbackModel();
        $feedbacks = $feedbackModel->retrieveFeedback();

        return json_encode($feedbacks);
    }

    // Method to delete feedback
    public function deleteFeedback($id) {
        $feedbackModel = new FeedbackModel();
        $result = $feedbackModel->removeFeedback($id);

        if ($result) {
            return json_encode(['success' => 'Feedback deleted successfully.']);
        } else {
            return json_encode(['error' => 'Failed to delete feedback.']);
        }
    }
}

?>
