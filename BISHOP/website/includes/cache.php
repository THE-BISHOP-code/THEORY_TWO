<?php
/**
 * BISHOP Website - Cache Class
 * 
 * Provides caching capabilities for the website.
 */

class Cache {
    // Cache directory
    private static $cacheDir = '/cache';
    
    // Default cache lifetime in seconds
    private static $defaultLifetime = 3600; // 1 hour
    
    /**
     * Get cached data
     * 
     * @param string $key Cache key
     * @return mixed Cached data or null if not found
     */
    public static function get($key) {
        $cacheFile = self::getCacheFilePath($key);
        
        if (!file_exists($cacheFile)) {
            return null;
        }
        
        $data = file_get_contents($cacheFile);
        $cacheData = unserialize($data);
        
        // Check if cache has expired
        if ($cacheData['expires'] < time()) {
            self::delete($key);
            return null;
        }
        
        return $cacheData['data'];
    }
    
    /**
     * Set cached data
     * 
     * @param string $key Cache key
     * @param mixed $data Data to cache
     * @param int $lifetime Cache lifetime in seconds
     * @return bool True if data was cached, false otherwise
     */
    public static function set($key, $data, $lifetime = null) {
        $cacheDir = ROOT_PATH . self::$cacheDir;
        
        // Create cache directory if it doesn't exist
        if (!file_exists($cacheDir)) {
            mkdir($cacheDir, 0755, true);
        }
        
        $cacheFile = self::getCacheFilePath($key);
        
        // Set cache lifetime
        $lifetime = $lifetime ?? self::$defaultLifetime;
        
        // Prepare cache data
        $cacheData = [
            'key' => $key,
            'data' => $data,
            'created' => time(),
            'expires' => time() + $lifetime
        ];
        
        // Write cache file
        return file_put_contents($cacheFile, serialize($cacheData)) !== false;
    }
    
    /**
     * Delete cached data
     * 
     * @param string $key Cache key
     * @return bool True if cache was deleted, false otherwise
     */
    public static function delete($key) {
        $cacheFile = self::getCacheFilePath($key);
        
        if (file_exists($cacheFile)) {
            return unlink($cacheFile);
        }
        
        return true;
    }
    
    /**
     * Check if cache exists
     * 
     * @param string $key Cache key
     * @return bool True if cache exists, false otherwise
     */
    public static function exists($key) {
        $cacheFile = self::getCacheFilePath($key);
        
        if (!file_exists($cacheFile)) {
            return false;
        }
        
        $data = file_get_contents($cacheFile);
        $cacheData = unserialize($data);
        
        // Check if cache has expired
        if ($cacheData['expires'] < time()) {
            self::delete($key);
            return false;
        }
        
        return true;
    }
    
    /**
     * Clear all cached data
     * 
     * @return bool True if cache was cleared, false otherwise
     */
    public static function clear() {
        $cacheDir = ROOT_PATH . self::$cacheDir;
        
        if (!file_exists($cacheDir)) {
            return true;
        }
        
        $files = glob($cacheDir . '/*.cache');
        
        foreach ($files as $file) {
            unlink($file);
        }
        
        return true;
    }
    
    /**
     * Get cache file path
     * 
     * @param string $key Cache key
     * @return string Cache file path
     */
    private static function getCacheFilePath($key) {
        $cacheDir = ROOT_PATH . self::$cacheDir;
        $hash = md5($key);
        
        return $cacheDir . '/' . $hash . '.cache';
    }
    
    /**
     * Get cache statistics
     * 
     * @return array Cache statistics
     */
    public static function getStats() {
        $cacheDir = ROOT_PATH . self::$cacheDir;
        
        if (!file_exists($cacheDir)) {
            return [
                'total' => 0,
                'size' => 0,
                'expired' => 0,
                'valid' => 0
            ];
        }
        
        $files = glob($cacheDir . '/*.cache');
        $total = count($files);
        $size = 0;
        $expired = 0;
        $valid = 0;
        
        foreach ($files as $file) {
            $size += filesize($file);
            
            $data = file_get_contents($file);
            $cacheData = unserialize($data);
            
            if ($cacheData['expires'] < time()) {
                $expired++;
            } else {
                $valid++;
            }
        }
        
        return [
            'total' => $total,
            'size' => $size,
            'expired' => $expired,
            'valid' => $valid
        ];
    }
    
    /**
     * Clean expired cache
     * 
     * @return int Number of expired cache files deleted
     */
    public static function clean() {
        $cacheDir = ROOT_PATH . self::$cacheDir;
        
        if (!file_exists($cacheDir)) {
            return 0;
        }
        
        $files = glob($cacheDir . '/*.cache');
        $deleted = 0;
        
        foreach ($files as $file) {
            $data = file_get_contents($file);
            $cacheData = unserialize($data);
            
            if ($cacheData['expires'] < time()) {
                unlink($file);
                $deleted++;
            }
        }
        
        return $deleted;
    }
    
    /**
     * Remember a value
     * 
     * @param string $key Cache key
     * @param callable $callback Callback function to generate value
     * @param int $lifetime Cache lifetime in seconds
     * @return mixed Cached data or callback result
     */
    public static function remember($key, $callback, $lifetime = null) {
        $value = self::get($key);
        
        if ($value !== null) {
            return $value;
        }
        
        $value = $callback();
        self::set($key, $value, $lifetime);
        
        return $value;
    }
    
    /**
     * Set default cache lifetime
     * 
     * @param int $lifetime Cache lifetime in seconds
     */
    public static function setDefaultLifetime($lifetime) {
        self::$defaultLifetime = $lifetime;
    }
    
    /**
     * Get default cache lifetime
     * 
     * @return int Default cache lifetime in seconds
     */
    public static function getDefaultLifetime() {
        return self::$defaultLifetime;
    }
}
