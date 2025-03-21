<?php

class Database {
    private $host;
    private $dbName;
    private $username;
    private $password;
    private $conn;
    
    /**
     * Database constructor
     */
    public function __construct() {
        $this->host = getenv('DB_HOST');
        $this->dbName = getenv('DB_NAME');
        $this->username = getenv('DB_USER');
        $this->password = getenv('DB_PASS');
    }
    
    /**
     * Get database connection
     * 
     * @return PDO Database connection
     */
    public function getConnection() {
        $this->conn = null;
        
        try {
            $this->conn = new PDO(
                "mysql:host={$this->host};dbname={$this->dbName};charset=utf8",
                $this->username,
                $this->password
            );
            
            // Set PDO error mode to exception
            $this->conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            
            // Use prepared statements
            $this->conn->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
            
            // Return values as associative arrays
            $this->conn->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
            
        } catch (PDOException $e) {
            if (DEBUG_MODE) {
                echo "Database Connection Error: " . $e->getMessage();
            } else {
                logApiError("Database Connection Error: " . $e->getMessage());
                sendErrorResponse("Database connection error. Please try again later.", 500);
            }
            die();
        }
        
        return $this->conn;
    }
}

// Create database connection
$database = new Database();
$db = $database->getConnection();