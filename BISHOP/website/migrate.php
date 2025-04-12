<?php
/**
 * BISHOP Website - Database Migration Script
 * 
 * This script runs database migrations to keep the database schema up to date.
 */

// Load configuration
require_once 'includes/config.php';

// Set error reporting
ini_set('display_errors', 1);
error_reporting(E_ALL);

// Check if running from command line
$isCli = php_sapi_name() === 'cli';

// Output function
function output($message) {
    global $isCli;
    
    if ($isCli) {
        echo $message . PHP_EOL;
    } else {
        echo $message . "<br>\n";
        flush();
    }
}

// Get database connection
$db = db_connect();

// Create migrations table if it doesn't exist
$db->exec("
    CREATE TABLE IF NOT EXISTS migrations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        migration VARCHAR(255) NOT NULL,
        batch INT NOT NULL,
        created_at DATETIME NOT NULL
    )
");

output('Migrations table created or already exists');

// Get all migration files
$migrationFiles = glob('db/migrations/*.sql');
sort($migrationFiles);

if (empty($migrationFiles)) {
    output('No migration files found');
    exit;
}

// Get already run migrations
$stmt = $db->query("SELECT migration FROM migrations");
$ranMigrations = $stmt->fetchAll(PDO::FETCH_COLUMN);

// Get current batch number
$stmt = $db->query("SELECT MAX(batch) FROM migrations");
$currentBatch = (int)$stmt->fetchColumn();
$nextBatch = $currentBatch + 1;

// Run migrations
$migrationsRun = 0;

foreach ($migrationFiles as $file) {
    $migration = basename($file);
    
    // Skip if migration has already been run
    if (in_array($migration, $ranMigrations)) {
        continue;
    }
    
    output("Running migration: $migration");
    
    // Get migration SQL
    $sql = file_get_contents($file);
    
    // Run migration in a transaction
    try {
        $db->beginTransaction();
        $db->exec($sql);
        
        // Record migration
        $stmt = $db->prepare("INSERT INTO migrations (migration, batch, created_at) VALUES (?, ?, NOW())");
        $stmt->execute([$migration, $nextBatch]);
        
        $db->commit();
        $migrationsRun++;
        
        output("Migration completed: $migration");
    } catch (PDOException $e) {
        $db->rollBack();
        output("Error running migration $migration: " . $e->getMessage());
        exit(1);
    }
}

if ($migrationsRun > 0) {
    output("$migrationsRun migrations run successfully");
} else {
    output('No migrations to run');
}

// Run seeds if specified
if (isset($argv[1]) && $argv[1] === '--seed') {
    output('Running seeds...');
    
    $seedFiles = glob('db/seeds/*.sql');
    sort($seedFiles);
    
    if (empty($seedFiles)) {
        output('No seed files found');
        exit;
    }
    
    foreach ($seedFiles as $file) {
        $seed = basename($file);
        output("Running seed: $seed");
        
        // Get seed SQL
        $sql = file_get_contents($file);
        
        // Run seed in a transaction
        try {
            $db->beginTransaction();
            $db->exec($sql);
            $db->commit();
            
            output("Seed completed: $seed");
        } catch (PDOException $e) {
            $db->rollBack();
            output("Error running seed $seed: " . $e->getMessage());
            exit(1);
        }
    }
    
    output('Seeds run successfully');
}

// Run specific migration if specified
if (isset($argv[1]) && $argv[1] === '--migration' && isset($argv[2])) {
    $migrationName = $argv[2];
    $migrationFile = "db/migrations/$migrationName.sql";
    
    if (!file_exists($migrationFile)) {
        output("Migration file not found: $migrationName");
        exit(1);
    }
    
    output("Running specific migration: $migrationName");
    
    // Get migration SQL
    $sql = file_get_contents($migrationFile);
    
    // Run migration in a transaction
    try {
        $db->beginTransaction();
        $db->exec($sql);
        
        // Record migration if not already run
        if (!in_array("$migrationName.sql", $ranMigrations)) {
            $stmt = $db->prepare("INSERT INTO migrations (migration, batch, created_at) VALUES (?, ?, NOW())");
            $stmt->execute(["$migrationName.sql", $nextBatch]);
        }
        
        $db->commit();
        
        output("Migration completed: $migrationName");
    } catch (PDOException $e) {
        $db->rollBack();
        output("Error running migration $migrationName: " . $e->getMessage());
        exit(1);
    }
}

// Rollback last batch if specified
if (isset($argv[1]) && $argv[1] === '--rollback') {
    output('Rolling back last batch...');
    
    // Get migrations from last batch
    $stmt = $db->prepare("SELECT migration FROM migrations WHERE batch = ?");
    $stmt->execute([$currentBatch]);
    $migrations = $stmt->fetchAll(PDO::FETCH_COLUMN);
    
    if (empty($migrations)) {
        output('No migrations to roll back');
        exit;
    }
    
    // Roll back migrations in reverse order
    $migrations = array_reverse($migrations);
    
    foreach ($migrations as $migration) {
        output("Rolling back migration: $migration");
        
        // Get rollback SQL
        $rollbackFile = "db/rollbacks/" . str_replace('.sql', '_rollback.sql', $migration);
        
        if (!file_exists($rollbackFile)) {
            output("Rollback file not found: $rollbackFile");
            exit(1);
        }
        
        $sql = file_get_contents($rollbackFile);
        
        // Run rollback in a transaction
        try {
            $db->beginTransaction();
            $db->exec($sql);
            
            // Remove migration record
            $stmt = $db->prepare("DELETE FROM migrations WHERE migration = ?");
            $stmt->execute([$migration]);
            
            $db->commit();
            
            output("Rollback completed: $migration");
        } catch (PDOException $e) {
            $db->rollBack();
            output("Error rolling back migration $migration: " . $e->getMessage());
            exit(1);
        }
    }
    
    output('Rollback completed successfully');
}

// Create migration if specified
if (isset($argv[1]) && $argv[1] === '--create' && isset($argv[2])) {
    $migrationName = $argv[2];
    $timestamp = date('Y_m_d_His');
    $migrationFile = "db/migrations/{$timestamp}_{$migrationName}.sql";
    $rollbackFile = "db/rollbacks/{$timestamp}_{$migrationName}_rollback.sql";
    
    // Create migrations directory if it doesn't exist
    if (!file_exists('db/migrations')) {
        mkdir('db/migrations', 0755, true);
    }
    
    // Create rollbacks directory if it doesn't exist
    if (!file_exists('db/rollbacks')) {
        mkdir('db/rollbacks', 0755, true);
    }
    
    // Create migration file
    $migrationContent = "-- Migration: $migrationName\n-- Created at: " . date('Y-m-d H:i:s') . "\n\n-- Your SQL here\n";
    file_put_contents($migrationFile, $migrationContent);
    
    // Create rollback file
    $rollbackContent = "-- Rollback for migration: $migrationName\n-- Created at: " . date('Y-m-d H:i:s') . "\n\n-- Your rollback SQL here\n";
    file_put_contents($rollbackFile, $rollbackContent);
    
    output("Migration created: $migrationFile");
    output("Rollback created: $rollbackFile");
}

// Show help if specified
if (isset($argv[1]) && $argv[1] === '--help') {
    output('Usage:');
    output('  php migrate.php                  Run all pending migrations');
    output('  php migrate.php --seed           Run all pending migrations and seeds');
    output('  php migrate.php --rollback       Rollback the last batch of migrations');
    output('  php migrate.php --migration name Run a specific migration');
    output('  php migrate.php --create name    Create a new migration');
    output('  php migrate.php --help           Show this help message');
}

exit(0);
