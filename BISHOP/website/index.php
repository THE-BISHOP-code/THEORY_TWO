<?php
/**
 * BISHOP Website - Homepage
 */
require_once 'includes/config.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo SITE_NAME; ?> - Advanced AI Assistant for Discord</title>
    <meta name="description" content="<?php echo SITE_DESCRIPTION; ?>">
    
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
    
    <!-- Open Graph / Social Media -->
    <meta property="og:title" content="<?php echo SITE_NAME; ?> - Advanced AI Assistant for Discord">
    <meta property="og:description" content="<?php echo SITE_DESCRIPTION; ?>">
    <meta property="og:image" content="<?php echo SITE_URL; ?>/assets/img/og-image.jpg">
    <meta property="og:url" content="<?php echo SITE_URL; ?>">
    <meta property="og:type" content="website">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="<?php echo SITE_NAME; ?> - Advanced AI Assistant for Discord">
    <meta name="twitter:description" content="<?php echo SITE_DESCRIPTION; ?>">
    <meta name="twitter:image" content="<?php echo SITE_URL; ?>/assets/img/og-image.jpg">
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
    
    <!-- Hero Section -->
    <section class="hero">
        <div class="container">
            <div class="hero-content animate-on-scroll">
                <h1 class="hero-title">Advanced AI Assistant for Discord</h1>
                <p class="hero-subtitle">BISHOP combines powerful AI capabilities with server management tools to enhance your Discord experience.</p>
                <div class="hero-buttons">
                    <a href="/pricing.php" class="btn btn-primary btn-large">Get Started</a>
                    <a href="#features" class="btn btn-secondary btn-large">Learn More</a>
                </div>
            </div>
        </div>
        <div class="hero-character">
            <!-- Interactive character will be added here -->
            <img src="/assets/img/hero-character.png" alt="BISHOP AI Character" class="hero-image">
        </div>
    </section>
    
    <!-- Features Section -->
    <section id="features" class="features">
        <div class="container">
            <h2 class="section-title animate-on-scroll">Powerful Features</h2>
            
            <div class="features-grid">
                <div class="glass-card feature-card animate-on-scroll delay-1">
                    <div class="feature-icon">
                        <i class="fas fa-robot"></i>
                    </div>
                    <h3 class="feature-title">AI Interaction</h3>
                    <p>Use /spectre to interact with a powerful AI assistant that can help with various tasks, from creative writing to problem-solving.</p>
                </div>
                
                <div class="glass-card feature-card animate-on-scroll delay-2">
                    <div class="feature-icon">
                        <i class="fas fa-save"></i>
                    </div>
                    <h3 class="feature-title">Content Management</h3>
                    <p>Save and organize your AI-generated content with /vault for easy access later.</p>
                </div>
                
                <div class="glass-card feature-card animate-on-scroll delay-3">
                    <div class="feature-icon">
                        <i class="fas fa-exchange-alt"></i>
                    </div>
                    <h3 class="feature-title">Community Marketplace</h3>
                    <p>Share your creations with others and discover content from the community with /the_exchange.</p>
                </div>
                
                <div class="glass-card feature-card animate-on-scroll delay-4">
                    <div class="feature-icon">
                        <i class="fas fa-terminal"></i>
                    </div>
                    <h3 class="feature-title">Command Execution</h3>
                    <p>Execute saved commands with /commit to automate Discord server management tasks.</p>
                </div>
            </div>
        </div>
    </section>
    
    <!-- Pricing Section -->
    <section id="pricing" class="pricing">
        <div class="container">
            <h2 class="section-title animate-on-scroll">Choose Your Tier</h2>
            
            <div class="pricing-grid">
                <div class="glass-card pricing-card animate-on-scroll delay-1">
                    <h3 class="pricing-title">Drifter</h3>
                    <div class="pricing-price">
                        Free
                    </div>
                    <ul class="pricing-features">
                        <li class="included">3 replies per conversation</li>
                        <li class="included">5 saved files max</li>
                        <li class="included">10-minute cooldown</li>
                        <li class="excluded">Custom bot configuration</li>
                        <li class="excluded">Premium commands</li>
                        <li class="excluded">Priority support</li>
                    </ul>
                    <a href="<?php echo get_discord_oauth_url(); ?>" class="btn btn-secondary">Get Started</a>
                </div>
                
                <div class="glass-card pricing-card featured animate-on-scroll delay-2">
                    <h3 class="pricing-title">Seeker</h3>
                    <div class="pricing-price">
                        $<?php echo TIER_SEEKER_PRICE; ?>
                        <span class="pricing-period">/ month</span>
                    </div>
                    <ul class="pricing-features">
                        <li class="included">5 replies per conversation</li>
                        <li class="included">12 saved files max</li>
                        <li class="included">2-minute cooldown</li>
                        <li class="excluded">Custom bot configuration</li>
                        <li class="included">Premium commands</li>
                        <li class="included">Priority support</li>
                    </ul>
                    <a href="/pricing.php#seeker" class="btn btn-primary">Choose Plan</a>
                </div>
                
                <div class="glass-card pricing-card animate-on-scroll delay-3">
                    <h3 class="pricing-title">Abysswalker</h3>
                    <div class="pricing-price">
                        $<?php echo TIER_ABYSSWALKER_PRICE; ?>
                        <span class="pricing-period">/ month</span>
                    </div>
                    <ul class="pricing-features">
                        <li class="included">7 replies per conversation</li>
                        <li class="included">30 saved files max</li>
                        <li class="included">No cooldown</li>
                        <li class="included">Custom bot configuration</li>
                        <li class="included">Premium commands</li>
                        <li class="included">Dedicated support</li>
                    </ul>
                    <a href="/pricing.php#abysswalker" class="btn btn-secondary">Choose Plan</a>
                </div>
            </div>
        </div>
    </section>
    
    <!-- About Section -->
    <section id="about" class="about">
        <div class="container">
            <div class="about-grid">
                <div class="about-content animate-on-scroll">
                    <h2>About BISHOP</h2>
                    <p>BISHOP is an advanced Discord bot that combines AI capabilities with powerful server management tools. It's designed to enhance your Discord experience with intelligent conversations, content management, and automation.</p>
                    <p>Our mission is to provide the most versatile and user-friendly AI assistant for Discord, empowering users to be more productive and creative in their communities.</p>
                    <a href="/about.php" class="btn btn-secondary">Learn More</a>
                </div>
                <div class="about-image animate-on-scroll delay-2">
                    <img src="/assets/img/about-image.jpg" alt="BISHOP in action">
                </div>
            </div>
        </div>
    </section>
    
    <!-- Contact Section -->
    <section id="contact" class="contact">
        <div class="container">
            <h2 class="section-title animate-on-scroll">Get In Touch</h2>
            
            <div class="contact-grid">
                <div class="glass-card animate-on-scroll delay-1">
                    <h3>Contact Information</h3>
                    <ul class="contact-info">
                        <li>
                            <div class="contact-info-icon">
                                <i class="fas fa-envelope"></i>
                            </div>
                            <div>
                                <strong>Email</strong><br>
                                <a href="mailto:<?php echo SITE_EMAIL; ?>"><?php echo SITE_EMAIL; ?></a>
                            </div>
                        </li>
                        <li>
                            <div class="contact-info-icon">
                                <i class="fab fa-discord"></i>
                            </div>
                            <div>
                                <strong>Discord</strong><br>
                                <a href="https://discord.gg/bishop" target="_blank">Join our community</a>
                            </div>
                        </li>
                        <li>
                            <div class="contact-info-icon">
                                <i class="fas fa-globe"></i>
                            </div>
                            <div>
                                <strong>Website</strong><br>
                                <a href="<?php echo SITE_URL; ?>"><?php echo SITE_URL; ?></a>
                            </div>
                        </li>
                    </ul>
                </div>
                
                <div class="glass-card animate-on-scroll delay-2">
                    <h3>Send a Message</h3>
                    <form class="contact-form">
                        <div class="form-group">
                            <label for="name">Name</label>
                            <input type="text" id="name" name="name" required>
                        </div>
                        <div class="form-group">
                            <label for="email">Email</label>
                            <input type="email" id="email" name="email" required>
                        </div>
                        <div class="form-group">
                            <label for="message">Message</label>
                            <textarea id="message" name="message" rows="5" required></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary">Send Message</button>
                    </form>
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
