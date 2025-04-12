<?php
/**
 * BISHOP Website - Deployment Script
 * 
 * This script automates the deployment process for the website.
 * It should be protected with a secret key to prevent unauthorized access.
 */

// Set error reporting
ini_set('display_errors', 0);
error_reporting(0);

// Set execution time limit
set_time_limit(300);

// Secret key to prevent unauthorized access
$secretKey = 'your_secret_deployment_key';

// Check if secret key is provided
if (!isset($_GET['key']) || $_GET['key'] !== $secretKey) {
    header('HTTP/1.1 403 Forbidden');
    echo 'Access denied';
    exit;
}

// Log function
function logMessage($message) {
    echo date('Y-m-d H:i:s') . ' - ' . $message . "<br>\n";
    flush();
}

// Execute command function
function executeCommand($command) {
    $output = [];
    $returnVar = 0;
    
    exec($command . ' 2>&1', $output, $returnVar);
    
    return [
        'output' => $output,
        'status' => $returnVar
    ];
}

// Start deployment
logMessage('Starting deployment...');

// Create backup directory if it doesn't exist
$backupDir = __DIR__ . '/backups';
if (!file_exists($backupDir)) {
    mkdir($backupDir, 0755, true);
    logMessage('Created backup directory');
}

// Create backup of current files
$backupFile = $backupDir . '/backup_' . date('Y-m-d_H-i-s') . '.zip';
$result = executeCommand('zip -r ' . escapeshellarg($backupFile) . ' ' . escapeshellarg(__DIR__) . ' -x "' . escapeshellarg(__DIR__) . '/backups/*" -x "' . escapeshellarg(__DIR__) . '/logs/*" -x "' . escapeshellarg(__DIR__) . '/cache/*"');

if ($result['status'] !== 0) {
    logMessage('Failed to create backup: ' . implode("\n", $result['output']));
    exit;
}

logMessage('Created backup: ' . basename($backupFile));

// Pull latest changes from Git repository
$result = executeCommand('cd ' . escapeshellarg(__DIR__) . ' && git pull');

if ($result['status'] !== 0) {
    logMessage('Failed to pull latest changes: ' . implode("\n", $result['output']));
    exit;
}

logMessage('Pulled latest changes: ' . implode("\n", $result['output']));

// Install/update dependencies
$result = executeCommand('cd ' . escapeshellarg(__DIR__) . ' && composer install --no-dev --optimize-autoloader');

if ($result['status'] !== 0) {
    logMessage('Failed to install dependencies: ' . implode("\n", $result['output']));
    exit;
}

logMessage('Installed dependencies');

// Run database migrations
$result = executeCommand('cd ' . escapeshellarg(__DIR__) . ' && php migrate.php');

if ($result['status'] !== 0) {
    logMessage('Failed to run database migrations: ' . implode("\n", $result['output']));
    exit;
}

logMessage('Ran database migrations');

// Clear cache
$cacheDir = __DIR__ . '/cache';
if (file_exists($cacheDir)) {
    $result = executeCommand('rm -rf ' . escapeshellarg($cacheDir . '/*'));
    
    if ($result['status'] !== 0) {
        logMessage('Failed to clear cache: ' . implode("\n", $result['output']));
        exit;
    }
    
    logMessage('Cleared cache');
}

// Set file permissions
$result = executeCommand('cd ' . escapeshellarg(__DIR__) . ' && chmod -R 755 .');

if ($result['status'] !== 0) {
    logMessage('Failed to set file permissions: ' . implode("\n", $result['output']));
    exit;
}

logMessage('Set file permissions');

// Create required directories
$directories = [
    '/cache',
    '/logs',
    '/storage',
    '/storage/uploads',
    '/storage/temp'
];

foreach ($directories as $directory) {
    $dir = __DIR__ . $directory;
    
    if (!file_exists($dir)) {
        mkdir($dir, 0755, true);
        logMessage('Created directory: ' . $directory);
    }
}

// Set directory permissions
$result = executeCommand('cd ' . escapeshellarg(__DIR__) . ' && chmod -R 777 cache logs storage');

if ($result['status'] !== 0) {
    logMessage('Failed to set directory permissions: ' . implode("\n", $result['output']));
    exit;
}

logMessage('Set directory permissions');

// Run post-deployment script
$postDeployScript = __DIR__ . '/post-deploy.php';

if (file_exists($postDeployScript)) {
    include $postDeployScript;
    logMessage('Ran post-deployment script');
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

// Finish deployment
logMessage('Deployment completed successfully!');
