<?php
/**
 * BISHOP Website - Login Page
 * 
 * Handles Discord OAuth login process.
 */
require_once 'includes/config.php';

// Check if user is already logged in
if (is_logged_in()) {
    // Redirect to dashboard or requested page
    $redirect = isset($_SESSION['redirect_after_login']) ? $_SESSION['redirect_after_login'] : '/dashboard/';
    unset($_SESSION['redirect_after_login']);
    header("Location: $redirect");
    exit;
}

// Check if this is a callback from Discord OAuth
if (isset($_GET['code'])) {
    // Process the login
    if (process_discord_login($_GET['code'])) {
        // Login successful
        $redirect = isset($_SESSION['redirect_after_login']) ? $_SESSION['redirect_after_login'] : '/dashboard/';
        unset($_SESSION['redirect_after_login']);
        header("Location: $redirect");
        exit;
    } else {
        // Login failed
        $error = 'Failed to authenticate with Discord. Please try again.';
    }
}

// If there was an error in the OAuth process
if (isset($_GET['error'])) {
    $error = 'Authentication canceled or failed. Please try again.';
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - <?php echo SITE_NAME; ?></title>
    
    <!-- Favicon -->
    <link rel="icon" href="/assets/img/favicon.ico">
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="/assets/css/style.css">
    
    <style>
        .login-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        .login-card {
            max-width: 500px;
            width: 100%;
            text-align: center;
            padding: 3rem;
        }
        
        .login-logo {
            margin-bottom: 2rem;
        }
        
        .login-logo img {
            max-width: 120px;
            margin-bottom: 1rem;
        }
        
        .login-title {
            margin-bottom: 1.5rem;
        }
        
        .login-subtitle {
            margin-bottom: 2rem;
            color: var(--text-secondary);
        }
        
        .discord-btn {
            background-color: #5865F2;
            color: white;
            padding: 1rem 2rem;
            border-radius: 0.5rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            text-decoration: none;
            margin-bottom: 1.5rem;
        }
        
        .discord-btn:hover {
            background-color: #4752c4;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(88, 101, 242, 0.4);
        }
        
        .discord-btn i {
            margin-right: 0.75rem;
            font-size: 1.25rem;
        }
        
        .login-footer {
            margin-top: 2rem;
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        
        .login-footer a {
            color: var(--accent-blue);
            text-decoration: none;
        }
        
        .login-footer a:hover {
            text-decoration: underline;
        }
        
        .error-message {
            background-color: rgba(231, 76, 60, 0.1);
            border-left: 4px solid var(--accent-red);
            padding: 1rem;
            margin-bottom: 2rem;
            text-align: left;
            color: var(--accent-red);
            border-radius: 0.25rem;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="glass-card login-card">
            <div class="login-logo">
                <img src="/assets/img/logo.png" alt="<?php echo SITE_NAME; ?> Logo">
                <h1><?php echo SITE_NAME; ?></h1>
            </div>
            
            <?php if (isset($error)): ?>
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i> <?php echo $error; ?>
                </div>
            <?php endif; ?>
            
            <h2 class="login-title">Login to Your Account</h2>
            <p class="login-subtitle">Connect with Discord to access your dashboard and manage your bot.</p>
            
            <a href="<?php echo get_discord_oauth_url(); ?>" class="discord-btn">
                <i class="fab fa-discord"></i> Login with Discord
            </a>
            
            <p>By logging in, you agree to our <a href="/terms.php">Terms of Service</a> and <a href="/privacy.php">Privacy Policy</a>.</p>
            
            <div class="login-footer">
                <p>Don't have an account? <a href="<?php echo get_discord_oauth_url(); ?>">Sign up with Discord</a></p>
                <p>Need help? <a href="/contact.php">Contact Support</a></p>
            </div>
        </div>
    </div>
</body>
</html>
