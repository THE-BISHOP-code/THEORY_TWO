<?php
/**
 * BISHOP Website - Security Class
 * 
 * Provides advanced security features for the website.
 */

class Security {
    /**
     * Generate a CSRF token
     * 
     * @return string CSRF token
     */
    public static function generateCsrfToken() {
        if (!isset($_SESSION['csrf_token'])) {
            $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
        }
        
        return $_SESSION['csrf_token'];
    }
    
    /**
     * Verify CSRF token
     * 
     * @param string $token CSRF token to verify
     * @return bool True if token is valid, false otherwise
     */
    public static function verifyCsrfToken($token) {
        if (!isset($_SESSION['csrf_token'])) {
            return false;
        }
        
        return hash_equals($_SESSION['csrf_token'], $token);
    }
    
    /**
     * Generate a JWT token
     * 
     * @param array $payload Token payload
     * @param int $expiry Token expiry time in seconds
     * @return string JWT token
     */
    public static function generateJwtToken($payload, $expiry = 3600) {
        $header = [
            'typ' => 'JWT',
            'alg' => 'HS256'
        ];
        
        $payload['iat'] = time();
        $payload['exp'] = time() + $expiry;
        
        $header_encoded = self::base64UrlEncode(json_encode($header));
        $payload_encoded = self::base64UrlEncode(json_encode($payload));
        
        $signature = hash_hmac('sha256', "$header_encoded.$payload_encoded", JWT_SECRET, true);
        $signature_encoded = self::base64UrlEncode($signature);
        
        return "$header_encoded.$payload_encoded.$signature_encoded";
    }
    
    /**
     * Verify JWT token
     * 
     * @param string $token JWT token to verify
     * @return array|false Token payload if valid, false otherwise
     */
    public static function verifyJwtToken($token) {
        $parts = explode('.', $token);
        
        if (count($parts) !== 3) {
            return false;
        }
        
        list($header_encoded, $payload_encoded, $signature_encoded) = $parts;
        
        $signature = self::base64UrlDecode($signature_encoded);
        $expected_signature = hash_hmac('sha256', "$header_encoded.$payload_encoded", JWT_SECRET, true);
        
        if (!hash_equals($expected_signature, $signature)) {
            return false;
        }
        
        $payload = json_decode(self::base64UrlDecode($payload_encoded), true);
        
        if (!$payload) {
            return false;
        }
        
        if (isset($payload['exp']) && $payload['exp'] < time()) {
            return false;
        }
        
        return $payload;
    }
    
    /**
     * Encrypt data
     * 
     * @param string $data Data to encrypt
     * @return string Encrypted data
     */
    public static function encrypt($data) {
        $iv = random_bytes(16);
        $encrypted = openssl_encrypt($data, 'AES-256-CBC', ENCRYPTION_KEY, 0, $iv);
        
        if ($encrypted === false) {
            return false;
        }
        
        return base64_encode($iv . $encrypted);
    }
    
    /**
     * Decrypt data
     * 
     * @param string $data Data to decrypt
     * @return string|false Decrypted data or false on failure
     */
    public static function decrypt($data) {
        $data = base64_decode($data);
        
        if ($data === false) {
            return false;
        }
        
        $iv = substr($data, 0, 16);
        $encrypted = substr($data, 16);
        
        return openssl_decrypt($encrypted, 'AES-256-CBC', ENCRYPTION_KEY, 0, $iv);
    }
    
    /**
     * Generate a secure random token
     * 
     * @param int $length Token length
     * @return string Random token
     */
    public static function generateToken($length = 32) {
        return bin2hex(random_bytes($length / 2));
    }
    
    /**
     * Hash a password
     * 
     * @param string $password Password to hash
     * @return string Hashed password
     */
    public static function hashPassword($password) {
        return password_hash($password, PASSWORD_ARGON2ID, [
            'memory_cost' => 65536,
            'time_cost' => 4,
            'threads' => 3
        ]);
    }
    
    /**
     * Verify a password
     * 
     * @param string $password Password to verify
     * @param string $hash Password hash
     * @return bool True if password is valid, false otherwise
     */
    public static function verifyPassword($password, $hash) {
        return password_verify($password, $hash);
    }
    
    /**
     * Sanitize input
     * 
     * @param string $input Input to sanitize
     * @return string Sanitized input
     */
    public static function sanitize($input) {
        return htmlspecialchars($input, ENT_QUOTES, 'UTF-8');
    }
    
    /**
     * Validate email
     * 
     * @param string $email Email to validate
     * @return bool True if email is valid, false otherwise
     */
    public static function validateEmail($email) {
        return filter_var($email, FILTER_VALIDATE_EMAIL) !== false;
    }
    
    /**
     * Validate URL
     * 
     * @param string $url URL to validate
     * @return bool True if URL is valid, false otherwise
     */
    public static function validateUrl($url) {
        return filter_var($url, FILTER_VALIDATE_URL) !== false;
    }
    
    /**
     * Check if request is AJAX
     * 
     * @return bool True if request is AJAX, false otherwise
     */
    public static function isAjax() {
        return isset($_SERVER['HTTP_X_REQUESTED_WITH']) && strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest';
    }
    
    /**
     * Check if request is HTTPS
     * 
     * @return bool True if request is HTTPS, false otherwise
     */
    public static function isHttps() {
        return isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on';
    }
    
    /**
     * Get client IP address
     * 
     * @return string Client IP address
     */
    public static function getClientIp() {
        $ip = '';
        
        if (isset($_SERVER['HTTP_CLIENT_IP'])) {
            $ip = $_SERVER['HTTP_CLIENT_IP'];
        } elseif (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
            $ip = $_SERVER['HTTP_X_FORWARDED_FOR'];
        } elseif (isset($_SERVER['REMOTE_ADDR'])) {
            $ip = $_SERVER['REMOTE_ADDR'];
        }
        
        return $ip;
    }
    
    /**
     * Get user agent
     * 
     * @return string User agent
     */
    public static function getUserAgent() {
        return isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : '';
    }
    
    /**
     * Base64 URL encode
     * 
     * @param string $data Data to encode
     * @return string Encoded data
     */
    private static function base64UrlEncode($data) {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }
    
    /**
     * Base64 URL decode
     * 
     * @param string $data Data to decode
     * @return string Decoded data
     */
    private static function base64UrlDecode($data) {
        return base64_decode(strtr($data, '-_', '+/'));
    }
    
    /**
     * Check for common security vulnerabilities
     * 
     * @return array Array of detected vulnerabilities
     */
    public static function checkVulnerabilities() {
        $vulnerabilities = [];
        
        // Check for XSS attempts
        foreach ($_GET as $key => $value) {
            if (is_string($value) && preg_match('/<script|javascript:|on[a-z]+\s*=|alert\s*\(|eval\s*\(/i', $value)) {
                $vulnerabilities[] = "Potential XSS attack detected in GET parameter: $key";
            }
        }
        
        foreach ($_POST as $key => $value) {
            if (is_string($value) && preg_match('/<script|javascript:|on[a-z]+\s*=|alert\s*\(|eval\s*\(/i', $value)) {
                $vulnerabilities[] = "Potential XSS attack detected in POST parameter: $key";
            }
        }
        
        // Check for SQL injection attempts
        foreach ($_GET as $key => $value) {
            if (is_string($value) && preg_match('/(\%27)|(\')|(\-\-)|(\%23)|(#)/i', $value)) {
                $vulnerabilities[] = "Potential SQL injection attack detected in GET parameter: $key";
            }
        }
        
        foreach ($_POST as $key => $value) {
            if (is_string($value) && preg_match('/(\%27)|(\')|(\-\-)|(\%23)|(#)/i', $value)) {
                $vulnerabilities[] = "Potential SQL injection attack detected in POST parameter: $key";
            }
        }
        
        // Check for file inclusion attempts
        foreach ($_GET as $key => $value) {
            if (is_string($value) && preg_match('/(\.\.\/|\.\.\\\\|\/etc\/passwd|c:\\\\windows)/i', $value)) {
                $vulnerabilities[] = "Potential file inclusion attack detected in GET parameter: $key";
            }
        }
        
        foreach ($_POST as $key => $value) {
            if (is_string($value) && preg_match('/(\.\.\/|\.\.\\\\|\/etc\/passwd|c:\\\\windows)/i', $value)) {
                $vulnerabilities[] = "Potential file inclusion attack detected in POST parameter: $key";
            }
        }
        
        return $vulnerabilities;
    }
    
    /**
     * Log security event
     * 
     * @param string $event Event description
     * @param string $level Event level (info, warning, error)
     * @return bool True if event was logged, false otherwise
     */
    public static function logSecurityEvent($event, $level = 'info') {
        $log_file = ROOT_PATH . '/logs/security.log';
        $log_dir = dirname($log_file);
        
        if (!file_exists($log_dir)) {
            mkdir($log_dir, 0755, true);
        }
        
        $log_entry = date('Y-m-d H:i:s') . ' [' . strtoupper($level) . '] ' . $event . ' - IP: ' . self::getClientIp() . ' - User Agent: ' . self::getUserAgent() . PHP_EOL;
        
        return file_put_contents($log_file, $log_entry, FILE_APPEND) !== false;
    }
}
