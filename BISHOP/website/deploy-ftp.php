<?php
/**
 * BISHOP Website - FTP Deployment Script
 * 
 * This script automates the deployment process for the website to an FTP server.
 * It should be protected with a secret key to prevent unauthorized access.
 */

// Load configuration
require_once 'includes/config.php';

// Set error reporting
ini_set('display_errors', 1);
error_reporting(E_ALL);

// Set execution time limit (5 minutes)
set_time_limit(300);

// Secret key to prevent unauthorized access
$secretKey = 'your_secret_deployment_key';

// Check if running from CLI
$isCli = php_sapi_name() === 'cli';

// Check if secret key is provided when not in CLI mode
if (!$isCli && (!isset($_GET['key']) || $_GET['key'] !== $secretKey)) {
    header('HTTP/1.1 403 Forbidden');
    echo 'Access denied';
    exit;
}

// Log function
function logMessage($message) {
    global $isCli;
    
    $logLine = date('Y-m-d H:i:s') . ' - ' . $message;
    
    if ($isCli) {
        echo $logLine . PHP_EOL;
    } else {
        echo $logLine . "<br>\n";
        flush();
    }
    
    // Also log to file
    file_put_contents(__DIR__ . '/logs/deployment.log', $logLine . PHP_EOL, FILE_APPEND);
}

// Get FTP credentials from environment variables
$ftpHost = env('FTP_HOST', 'ftpupload.net');
$ftpUser = env('FTP_USER', '');
$ftpPass = env('FTP_PASS', '');
$ftpPort = (int)env('FTP_PORT', 21);
$ftpRoot = env('FTP_ROOT', '/htdocs');

// Check if FTP credentials are set
if (empty($ftpUser) || empty($ftpPass)) {
    logMessage('Error: FTP credentials are not set in .env file');
    exit(1);
}

// Start deployment
logMessage('Starting FTP deployment...');

// Create backup directory if it doesn't exist
$backupDir = __DIR__ . '/backups';
if (!file_exists($backupDir)) {
    mkdir($backupDir, 0755, true);
    logMessage('Created backup directory');
}

// Create logs directory if it doesn't exist
$logsDir = __DIR__ . '/logs';
if (!file_exists($logsDir)) {
    mkdir($logsDir, 0755, true);
    logMessage('Created logs directory');
}

// Create backup of current files
$backupFile = $backupDir . '/backup_' . date('Y-m-d_H-i-s') . '.zip';
$excludes = [
    'backups/*',
    'logs/*',
    'cache/*',
    '.env',
    '.git/*',
    'node_modules/*'
];

$excludeParams = '';
foreach ($excludes as $exclude) {
    $excludeParams .= ' -x "' . escapeshellarg(__DIR__ . '/' . $exclude) . '"';
}

$command = 'zip -r ' . escapeshellarg($backupFile) . ' ' . escapeshellarg(__DIR__) . $excludeParams;
exec($command, $output, $returnVar);

if ($returnVar !== 0) {
    logMessage('Warning: Failed to create backup: ' . implode("\n", $output));
    // Continue anyway
} else {
    logMessage('Created backup: ' . basename($backupFile));
}

// Connect to FTP server
logMessage('Connecting to FTP server: ' . $ftpHost);
$conn = ftp_connect($ftpHost, $ftpPort);

if (!$conn) {
    logMessage('Error: Could not connect to FTP server');
    exit(1);
}

// Login to FTP server
logMessage('Logging in to FTP server as: ' . $ftpUser);
$login = ftp_login($conn, $ftpUser, $ftpPass);

if (!$login) {
    logMessage('Error: Could not login to FTP server');
    ftp_close($conn);
    exit(1);
}

// Enable passive mode
ftp_pasv($conn, true);

// Create list of files to upload
logMessage('Creating list of files to upload...');
$filesToUpload = [];
$excludePatterns = [
    '/^\.env/',
    '/^\.git/',
    '/^backups\//',
    '/^logs\//',
    '/^cache\//',
    '/^node_modules\//',
    '/^\.htaccess$/',
    '/^deploy.*\.php$/',
    '/^composer\.json$/',
    '/^composer\.lock$/',
    '/^package\.json$/',
    '/^package-lock\.json$/',
    '/^README\.md$/'
];

function shouldExclude($file, $patterns) {
    foreach ($patterns as $pattern) {
        if (preg_match($pattern, $file)) {
            return true;
        }
    }
    return false;
}

function scanDirectory($dir, &$results, $baseDir = '', $excludePatterns = []) {
    $files = scandir($dir);
    
    foreach ($files as $file) {
        if ($file === '.' || $file === '..') {
            continue;
        }
        
        $path = $dir . '/' . $file;
        $relativePath = $baseDir . '/' . $file;
        
        if (shouldExclude($relativePath, $excludePatterns)) {
            continue;
        }
        
        if (is_dir($path)) {
            scanDirectory($path, $results, $relativePath, $excludePatterns);
        } else {
            $results[] = [
                'local_path' => $path,
                'remote_path' => $relativePath
            ];
        }
    }
}

scanDirectory(__DIR__, $filesToUpload, '', $excludePatterns);
logMessage('Found ' . count($filesToUpload) . ' files to upload');

// Create remote directories
logMessage('Creating remote directories...');
$directories = [];

foreach ($filesToUpload as $file) {
    $dir = dirname($file['remote_path']);
    if ($dir !== '.' && !in_array($dir, $directories)) {
        $directories[] = $dir;
    }
}

// Sort directories by depth to ensure parent directories are created first
usort($directories, function($a, $b) {
    return substr_count($a, '/') - substr_count($b, '/');
});

// Create directories on remote server
foreach ($directories as $dir) {
    $remotePath = $ftpRoot . $dir;
    
    // Try to change to directory to check if it exists
    if (@ftp_chdir($conn, $remotePath)) {
        // Directory exists, change back to root
        ftp_chdir($conn, $ftpRoot);
    } else {
        // Directory doesn't exist, create it
        $parts = explode('/', trim($dir, '/'));
        $path = $ftpRoot;
        
        foreach ($parts as $part) {
            $path .= '/' . $part;
            
            if (!@ftp_chdir($conn, $path)) {
                if (!@ftp_mkdir($conn, $path)) {
                    logMessage('Warning: Could not create directory: ' . $path);
                } else {
                    logMessage('Created directory: ' . $path);
                }
            }
            
            ftp_chdir($conn, $ftpRoot);
        }
    }
}

// Upload files
logMessage('Uploading files...');
$uploadedCount = 0;
$failedCount = 0;

foreach ($filesToUpload as $file) {
    $localPath = $file['local_path'];
    $remotePath = $ftpRoot . $file['remote_path'];
    
    // Upload file
    if (ftp_put($conn, $remotePath, $localPath, FTP_BINARY)) {
        $uploadedCount++;
        
        // Log every 10 files
        if ($uploadedCount % 10 === 0) {
            logMessage('Uploaded ' . $uploadedCount . ' files...');
        }
    } else {
        logMessage('Warning: Failed to upload file: ' . $file['remote_path']);
        $failedCount++;
    }
}

// Close FTP connection
ftp_close($conn);

// Log results
logMessage('Deployment completed!');
logMessage('Uploaded ' . $uploadedCount . ' files');

if ($failedCount > 0) {
    logMessage('Failed to upload ' . $failedCount . ' files');
}

// Clean up old backups (keep last 5)
$backups = glob($backupDir . '/backup_*.zip');
usort($backups, function($a, $b) {
    return filemtime($b) - filemtime($a);
});

$backupsToKeep = 5;

if (count($backups) > $backupsToKeep) {
    $backupsToDelete = array_slice($backups, $backupsToKeep);
    
    foreach ($backupsToDelete as $backup) {
        unlink($backup);
        logMessage('Deleted old backup: ' . basename($backup));
    }
}

logMessage('Deployment process completed successfully!');
exit(0);
