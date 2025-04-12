<?php
/**
 * BISHOP Website - Logout
 * 
 * Logs the user out and redirects to the homepage.
 */
require_once '../includes/config.php';

// Logout the user
logout();

// Redirect to homepage
header('Location: /');
exit;
