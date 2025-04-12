<?php
/**
 * BISHOP Website - Logger Class
 * 
 * Provides advanced logging capabilities for the website.
 */

class Logger {
    // Log levels
    const DEBUG = 'DEBUG';
    const INFO = 'INFO';
    const WARNING = 'WARNING';
    const ERROR = 'ERROR';
    const CRITICAL = 'CRITICAL';
    
    // Log file paths
    private static $logFiles = [
        'general' => '/logs/general.log',
        'error' => '/logs/error.log',
        'security' => '/logs/security.log',
        'api' => '/logs/api.log',
        'auth' => '/logs/auth.log',
        'payment' => '/logs/payment.log'
    ];
    
    /**
     * Log a message
     * 
     * @param string $message Message to log
     * @param string $level Log level
     * @param string $category Log category
     * @return bool True if message was logged, false otherwise
     */
    public static function log($message, $level = self::INFO, $category = 'general') {
        // Get log file path
        $logFile = self::getLogFilePath($category);
        
        // Create log directory if it doesn't exist
        $logDir = dirname($logFile);
        if (!file_exists($logDir)) {
            mkdir($logDir, 0755, true);
        }
        
        // Format log entry
        $logEntry = self::formatLogEntry($message, $level);
        
        // Write to log file
        $result = file_put_contents($logFile, $logEntry, FILE_APPEND);
        
        // If error level is ERROR or CRITICAL, also log to error log
        if ($level === self::ERROR || $level === self::CRITICAL) {
            $errorLogFile = self::getLogFilePath('error');
            file_put_contents($errorLogFile, $logEntry, FILE_APPEND);
        }
        
        return $result !== false;
    }
    
    /**
     * Log a debug message
     * 
     * @param string $message Message to log
     * @param string $category Log category
     * @return bool True if message was logged, false otherwise
     */
    public static function debug($message, $category = 'general') {
        return self::log($message, self::DEBUG, $category);
    }
    
    /**
     * Log an info message
     * 
     * @param string $message Message to log
     * @param string $category Log category
     * @return bool True if message was logged, false otherwise
     */
    public static function info($message, $category = 'general') {
        return self::log($message, self::INFO, $category);
    }
    
    /**
     * Log a warning message
     * 
     * @param string $message Message to log
     * @param string $category Log category
     * @return bool True if message was logged, false otherwise
     */
    public static function warning($message, $category = 'general') {
        return self::log($message, self::WARNING, $category);
    }
    
    /**
     * Log an error message
     * 
     * @param string $message Message to log
     * @param string $category Log category
     * @return bool True if message was logged, false otherwise
     */
    public static function error($message, $category = 'general') {
        return self::log($message, self::ERROR, $category);
    }
    
    /**
     * Log a critical message
     * 
     * @param string $message Message to log
     * @param string $category Log category
     * @return bool True if message was logged, false otherwise
     */
    public static function critical($message, $category = 'general') {
        return self::log($message, self::CRITICAL, $category);
    }
    
    /**
     * Log an exception
     * 
     * @param Exception $exception Exception to log
     * @param string $category Log category
     * @return bool True if exception was logged, false otherwise
     */
    public static function exception($exception, $category = 'general') {
        $message = get_class($exception) . ': ' . $exception->getMessage() . ' in ' . $exception->getFile() . ' on line ' . $exception->getLine() . PHP_EOL;
        $message .= 'Stack trace: ' . PHP_EOL . $exception->getTraceAsString();
        
        return self::log($message, self::ERROR, $category);
    }
    
    /**
     * Log a database query
     * 
     * @param string $query SQL query
     * @param array $params Query parameters
     * @param float $executionTime Query execution time
     * @return bool True if query was logged, false otherwise
     */
    public static function query($query, $params = [], $executionTime = 0) {
        $message = 'Query: ' . $query . PHP_EOL;
        
        if (!empty($params)) {
            $message .= 'Parameters: ' . json_encode($params) . PHP_EOL;
        }
        
        $message .= 'Execution time: ' . number_format($executionTime, 4) . ' seconds';
        
        return self::log($message, self::DEBUG, 'database');
    }
    
    /**
     * Log an API request
     * 
     * @param string $method Request method
     * @param string $endpoint Request endpoint
     * @param array $params Request parameters
     * @param int $statusCode Response status code
     * @param array $response Response data
     * @param float $executionTime Request execution time
     * @return bool True if request was logged, false otherwise
     */
    public static function apiRequest($method, $endpoint, $params = [], $statusCode = 200, $response = [], $executionTime = 0) {
        $message = 'API Request: ' . $method . ' ' . $endpoint . PHP_EOL;
        
        if (!empty($params)) {
            $message .= 'Parameters: ' . json_encode($params) . PHP_EOL;
        }
        
        $message .= 'Status code: ' . $statusCode . PHP_EOL;
        
        if (!empty($response)) {
            $message .= 'Response: ' . json_encode($response) . PHP_EOL;
        }
        
        $message .= 'Execution time: ' . number_format($executionTime, 4) . ' seconds';
        
        $level = $statusCode >= 400 ? self::ERROR : self::INFO;
        
        return self::log($message, $level, 'api');
    }
    
    /**
     * Log an authentication event
     * 
     * @param string $event Event description
     * @param string $userId User ID
     * @param bool $success Whether the event was successful
     * @return bool True if event was logged, false otherwise
     */
    public static function auth($event, $userId = null, $success = true) {
        $message = 'Auth event: ' . $event . PHP_EOL;
        
        if ($userId !== null) {
            $message .= 'User ID: ' . $userId . PHP_EOL;
        }
        
        $message .= 'Success: ' . ($success ? 'Yes' : 'No') . PHP_EOL;
        $message .= 'IP: ' . Security::getClientIp() . PHP_EOL;
        $message .= 'User Agent: ' . Security::getUserAgent();
        
        $level = $success ? self::INFO : self::WARNING;
        
        return self::log($message, $level, 'auth');
    }
    
    /**
     * Log a payment event
     * 
     * @param string $event Event description
     * @param string $userId User ID
     * @param string $paymentId Payment ID
     * @param float $amount Payment amount
     * @param string $currency Payment currency
     * @param bool $success Whether the event was successful
     * @return bool True if event was logged, false otherwise
     */
    public static function payment($event, $userId, $paymentId, $amount, $currency, $success = true) {
        $message = 'Payment event: ' . $event . PHP_EOL;
        $message .= 'User ID: ' . $userId . PHP_EOL;
        $message .= 'Payment ID: ' . $paymentId . PHP_EOL;
        $message .= 'Amount: ' . $amount . ' ' . $currency . PHP_EOL;
        $message .= 'Success: ' . ($success ? 'Yes' : 'No');
        
        $level = $success ? self::INFO : self::ERROR;
        
        return self::log($message, $level, 'payment');
    }
    
    /**
     * Get log file path
     * 
     * @param string $category Log category
     * @return string Log file path
     */
    private static function getLogFilePath($category) {
        // If category doesn't exist, use general log
        if (!isset(self::$logFiles[$category])) {
            $category = 'general';
        }
        
        return ROOT_PATH . self::$logFiles[$category];
    }
    
    /**
     * Format log entry
     * 
     * @param string $message Message to log
     * @param string $level Log level
     * @return string Formatted log entry
     */
    private static function formatLogEntry($message, $level) {
        $timestamp = date('Y-m-d H:i:s');
        $ip = Security::getClientIp();
        $userId = isset($_SESSION['user_id']) ? $_SESSION['user_id'] : 'guest';
        
        return "[{$timestamp}] [{$level}] [IP: {$ip}] [User: {$userId}] {$message}" . PHP_EOL;
    }
    
    /**
     * Get all log files
     * 
     * @return array Log files
     */
    public static function getLogFiles() {
        $files = [];
        
        foreach (self::$logFiles as $category => $path) {
            $fullPath = ROOT_PATH . $path;
            
            if (file_exists($fullPath)) {
                $files[$category] = $fullPath;
            }
        }
        
        return $files;
    }
    
    /**
     * Get log file content
     * 
     * @param string $category Log category
     * @param int $lines Number of lines to get
     * @param bool $reverse Whether to reverse the order of lines
     * @return array Log file content
     */
    public static function getLogContent($category, $lines = 100, $reverse = true) {
        $logFile = self::getLogFilePath($category);
        
        if (!file_exists($logFile)) {
            return [];
        }
        
        $content = file($logFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        
        if ($reverse) {
            $content = array_reverse($content);
        }
        
        return array_slice($content, 0, $lines);
    }
    
    /**
     * Clear log file
     * 
     * @param string $category Log category
     * @return bool True if log file was cleared, false otherwise
     */
    public static function clearLog($category) {
        $logFile = self::getLogFilePath($category);
        
        if (!file_exists($logFile)) {
            return true;
        }
        
        return file_put_contents($logFile, '') !== false;
    }
    
    /**
     * Rotate log files
     * 
     * @param int $maxSize Maximum log file size in bytes
     * @param int $maxFiles Maximum number of log files to keep
     * @return bool True if log files were rotated, false otherwise
     */
    public static function rotateLogs($maxSize = 10485760, $maxFiles = 5) {
        $rotated = false;
        
        foreach (self::$logFiles as $category => $path) {
            $logFile = ROOT_PATH . $path;
            
            if (!file_exists($logFile)) {
                continue;
            }
            
            // Check if log file is too large
            if (filesize($logFile) > $maxSize) {
                // Rotate log files
                for ($i = $maxFiles - 1; $i > 0; $i--) {
                    $oldFile = $logFile . '.' . $i;
                    $newFile = $logFile . '.' . ($i + 1);
                    
                    if (file_exists($oldFile)) {
                        rename($oldFile, $newFile);
                    }
                }
                
                // Move current log file
                rename($logFile, $logFile . '.1');
                
                // Create new log file
                touch($logFile);
                
                $rotated = true;
            }
        }
        
        return $rotated;
    }
}
