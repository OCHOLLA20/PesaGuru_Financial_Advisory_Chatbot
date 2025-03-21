<?php

namespace PesaGuru\Utils;

class Logger
{
    /**
     * Log levels based on RFC 5424
     */
    const EMERGENCY = 'emergency';
    const ALERT     = 'alert';
    const CRITICAL  = 'critical';
    const ERROR     = 'error';
    const WARNING   = 'warning';
    const NOTICE    = 'notice';
    const INFO      = 'info';
    const DEBUG     = 'debug';

    /**
     * @var array Valid log levels and their severity (lower number = higher severity)
     */
    protected $validLevels = [
        self::EMERGENCY => 0,
        self::ALERT     => 1,
        self::CRITICAL  => 2,
        self::ERROR     => 3,
        self::WARNING   => 4,
        self::NOTICE    => 5,
        self::INFO      => 6,
        self::DEBUG     => 7
    ];

    /**
     * @var string The name of the logger (typically the component name)
     */
    protected $name;

    /**
     * @var string Directory where log files will be stored
     */
    protected $logDir;

    /**
     * @var string The minimum log level to record
     */
    protected $minLevel;

    /**
     * @var int Maximum log file size in bytes before rotation (default: 10MB)
     */
    protected $maxFileSize = 10485760;

    /**
     * @var int Maximum number of log files to keep when rotating
     */
    protected $maxFiles = 5;

    /**
     * @var bool Whether to include a timestamp in log entries
     */
    protected $includeTimestamp = true;

    /**
     * @var resource File handle for writing logs
     */
    protected $fileHandle = null;

    /**
     * @var string Current log file path
     */
    protected $currentLogFile;

    /**
     * Constructor
     *
     * @param string $name Logger name (typically component/module name)
     * @param string $logDir Directory to store log files (default: logs directory in project root)
     * @param string $minLevel Minimum log level to record (default: debug in dev, info in production)
     */
    public function __construct($name, $logDir = null, $minLevel = null)
    {
        $this->name = $name;

        // Set log directory
        if ($logDir === null) {
            $this->logDir = dirname(dirname(__FILE__)) . '/logs';
        } else {
            $this->logDir = rtrim($logDir, '/\\');
        }

        // Create log directory if it doesn't exist
        if (!file_exists($this->logDir)) {
            mkdir($this->logDir, 0755, true);
        }

        // Set minimum log level based on environment if not specified
        if ($minLevel === null) {
            $this->minLevel = $this->isProduction() ? self::INFO : self::DEBUG;
        } else {
            $this->minLevel = strtolower($minLevel);
        }

        // Validate and set min level
        if (!isset($this->validLevels[$this->minLevel])) {
            $this->minLevel = self::INFO;
        }

        // Set the current log file path
        $this->currentLogFile = $this->logDir . '/' . $this->name . '.log';
    }

    /**
     * Determine if running in production environment
     *
     * @return bool True if in production environment
     */
    protected function isProduction()
    {
        // Check for environment variable
        $env = getenv('APP_ENV');
        
        if ($env) {
            return strtolower($env) === 'production';
        }
        
        // Default to development environment
        return false;
    }

    /**
     * Destructor to ensure file handle is closed
     */
    public function __destruct()
    {
        $this->closeLogFile();
    }

    /**
     * Open the log file for writing
     *
     * @return bool Success status
     */
    protected function openLogFile()
    {
        if ($this->fileHandle) {
            return true;
        }

        // Check if log file needs rotation
        $this->rotateLogFileIfNeeded();

        // Open file handle for appending
        $this->fileHandle = @fopen($this->currentLogFile, 'a');
        
        if (!$this->fileHandle) {
            // If we can't open the log file, try to write to system temp directory
            $tempLogFile = sys_get_temp_dir() . '/pesaguru_' . $this->name . '.log';
            $this->fileHandle = @fopen($tempLogFile, 'a');
            
            if ($this->fileHandle) {
                $this->currentLogFile = $tempLogFile;
                return true;
            }
            
            return false;
        }
        
        return true;
    }

    /**
     * Close the log file
     */
    protected function closeLogFile()
    {
        if ($this->fileHandle) {
            fclose($this->fileHandle);
            $this->fileHandle = null;
        }
    }

    /**
     * Rotate log file if it exceeds the maximum size
     */
    protected function rotateLogFileIfNeeded()
    {
        if (!file_exists($this->currentLogFile)) {
            return;
        }

        // Check if file size exceeds max size
        if (filesize($this->currentLogFile) < $this->maxFileSize) {
            return;
        }

        // Close file if it's open
        $this->closeLogFile();

        // Remove oldest log file if we've reached max files
        $oldestLog = $this->logDir . '/' . $this->name . '.' . $this->maxFiles . '.log';
        if (file_exists($oldestLog)) {
            @unlink($oldestLog);
        }

        // Shift existing log files
        for ($i = $this->maxFiles - 1; $i >= 1; $i--) {
            $oldFile = $this->logDir . '/' . $this->name . '.' . $i . '.log';
            $newFile = $this->logDir . '/' . $this->name . '.' . ($i + 1) . '.log';
            
            if (file_exists($oldFile)) {
                @rename($oldFile, $newFile);
            }
        }

        // Rename current log to .1.log
        @rename($this->currentLogFile, $this->logDir . '/' . $this->name . '.1.log');
    }

    /**
     * Format a log message with timestamp, level, and context
     *
     * @param string $level Log level
     * @param string $message Log message
     * @param array $context Additional context data
     * @return string Formatted log message
     */
    protected function formatLogMessage($level, $message, array $context = [])
    {
        $output = '';
        
        // Add timestamp if enabled
        if ($this->includeTimestamp) {
            $output .= '[' . date('Y-m-d H:i:s') . '] ';
        }
        
        // Add log level
        $output .= '[' . strtoupper($level) . '] ';
        
        // Add message with context placeholders replaced
        $output .= $this->interpolate($message, $context);
        
        // If there are additional context elements, add them as JSON
        $extraContext = array_diff_key($context, array_flip(array_keys(array_filter($context, 'is_scalar'))));
        if (!empty($extraContext)) {
            $output .= ' ' . json_encode($extraContext, JSON_UNESCAPED_SLASHES);
        }
        
        return $output;
    }

    /**
     * Replace placeholders in the message with context values
     *
     * @param string $message Message with placeholders
     * @param array $context Values to replace placeholders
     * @return string Interpolated message
     */
    protected function interpolate($message, array $context = [])
    {
        // Build a replacement array with braces around the context keys
        $replace = [];
        foreach ($context as $key => $val) {
            // Skip non-scalar values as they will be encoded as JSON
            if (!is_scalar($val) && !is_null($val)) {
                continue;
            }
            
            // Format null, boolean, and other scalar values
            if (is_null($val)) {
                $val = 'null';
            } elseif (is_bool($val)) {
                $val = $val ? 'true' : 'false';
            }
            
            $replace['{' . $key . '}'] = $val;
        }
        
        // Replace placeholders with values
        return strtr($message, $replace);
    }

    /**
     * Write a message to the log file
     *
     * @param string $level Log level
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool Success status
     */
    public function log($level, $message, array $context = [])
    {
        // Normalize level to lowercase
        $level = strtolower($level);
        
        // Skip if level is not valid or below minimum level
        if (!isset($this->validLevels[$level]) || 
            $this->validLevels[$level] > $this->validLevels[$this->minLevel]) {
            return false;
        }
        
        // Format the log message
        $formattedMessage = $this->formatLogMessage($level, $message, $context) . PHP_EOL;
        
        // Try to open log file
        if (!$this->openLogFile()) {
            // If we can't open the log file, try to use error_log as fallback
            error_log($formattedMessage);
            return false;
        }
        
        // Write to log file
        $result = fwrite($this->fileHandle, $formattedMessage);
        
        // Flush to ensure it's written immediately
        fflush($this->fileHandle);
        
        return ($result !== false);
    }

    /**
     * Set the maximum log file size before rotation
     *
     * @param int $sizeInBytes Size in bytes
     * @return $this For method chaining
     */
    public function setMaxFileSize($sizeInBytes)
    {
        $this->maxFileSize = max(1024, (int)$sizeInBytes);
        return $this;
    }

    /**
     * Set the maximum number of rotated log files to keep
     *
     * @param int $maxFiles Maximum number of files
     * @return $this For method chaining
     */
    public function setMaxFiles($maxFiles)
    {
        $this->maxFiles = max(1, (int)$maxFiles);
        return $this;
    }

    /**
     * Set whether to include timestamps in log messages
     *
     * @param bool $include Whether to include timestamps
     * @return $this For method chaining
     */
    public function includeTimestamps($include = true)
    {
        $this->includeTimestamp = (bool)$include;
        return $this;
    }

    /**
     * Set the minimum log level
     *
     * @param string $level Minimum log level
     * @return $this For method chaining
     */
    public function setMinLevel($level)
    {
        $level = strtolower($level);
        
        if (isset($this->validLevels[$level])) {
            $this->minLevel = $level;
        }
        
        return $this;
    }

    /**
     * Log an emergency message (system is unusable)
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool Success status
     */
    public function emergency($message, array $context = [])
    {
        return $this->log(self::EMERGENCY, $message, $context);
    }

    /**
     * Log an alert message (action must be taken immediately)
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool Success status
     */
    public function alert($message, array $context = [])
    {
        return $this->log(self::ALERT, $message, $context);
    }

    /**
     * Log a critical message (critical conditions)
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool Success status
     */
    public function critical($message, array $context = [])
    {
        return $this->log(self::CRITICAL, $message, $context);
    }

    /**
     * Log an error message (error conditions)
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool Success status
     */
    public function error($message, array $context = [])
    {
        return $this->log(self::ERROR, $message, $context);
    }

    /**
     * Log a warning message (warning conditions)
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool Success status
     */
    public function warning($message, array $context = [])
    {
        return $this->log(self::WARNING, $message, $context);
    }

    /**
     * Log a notice message (normal but significant conditions)
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool Success status
     */
    public function notice($message, array $context = [])
    {
        return $this->log(self::NOTICE, $message, $context);
    }

    /**
     * Log an info message (informational messages)
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool Success status
     */
    public function info($message, array $context = [])
    {
        return $this->log(self::INFO, $message, $context);
    }

    /**
     * Log a debug message (debug-level messages)
     *
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool Success status
     */
    public function debug($message, array $context = [])
    {
        return $this->log(self::DEBUG, $message, $context);
    }

    /**
     * Get all logs for the current logger within a specified time period
     *
     * @param int $hours Number of hours to look back
     * @return array Log entries
     */
    public function getRecentLogs($hours = 24)
    {
        $logs = [];
        $logFiles = [$this->currentLogFile];
        
        // Include rotated log files
        for ($i = 1; $i <= $this->maxFiles; $i++) {
            $rotatedLog = $this->logDir . '/' . $this->name . '.' . $i . '.log';
            if (file_exists($rotatedLog)) {
                $logFiles[] = $rotatedLog;
            }
        }
        
        // Get cutoff timestamp
        $cutoffTime = time() - ($hours * 3600);
        
        // Process log files
        foreach ($logFiles as $file) {
            if (!file_exists($file)) {
                continue;
            }
            
            $handle = @fopen($file, 'r');
            if (!$handle) {
                continue;
            }
            
            while (($line = fgets($handle)) !== false) {
                // Parse timestamp from log line if present
                if (preg_match('/^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]/', $line, $matches)) {
                    $timestamp = strtotime($matches[1]);
                    
                    // Skip if older than cutoff
                    if ($timestamp < $cutoffTime) {
                        continue;
                    }
                    
                    $logs[] = $line;
                } else {
                    // If no timestamp, include the line anyway
                    $logs[] = $line;
                }
            }
            
            fclose($handle);
        }
        
        return $logs;
    }
}