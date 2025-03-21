<?php
session_start();
require_once '../config/database.php'; // Include database connection

class Auth {
    private $db;

    public function __construct() {
        $this->db = new Database();
    }

    // User Registration
    public function register($name, $email, $password) {
        if ($this->userExists($email)) {
            return ['status' => 'error', 'message' => 'Email already registered.'];
        }

        $hashedPassword = password_hash($password, PASSWORD_BCRYPT);
        $query = "INSERT INTO users (name, email, password) VALUES (:name, :email, :password)";
        $stmt = $this->db->connect()->prepare($query);
        $stmt->bindParam(':name', $name);
        $stmt->bindParam(':email', $email);
        $stmt->bindParam(':password', $hashedPassword);

        if ($stmt->execute()) {
            return ['status' => 'success', 'message' => 'Registration successful. Please log in.'];
        } else {
            return ['status' => 'error', 'message' => 'Registration failed. Try again.'];
        }
    }

    // User Login
    public function login($email, $password) {
        $query = "SELECT * FROM users WHERE email = :email";
        $stmt = $this->db->connect()->prepare($query);
        $stmt->bindParam(':email', $email);
        $stmt->execute();

        if ($stmt->rowCount() > 0) {
            $user = $stmt->fetch(PDO::FETCH_ASSOC);
            if (password_verify($password, $user['password'])) {
                $_SESSION['user_id'] = $user['id'];
                $_SESSION['user_email'] = $user['email'];

                return ['status' => 'success', 'message' => 'Login successful.', 'user' => $user];
            } else {
                return ['status' => 'error', 'message' => 'Incorrect password.'];
            }
        } else {
            return ['status' => 'error', 'message' => 'User not found.'];
        }
    }

    // Check if user exists
    private function userExists($email) {
        $query = "SELECT * FROM users WHERE email = :email";
        $stmt = $this->db->connect()->prepare($query);
        $stmt->bindParam(':email', $email);
        $stmt->execute();
        return $stmt->rowCount() > 0;
    }

    // Logout function
    public function logout() {
        session_destroy();
        return ['status' => 'success', 'message' => 'Logged out successfully.'];
    }

    // Get logged-in user
    public function getUser() {
        if (isset($_SESSION['user_id'])) {
            $query = "SELECT * FROM users WHERE id = :id";
            $stmt = $this->db->connect()->prepare($query);
            $stmt->bindParam(':id', $_SESSION['user_id']);
            $stmt->execute();
            return $stmt->fetch(PDO::FETCH_ASSOC);
        }
        return null;
    }
}

// API Handling
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $auth = new Auth();

    if (isset($_POST['action'])) {
        switch ($_POST['action']) {
            case 'register':
                $name = $_POST['name'];
                $email = $_POST['email'];
                $password = $_POST['password'];
                echo json_encode($auth->register($name, $email, $password));
                break;

            case 'login':
                $email = $_POST['email'];
                $password = $_POST['password'];
                echo json_encode($auth->login($email, $password));
                break;

            case 'logout':
                echo json_encode($auth->logout());
                break;
        }
    }
}
?>

