<?php
/**
 * BISHOP Website - About Page
 */
require_once 'includes/config.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About - <?php echo SITE_NAME; ?></title>
    <meta name="description" content="Learn more about BISHOP, the advanced AI assistant for Discord with powerful server management tools.">
    
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
        .about-hero {
            position: relative;
            overflow: hidden;
            padding: 8rem 0;
            background: linear-gradient(135deg, rgba(15, 18, 24, 0.9) 0%, rgba(26, 31, 42, 0.9) 100%);
        }
        
        .about-hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: url('/assets/img/about-bg.jpg');
            background-size: cover;
            background-position: center;
            opacity: 0.2;
            z-index: -1;
        }
        
        .mission-section {
            padding: 5rem 0;
        }
        
        .mission-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 3rem;
            align-items: center;
        }
        
        .mission-image img {
            border-radius: var(--radius-lg);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .values-section {
            padding: 5rem 0;
            background: linear-gradient(135deg, rgba(15, 18, 24, 0.8) 0%, rgba(26, 31, 42, 0.8) 100%);
        }
        
        .values-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
        }
        
        .value-card {
            text-align: center;
            padding: 2rem;
        }
        
        .value-icon {
            width: 80px;
            height: 80px;
            background: var(--glass-bg);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            font-size: 2rem;
            color: var(--accent-gold);
        }
        
        .value-title {
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .team-section {
            padding: 5rem 0;
        }
        
        .team-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
        }
        
        .team-card {
            text-align: center;
        }
        
        .team-avatar {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            overflow: hidden;
            margin: 0 auto 1.5rem;
            border: 3px solid var(--accent-gold);
        }
        
        .team-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .team-name {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }
        
        .team-role {
            color: var(--accent-gold);
            margin-bottom: 1rem;
        }
        
        .team-bio {
            color: var(--text-secondary);
        }
        
        .team-social {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .team-social a {
            width: 40px;
            height: 40px;
            background: var(--glass-bg);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
            transition: all var(--transition-fast);
        }
        
        .team-social a:hover {
            background: var(--accent-gold);
            color: var(--bg-primary);
            transform: translateY(-3px);
        }
        
        .timeline-section {
            padding: 5rem 0;
            background: linear-gradient(135deg, rgba(15, 18, 24, 0.8) 0%, rgba(26, 31, 42, 0.8) 100%);
        }
        
        .timeline {
            position: relative;
            max-width: 800px;
            margin: 3rem auto 0;
        }
        
        .timeline::after {
            content: '';
            position: absolute;
            width: 2px;
            background-color: var(--accent-gold);
            top: 0;
            bottom: 0;
            left: 50%;
            margin-left: -1px;
        }
        
        .timeline-item {
            padding: 10px 40px;
            position: relative;
            width: 50%;
            box-sizing: border-box;
        }
        
        .timeline-item::after {
            content: '';
            position: absolute;
            width: 20px;
            height: 20px;
            background-color: var(--bg-primary);
            border: 4px solid var(--accent-gold);
            border-radius: 50%;
            top: 15px;
            z-index: 1;
        }
        
        .timeline-item:nth-child(odd) {
            left: 0;
        }
        
        .timeline-item:nth-child(even) {
            left: 50%;
        }
        
        .timeline-item:nth-child(odd)::after {
            right: -10px;
        }
        
        .timeline-item:nth-child(even)::after {
            left: -10px;
        }
        
        .timeline-content {
            padding: 20px;
            background: var(--glass-bg);
            border-radius: var(--radius-md);
            position: relative;
        }
        
        .timeline-date {
            color: var(--accent-gold);
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .timeline-title {
            margin-bottom: 0.5rem;
        }
        
        .timeline-description {
            color: var(--text-secondary);
        }
        
        @media (max-width: 768px) {
            .mission-grid {
                grid-template-columns: 1fr;
            }
            
            .timeline::after {
                left: 31px;
            }
            
            .timeline-item {
                width: 100%;
                padding-left: 70px;
                padding-right: 25px;
            }
            
            .timeline-item:nth-child(even) {
                left: 0;
            }
            
            .timeline-item:nth-child(odd)::after,
            .timeline-item:nth-child(even)::after {
                left: 21px;
            }
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
    
    <!-- About Hero -->
    <section class="about-hero">
        <div class="container">
            <div class="hero-content animate-on-scroll">
                <h1 class="hero-title">About BISHOP</h1>
                <p class="hero-subtitle">Learn about our mission, values, and the team behind BISHOP.</p>
            </div>
        </div>
    </section>
    
    <!-- Mission Section -->
    <section class="mission-section">
        <div class="container">
            <div class="mission-grid">
                <div class="mission-content animate-on-scroll">
                    <h2>Our Mission</h2>
                    <p>BISHOP was created with a clear mission: to provide the most versatile and user-friendly AI assistant for Discord, empowering users to be more productive and creative in their communities.</p>
                    <p>We believe that AI should be accessible to everyone, regardless of technical expertise. That's why we've designed BISHOP to be intuitive and easy to use, while still offering powerful features for advanced users.</p>
                    <p>Our goal is to continuously improve and expand BISHOP's capabilities, working closely with our community to ensure that we're meeting their needs and exceeding their expectations.</p>
                </div>
                <div class="mission-image animate-on-scroll delay-2">
                    <img src="/assets/img/mission-image.jpg" alt="BISHOP Mission">
                </div>
            </div>
        </div>
    </section>
    
    <!-- Values Section -->
    <section class="values-section">
        <div class="container">
            <h2 class="section-title animate-on-scroll">Our Values</h2>
            
            <div class="values-grid">
                <div class="glass-card value-card animate-on-scroll delay-1">
                    <div class="value-icon">
                        <i class="fas fa-lightbulb"></i>
                    </div>
                    <h3 class="value-title">Innovation</h3>
                    <p>We're constantly pushing the boundaries of what's possible with AI and Discord integration, exploring new features and capabilities to enhance the user experience.</p>
                </div>
                
                <div class="glass-card value-card animate-on-scroll delay-2">
                    <div class="value-icon">
                        <i class="fas fa-users"></i>
                    </div>
                    <h3 class="value-title">Community</h3>
                    <p>We believe in the power of community and collaboration. Our users are at the heart of everything we do, and we're committed to building a supportive and inclusive community around BISHOP.</p>
                </div>
                
                <div class="glass-card value-card animate-on-scroll delay-3">
                    <div class="value-icon">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <h3 class="value-title">Security</h3>
                    <p>We take security and privacy seriously. We're committed to protecting our users' data and ensuring that BISHOP is a safe and secure platform for everyone.</p>
                </div>
                
                <div class="glass-card value-card animate-on-scroll delay-4">
                    <div class="value-icon">
                        <i class="fas fa-star"></i>
                    </div>
                    <h3 class="value-title">Quality</h3>
                    <p>We're dedicated to delivering the highest quality product possible. We rigorously test and refine BISHOP to ensure that it meets our high standards for performance, reliability, and user experience.</p>
                </div>
            </div>
        </div>
    </section>
    
    <!-- Team Section -->
    <section class="team-section">
        <div class="container">
            <h2 class="section-title animate-on-scroll">Meet the Team</h2>
            
            <div class="team-grid">
                <div class="glass-card team-card animate-on-scroll delay-1">
                    <div class="team-avatar">
                        <img src="/assets/img/team-1.jpg" alt="Reign Spectre">
                    </div>
                    <h3 class="team-name">Reign Spectre</h3>
                    <div class="team-role">Founder & Lead Developer</div>
                    <p class="team-bio">Reign is the visionary behind BISHOP, combining expertise in AI and Discord bot development to create a powerful and user-friendly assistant.</p>
                    <div class="team-social">
                        <a href="#" target="_blank"><i class="fab fa-discord"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-twitter"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-github"></i></a>
                    </div>
                </div>
                
                <div class="glass-card team-card animate-on-scroll delay-2">
                    <div class="team-avatar">
                        <img src="/assets/img/team-2.jpg" alt="Alex Chen">
                    </div>
                    <h3 class="team-name">Alex Chen</h3>
                    <div class="team-role">AI Engineer</div>
                    <p class="team-bio">Alex specializes in natural language processing and machine learning, ensuring that BISHOP's AI capabilities are cutting-edge and responsive.</p>
                    <div class="team-social">
                        <a href="#" target="_blank"><i class="fab fa-discord"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-twitter"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-github"></i></a>
                    </div>
                </div>
                
                <div class="glass-card team-card animate-on-scroll delay-3">
                    <div class="team-avatar">
                        <img src="/assets/img/team-3.jpg" alt="Sophia Rodriguez">
                    </div>
                    <h3 class="team-name">Sophia Rodriguez</h3>
                    <div class="team-role">UX/UI Designer</div>
                    <p class="team-bio">Sophia is passionate about creating intuitive and beautiful user experiences, ensuring that BISHOP is not only powerful but also a joy to use.</p>
                    <div class="team-social">
                        <a href="#" target="_blank"><i class="fab fa-discord"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-twitter"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-dribbble"></i></a>
                    </div>
                </div>
                
                <div class="glass-card team-card animate-on-scroll delay-4">
                    <div class="team-avatar">
                        <img src="/assets/img/team-4.jpg" alt="Marcus Johnson">
                    </div>
                    <h3 class="team-name">Marcus Johnson</h3>
                    <div class="team-role">Community Manager</div>
                    <p class="team-bio">Marcus is the heart of our community, ensuring that users have the support they need and that their feedback is heard and implemented.</p>
                    <div class="team-social">
                        <a href="#" target="_blank"><i class="fab fa-discord"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-twitter"></i></a>
                        <a href="#" target="_blank"><i class="fab fa-instagram"></i></a>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <!-- Timeline Section -->
    <section class="timeline-section">
        <div class="container">
            <h2 class="section-title animate-on-scroll">Our Journey</h2>
            
            <div class="timeline animate-on-scroll">
                <div class="timeline-item">
                    <div class="timeline-content glass-card">
                        <div class="timeline-date">January 2023</div>
                        <h3 class="timeline-title">The Idea</h3>
                        <p class="timeline-description">The concept for BISHOP was born out of a desire to create a more intelligent and versatile Discord bot that could truly understand and respond to users' needs.</p>
                    </div>
                </div>
                
                <div class="timeline-item">
                    <div class="timeline-content glass-card">
                        <div class="timeline-date">March 2023</div>
                        <h3 class="timeline-title">Development Begins</h3>
                        <p class="timeline-description">Development of BISHOP officially began, with a focus on creating a solid foundation for the bot's AI capabilities and Discord integration.</p>
                    </div>
                </div>
                
                <div class="timeline-item">
                    <div class="timeline-content glass-card">
                        <div class="timeline-date">June 2023</div>
                        <h3 class="timeline-title">Alpha Testing</h3>
                        <p class="timeline-description">The first alpha version of BISHOP was released to a small group of testers, who provided valuable feedback and helped shape the bot's development.</p>
                    </div>
                </div>
                
                <div class="timeline-item">
                    <div class="timeline-content glass-card">
                        <div class="timeline-date">September 2023</div>
                        <h3 class="timeline-title">Beta Launch</h3>
                        <p class="timeline-description">BISHOP entered beta, with more features and improvements based on alpha feedback. The community began to grow as more users discovered the bot.</p>
                    </div>
                </div>
                
                <div class="timeline-item">
                    <div class="timeline-content glass-card">
                        <div class="timeline-date">December 2023</div>
                        <h3 class="timeline-title">Official Release</h3>
                        <p class="timeline-description">BISHOP was officially released to the public, with a full suite of features and a growing community of users and supporters.</p>
                    </div>
                </div>
                
                <div class="timeline-item">
                    <div class="timeline-content glass-card">
                        <div class="timeline-date">Present</div>
                        <h3 class="timeline-title">Continuous Improvement</h3>
                        <p class="timeline-description">We continue to improve and expand BISHOP, working closely with our community to ensure that the bot meets their needs and exceeds their expectations.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <!-- CTA Section -->
    <section class="cta">
        <div class="container">
            <div class="glass-card animate-on-scroll" style="text-align: center; padding: 3rem;">
                <h2>Join Our Community</h2>
                <p>Become part of the BISHOP community and help shape the future of AI on Discord.</p>
                <div style="margin-top: 2rem;">
                    <a href="https://discord.gg/bishop" target="_blank" class="btn btn-primary btn-large">Join Discord Server</a>
                    <a href="<?php echo get_discord_oauth_url(); ?>" class="btn btn-secondary btn-large" style="margin-left: 1rem;">Get Started</a>
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
