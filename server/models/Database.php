<?php
namespace App\Config;

class Database {
    private static $connection = null;
    
    /**
     * Get database connection
     * @return \PDO Database connection
     */
    public static function getConnection() {
        if (self::$connection === null) {
            $host = getenv('DB_HOST') ?: 'localhost';
            $dbname = getenv('DB_NAME') ?: 'pesaguru';
            $username = getenv('DB_USER') ?: 'root';
            $password = getenv('DB_PASS') ?: '';
            
            try {
                self::$connection = new \PDO(
                    "mysql:host=$host;dbname=$dbname;charset=utf8mb4",
                    $username,
                    $password,
                    [
                        \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
                        \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
                        \PDO::ATTR_EMULATE_PREPARES => false
                    ]
                );
            } catch (\PDOException $e) {
                // Log error
                error_log('Database connection error: ' . $e->getMessage());
                throw new \Exception('Database connection failed: ' . $e->getMessage());
            }
        }
        
        return self::$connection;
    }
}