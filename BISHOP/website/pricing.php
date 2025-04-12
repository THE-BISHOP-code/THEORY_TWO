<?php
/**
 * BISHOP Website - Pricing Page
 */
require_once 'includes/config.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pricing - <?php echo SITE_NAME; ?></title>
    <meta name="description" content="Choose the perfect plan for your Discord server with our flexible pricing options.">
    
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
        .pricing-comparison {
            margin-top: 3rem;
        }
        
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 2rem;
            background: var(--glass-bg);
            border-radius: var(--radius-lg);
            overflow: hidden;
        }
        
        .comparison-table th,
        .comparison-table td {
            padding: 1rem;
            text-align: center;
            border-bottom: 1px solid var(--glass-border);
        }
        
        .comparison-table th {
            background: rgba(0, 0, 0, 0.2);
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .comparison-table tr:last-child td {
            border-bottom: none;
        }
        
        .comparison-table td:first-child {
            text-align: left;
            font-weight: 500;
        }
        
        .comparison-table .feature-name {
            display: flex;
            align-items: center;
        }
        
        .comparison-table .feature-icon {
            margin-right: 0.75rem;
            color: var(--accent-gold);
        }
        
        .comparison-table .check {
            color: var(--accent-green);
            font-size: 1.25rem;
        }
        
        .comparison-table .times {
            color: var(--accent-red);
            font-size: 1.25rem;
        }
        
        .comparison-table .highlight {
            background: rgba(52, 152, 219, 0.1);
        }
        
        .tier-header {
            padding: 1rem;
            text-align: center;
            border-bottom: 1px solid var(--glass-border);
        }
        
        .tier-name {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .tier-price {
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-gold);
            margin-bottom: 0.5rem;
        }
        
        .tier-period {
            font-size: 0.9rem;
            color: var(--text-muted);
        }
        
        .tier-cta {
            margin-top: 1rem;
        }
        
        .faq-section {
            margin-top: 5rem;
        }
        
        .faq-item {
            margin-bottom: 1.5rem;
        }
        
        .faq-question {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--accent-gold);
        }
        
        .faq-answer {
            color: var(--text-secondary);
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
    
    <!-- Pricing Hero -->
    <section class="hero" style="height: 50vh; min-height: 400px;">
        <div class="container">
            <div class="hero-content animate-on-scroll">
                <h1 class="hero-title">Choose Your Perfect Plan</h1>
                <p class="hero-subtitle">Flexible pricing options to meet your needs, from free to premium features.</p>
            </div>
        </div>
    </section>
    
    <!-- Pricing Cards -->
    <section id="pricing" class="pricing">
        <div class="container">
            <div class="pricing-grid">
                <div class="glass-card pricing-card animate-on-scroll delay-1" id="drifter">
                    <h3 class="pricing-title">Drifter</h3>
                    <div class="pricing-price">
                        Free
                    </div>
                    <ul class="pricing-features">
                        <li class="included">3 replies per conversation</li>
                        <li class="included">5 saved files max</li>
                        <li class="included">10-minute cooldown</li>
                        <li class="included">Basic commands</li>
                        <li class="excluded">Custom bot configuration</li>
                        <li class="excluded">Premium commands</li>
                        <li class="excluded">Priority support</li>
                    </ul>
                    <a href="<?php echo get_discord_oauth_url(); ?>" class="btn btn-secondary">Get Started</a>
                </div>
                
                <div class="glass-card pricing-card featured animate-on-scroll delay-2" id="seeker">
                    <h3 class="pricing-title">Seeker</h3>
                    <div class="pricing-price">
                        $<?php echo TIER_SEEKER_PRICE; ?>
                        <span class="pricing-period">/ month</span>
                    </div>
                    <ul class="pricing-features">
                        <li class="included">5 replies per conversation</li>
                        <li class="included">12 saved files max</li>
                        <li class="included">2-minute cooldown</li>
                        <li class="included">Basic commands</li>
                        <li class="excluded">Custom bot configuration</li>
                        <li class="included">Premium commands</li>
                        <li class="included">Priority support</li>
                    </ul>
                    <a href="<?php echo is_logged_in() ? '/dashboard/subscription.php?tier=seeker' : get_discord_oauth_url(); ?>" class="btn btn-primary">Choose Plan</a>
                </div>
                
                <div class="glass-card pricing-card animate-on-scroll delay-3" id="abysswalker">
                    <h3 class="pricing-title">Abysswalker</h3>
                    <div class="pricing-price">
                        $<?php echo TIER_ABYSSWALKER_PRICE; ?>
                        <span class="pricing-period">/ month</span>
                    </div>
                    <ul class="pricing-features">
                        <li class="included">7 replies per conversation</li>
                        <li class="included">30 saved files max</li>
                        <li class="included">No cooldown</li>
                        <li class="included">Basic commands</li>
                        <li class="included">Custom bot configuration</li>
                        <li class="included">Premium commands</li>
                        <li class="included">Dedicated support</li>
                    </ul>
                    <a href="<?php echo is_logged_in() ? '/dashboard/subscription.php?tier=abysswalker' : get_discord_oauth_url(); ?>" class="btn btn-secondary">Choose Plan</a>
                </div>
            </div>
            
            <!-- Feature Comparison -->
            <div class="pricing-comparison animate-on-scroll">
                <h2 class="section-title">Feature Comparison</h2>
                
                <div class="table-responsive">
                    <table class="comparison-table">
                        <thead>
                            <tr>
                                <th>Feature</th>
                                <th>
                                    <div class="tier-header">
                                        <div class="tier-name">Drifter</div>
                                        <div class="tier-price">Free</div>
                                        <div class="tier-cta">
                                            <a href="<?php echo get_discord_oauth_url(); ?>" class="btn btn-secondary">Get Started</a>
                                        </div>
                                    </div>
                                </th>
                                <th class="highlight">
                                    <div class="tier-header">
                                        <div class="tier-name">Seeker</div>
                                        <div class="tier-price">$<?php echo TIER_SEEKER_PRICE; ?></div>
                                        <div class="tier-period">per month</div>
                                        <div class="tier-cta">
                                            <a href="<?php echo is_logged_in() ? '/dashboard/subscription.php?tier=seeker' : get_discord_oauth_url(); ?>" class="btn btn-primary">Choose Plan</a>
                                        </div>
                                    </div>
                                </th>
                                <th>
                                    <div class="tier-header">
                                        <div class="tier-name">Abysswalker</div>
                                        <div class="tier-price">$<?php echo TIER_ABYSSWALKER_PRICE; ?></div>
                                        <div class="tier-period">per month</div>
                                        <div class="tier-cta">
                                            <a href="<?php echo is_logged_in() ? '/dashboard/subscription.php?tier=abysswalker' : get_discord_oauth_url(); ?>" class="btn btn-secondary">Choose Plan</a>
                                        </div>
                                    </div>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>
                                    <div class="feature-name">
                                        <i class="fas fa-comment feature-icon"></i>
                                        Replies per Conversation
                                    </div>
                                </td>
                                <td>3</td>
                                <td class="highlight">5</td>
                                <td>7</td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="feature-name">
                                        <i class="fas fa-save feature-icon"></i>
                                        Max Saved Files
                                    </div>
                                </td>
                                <td>5</td>
                                <td class="highlight">12</td>
                                <td>30</td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="feature-name">
                                        <i class="fas fa-clock feature-icon"></i>
                                        Cooldown Period
                                    </div>
                                </td>
                                <td>10 minutes</td>
                                <td class="highlight">2 minutes</td>
                                <td>None</td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="feature-name">
                                        <i class="fas fa-terminal feature-icon"></i>
                                        Basic Commands
                                    </div>
                                </td>
                                <td><i class="fas fa-check check"></i></td>
                                <td class="highlight"><i class="fas fa-check check"></i></td>
                                <td><i class="fas fa-check check"></i></td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="feature-name">
                                        <i class="fas fa-code feature-icon"></i>
                                        Premium Commands
                                    </div>
                                </td>
                                <td><i class="fas fa-times times"></i></td>
                                <td class="highlight"><i class="fas fa-check check"></i></td>
                                <td><i class="fas fa-check check"></i></td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="feature-name">
                                        <i class="fas fa-exchange-alt feature-icon"></i>
                                        Market Access
                                    </div>
                                </td>
                                <td>Read-only</td>
                                <td class="highlight">Full</td>
                                <td>Full</td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="feature-name">
                                        <i class="fas fa-robot feature-icon"></i>
                                        Custom Bot Configuration
                                    </div>
                                </td>
                                <td><i class="fas fa-times times"></i></td>
                                <td class="highlight"><i class="fas fa-times times"></i></td>
                                <td><i class="fas fa-check check"></i></td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="feature-name">
                                        <i class="fas fa-server feature-icon"></i>
                                        Servers
                                    </div>
                                </td>
                                <td>Unlimited</td>
                                <td class="highlight">Unlimited</td>
                                <td>Unlimited (2 custom)</td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="feature-name">
                                        <i class="fas fa-headset feature-icon"></i>
                                        Support
                                    </div>
                                </td>
                                <td>Community</td>
                                <td class="highlight">Priority</td>
                                <td>Dedicated</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- FAQ Section -->
            <div class="faq-section animate-on-scroll">
                <h2 class="section-title">Frequently Asked Questions</h2>
                
                <div class="glass-card">
                    <div class="faq-item">
                        <div class="faq-question">How do I upgrade my tier?</div>
                        <div class="faq-answer">
                            To upgrade your tier, log in to your dashboard and navigate to the Subscription page. From there, you can select your desired tier and complete the payment process.
                        </div>
                    </div>
                    
                    <div class="faq-item">
                        <div class="faq-question">Can I downgrade my subscription?</div>
                        <div class="faq-answer">
                            Yes, you can downgrade your subscription at any time. Your current tier benefits will remain active until the end of your billing cycle, after which your account will switch to the new tier.
                        </div>
                    </div>
                    
                    <div class="faq-item">
                        <div class="faq-question">What payment methods do you accept?</div>
                        <div class="faq-answer">
                            We accept all major credit cards, PayPal, and cryptocurrency payments.
                        </div>
                    </div>
                    
                    <div class="faq-item">
                        <div class="faq-question">Is there a free trial for premium tiers?</div>
                        <div class="faq-answer">
                            We occasionally offer free trials for our premium tiers. Join our Discord server to stay updated on promotions and trial opportunities.
                        </div>
                    </div>
                    
                    <div class="faq-item">
                        <div class="faq-question">What happens to my saved files if I downgrade?</div>
                        <div class="faq-answer">
                            If you downgrade and have more saved files than your new tier allows, your files will remain accessible but you won't be able to save new files until you're below your tier's limit.
                        </div>
                    </div>
                    
                    <div class="faq-item">
                        <div class="faq-question">Can I use BISHOP on multiple servers?</div>
                        <div class="faq-answer">
                            Yes, you can add BISHOP to as many servers as you want. However, custom bot configuration is limited to 2 servers for Abysswalker tier users.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <!-- CTA Section -->
    <section class="cta">
        <div class="container">
            <div class="glass-card animate-on-scroll" style="text-align: center; padding: 3rem;">
                <h2>Ready to Get Started?</h2>
                <p>Choose the plan that's right for you and start enhancing your Discord experience today.</p>
                <div style="margin-top: 2rem;">
                    <a href="<?php echo get_discord_oauth_url(); ?>" class="btn btn-primary btn-large">Sign Up Now</a>
                    <a href="/contact.php" class="btn btn-secondary btn-large" style="margin-left: 1rem;">Contact Sales</a>
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
