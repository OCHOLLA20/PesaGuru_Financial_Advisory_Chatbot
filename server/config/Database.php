<?php

namespace PesaGuru\Server\Config;

use PDO;
use PDOException;

/**
 * Database connection and query management class
 * 
 * This class provides methods for database operations in PesaGuru including
 * connection management, transaction handling, and query execution.
 */
class Database
{
    /**
     * PDO instance for database connection
     * @var PDO|null
     */
    private static $connection = null;
    
    /**
     * Database configuration settings
     * @var array|null
     */
    private static $config = null;
    
    /**
     * Private constructor to prevent direct instantiation
     */
    private function __construct()
    {
        // This is a static class, constructor is private
    }
    
    /**
     * Get database connection (creates one if it doesn't exist)
     * 
     * @return PDO Database connection
     * @throws PDOException If connection fails
     */
    public static function getConnection()
    {
        // If connection already exists, return it
        if (self::$connection !== null) {
            return self::$connection;
        }
        
        // Load configuration if not already loaded
        if (self::$config === null) {
            self::loadConfig();
        }
        
        try {
            // Create DSN string for database connection
            $dsn = sprintf(
                "mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4",
                self::$config['host'],
                self::$config['port'],
                self::$config['dbname']
            );
            
            // Set PDO options for secure connections
            $options = [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
                PDO::ATTR_PERSISTENT => true
            ];
            
            // Create new PDO connection
            self::$connection = new PDO(
                $dsn,
                self::$config['username'],
                self::$config['password'],
                $options
            );
            
            // Log successful connection
            error_log("Database connection established successfully");
            
            return self::$connection;
        } catch (PDOException $e) {
            // Log connection error
            error_log("Database connection failed: " . $e->getMessage());
            
            // Re-throw exception for handling by calling code
            throw new \Exception('Database connection failed: ' . $e->getMessage());
        }
    }
    
    /**
     * Load database configuration from environment or config file
     */
    private static function loadConfig()
    {
        // First try to load from environment variables
        $host = getenv('DB_HOST');
        $port = getenv('DB_PORT');
        $dbname = getenv('DB_NAME');
        $username = getenv('DB_USERNAME') ?: getenv('DB_USER');
        $password = getenv('DB_PASSWORD') ?: getenv('DB_PASS');
        
        // If environment variables are not set, load from .env file if it exists
        if (!$host || !$dbname || !$username) {
            self::loadFromDotEnv();
            
            // After loading .env, try environment variables again
            $host = getenv('DB_HOST');
            $port = getenv('DB_PORT');
            $dbname = getenv('DB_NAME');
            $username = getenv('DB_USERNAME') ?: getenv('DB_USER');
            $password = getenv('DB_PASSWORD') ?: getenv('DB_PASS');
        }
        
        // If still not set, use defaults (for development only)
        if (!$host) $host = 'localhost';
        if (!$port) $port = '3306';
        if (!$dbname) $dbname = 'pesaguru';
        if (!$username) $username = 'root';
        if (!$password) $password = '';
        
        // Set configuration
        self::$config = [
            'host' => $host,
            'port' => $port,
            'dbname' => $dbname,
            'username' => $username,
            'password' => $password
        ];
    }
    
    /**
     * Load environment variables from .env file
     */
    private static function loadFromDotEnv()
    {
        $envFile = __DIR__ . '/../../.env';
        
        if (file_exists($envFile)) {
            $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            
            foreach ($lines as $line) {
                // Skip comments
                if (strpos(trim($line), '#') === 0) {
                    continue;
                }
                
                // Parse variable assignment
                if (strpos($line, '=') !== false) {
                    list($name, $value) = explode('=', $line, 2);
                    $name = trim($name);
                    $value = trim($value);
                    
                    // Remove quotes if present
                    if (strpos($value, '"') === 0 && strrpos($value, '"') === strlen($value) - 1) {
                        $value = substr($value, 1, -1);
                    } elseif (strpos($value, "'") === 0 && strrpos($value, "'") === strlen($value) - 1) {
                        $value = substr($value, 1, -1);
                    }
                    
                    // Set environment variable
                    putenv("$name=$value");
                }
            }
        }
    }
    
    /**
     * Close the database connection
     */
    public static function closeConnection()
    {
        self::$connection = null;
    }
    
    /**
     * Begin a database transaction
     * 
     * @return bool Success status
     */
    public static function beginTransaction()
    {
        $connection = self::getConnection();
        return $connection->beginTransaction();
    }
    
    /**
     * Commit the active database transaction
     * 
     * @return bool Success status
     */
    public static function commit()
    {
        $connection = self::getConnection();
        return $connection->commit();
    }
    
    /**
     * Roll back the active database transaction
     * 
     * @return bool Success status
     */
    public static function rollBack()
    {
        $connection = self::getConnection();
        return $connection->rollBack();
    }
    
    /**
     * Create a prepared statement
     * 
     * @param string $sql SQL query with placeholders
     * @return \PDOStatement Prepared statement
     */
    public static function prepare($sql)
    {
        $connection = self::getConnection();
        return $connection->prepare($sql);
    }
    
    /**
     * Execute a query and return the result set
     * 
     * @param string $sql SQL query
     * @param array $params Optional parameters for prepared statement
     * @return array Query results
     */
    public static function query($sql, $params = [])
    {
        $connection = self::getConnection();
        $stmt = $connection->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll();
    }
    
    /**
     * Execute a query and return a single row
     * 
     * @param string $sql SQL query
     * @param array $params Optional parameters for prepared statement
     * @return array|false Single row or false if no results
     */
    public static function queryOne($sql, $params = [])
    {
        $connection = self::getConnection();
        $stmt = $connection->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetch();
    }
    
    /**
     * Execute a query and return a single value
     * 
     * @param string $sql SQL query
     * @param array $params Optional parameters for prepared statement
     * @return mixed|false Single value or false if no results
     */
    public static function queryValue($sql, $params = [])
    {
        $connection = self::getConnection();
        $stmt = $connection->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchColumn();
    }
    
    /**
     * Execute an INSERT, UPDATE, or DELETE query
     * 
     * @param string $sql SQL query
     * @param array $params Optional parameters for prepared statement
     * @return int Number of affected rows
     */
    public static function execute($sql, $params = [])
    {
        $connection = self::getConnection();
        $stmt = $connection->prepare($sql);
        $stmt->execute($params);
        return $stmt->rowCount();
    }
    
    /**
     * Get the last inserted ID
     * 
     * @param string|null $name Optional name of sequence object
     * @return string Last inserted ID
     */
    public static function lastInsertId($name = null)
    {
        $connection = self::getConnection();
        return $connection->lastInsertId($name);
    }
}