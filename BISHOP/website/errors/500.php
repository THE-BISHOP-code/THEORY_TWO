<?php
/**
 * BISHOP Website - 500 Error Page
 */
http_response_code(500);
require_once '../includes/config.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Error - <?php echo SITE_NAME; ?></title>
    
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
        .error-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        .error-content {
            max-width: 600px;
            text-align: center;
        }
        
        .error-code {
            font-size: 8rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, var(--accent-red), var(--accent-gold));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1;
        }
        
        .error-title {
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
        }
        
        .error-message {
            color: var(--text-secondary);
            margin-bottom: 2rem;
            font-size: 1.1rem;
        }
        
        .error-actions {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .error-image {
            max-width: 300px;
            margin: 0 auto 2rem;
        }
        
        .error-image img {
            width: 100%;
            height: auto;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header>
        <div class="container header-container">
            <a href="/" class="logo">
                <img src="/assets/img/logo.png" alt="<?php echo SITE_NAME; ?> Logo">
                <span><?php echo SITE_NAME; ?></span>
            </a>
            
            <nav>
                <ul>
                    <li><a href="/" class="<?php echo active_class('home'); ?>">Home</a></li>
                    <li><a href="/about.php" class="<?php echo active_class('about'); ?>">About</a></li>
                    <li><a href="/pricing.php" class="<?php echo active_class('pricing'); ?>">Pricing</a></li>
                    <li><a href="/contact.php" class="<?php echo active_class('contact'); ?>">Contact</a></li>
                    <?php if (is_logged_in()): ?>
                        <li><a href="/dashboard/" class="<?php echo active_class('dashboard'); ?>">Dashboard</a></li>
                    <?php else: ?>
                        <li><a href="<?php echo get_discord_oauth_url(); ?>" class="btn btn-primary">Login with Discord</a></li>
                    <?php endif; ?>
                </ul>
            </nav>
        </div>
    </header>
    
    <!-- Error Content -->
    <section class="error-container">
        <div class="container">
            <div class="glass-card">
                <div class="error-content">
                    <div class="error-image">
                        <img src="/assets/img/500-robot.svg" alt="500 Error">
                    </div>
                    <div class="error-code">500</div>
                    <h1 class="error-title">Server Error</h1>
                    <p class="error-message">Something went wrong on our servers. We're working to fix the issue as soon as possible.</p>
                    <div class="error-actions">
                        <a href="/" class="btn btn-primary">Go to Homepage</a>
                        <a href="/contact.php" class="btn btn-secondary">Contact Support</a>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <!-- Footer -->
    <footer>
        <div class="container">
            <div class="footer-grid">
                <div>
                    <div class="footer-logo">
                        <img src="/assets/img/logo.png" alt="<?php echo SITE_NAME; ?> Logo">
                        <?php echo SITE_NAME; ?>
                    </div>
                    <p>Advanced AI assistant for Discord with powerful server management tools.</p>
                    <div class="footer-social">
                        <a href="#" target="_blank"><i class="fab fa-discord"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-twitter"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-github"></i></a>
                    </div>
                </div>
                
                <div class="footer-links">
                    <h4>Quick Links</h4>
                    <ul>
                        <li><a href="/">Home</a></li>
                        <li><a href="/about.php">About</a></li>
                        <li><a href="/pricing.php">Pricing</a></li>
                        <li><a href="/contact.php">Contact</a></li>
                    </ul>
                </div>
                
                <div class="footer-links">
                    <h4>Resources</h4>
                    <ul>
                        <li><a href="/docs/">Documentation</a></li>
                        <li><a href="/faq.php">FAQ</a></li>
                        <li><a href="/blog/">Blog</a></li>
                        <li><a href="/support.php">Support</a></li>
                    </ul>
                </div>
                
                <div class="footer-links">
                    <h4>Legal</h4>
                    <ul>
                        <li><a href="/terms.php">Terms of Service</a></li>
                        <li><a href="/privacy.php">Privacy Policy</a></li>
                        <li><a href="/cookies.php">Cookie Policy</a></li>
                    </ul>
                </div>
            </div>
            
            <div class="footer-bottom">
                <p>&copy; <?php echo date('Y'); ?> <?php echo SITE_NAME; ?>. All rights reserved.</p>
            </div>
        </div>
    </footer>
    
    <!-- Scripts -->
    <script src="/assets/js/main.js"></script>
</body>
</html>
