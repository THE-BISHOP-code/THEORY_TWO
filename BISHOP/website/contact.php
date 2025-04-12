<?php
/**
 * BISHOP Website - Contact Page
 */
require_once 'includes/config.php';

// Process form submission
$success = false;
$error = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Get form data
    $name = isset($_POST['name']) ? trim($_POST['name']) : '';
    $email = isset($_POST['email']) ? trim($_POST['email']) : '';
    $subject = isset($_POST['subject']) ? trim($_POST['subject']) : '';
    $message = isset($_POST['message']) ? trim($_POST['message']) : '';
    
    // Validate data
    $errors = [];
    
    if (empty($name)) {
        $errors[] = 'Name is required.';
    }
    
    if (empty($email)) {
        $errors[] = 'Email is required.';
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $errors[] = 'Please enter a valid email address.';
    }
    
    if (empty($subject)) {
        $errors[] = 'Subject is required.';
    }
    
    if (empty($message)) {
        $errors[] = 'Message is required.';
    }
    
    // If no errors, process the form
    if (empty($errors)) {
        // In a real application, you would send an email or save to database here
        // For this example, we'll just simulate success
        $success = true;
    } else {
        $error = implode('<br>', $errors);
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact - <?php echo SITE_NAME; ?></title>
    <meta name="description" content="Get in touch with the BISHOP team for support, feedback, or business inquiries.">
    
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
        .contact-hero {
            position: relative;
            overflow: hidden;
            padding: 8rem 0;
            background: linear-gradient(135deg, rgba(15, 18, 24, 0.9) 0%, rgba(26, 31, 42, 0.9) 100%);
        }
        
        .contact-hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: url('/assets/img/contact-bg.jpg');
            background-size: cover;
            background-position: center;
            opacity: 0.2;
            z-index: -1;
        }
        
        .contact-main {
            padding: 5rem 0;
        }
        
        .contact-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 3rem;
        }
        
        .contact-info-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 2rem;
        }
        
        .contact-info-icon {
            width: 50px;
            height: 50px;
            background: var(--glass-bg);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 1rem;
            color: var(--accent-gold);
            font-size: 1.25rem;
            flex-shrink: 0;
        }
        
        .contact-info-content {
            flex: 1;
        }
        
        .contact-info-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .contact-info-text {
            color: var(--text-secondary);
        }
        
        .contact-form-container {
            background: var(--glass-bg);
            border-radius: var(--radius-lg);
            padding: 2rem;
            border: 1px solid var(--glass-border);
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .form-control {
            width: 100%;
            padding: 0.75rem 1rem;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            font-family: inherit;
            transition: border-color var(--transition-fast);
        }
        
        .form-control:focus {
            outline: none;
            border-color: var(--accent-blue);
        }
        
        textarea.form-control {
            resize: vertical;
            min-height: 150px;
        }
        
        .form-error {
            color: var(--accent-red);
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        .form-success {
            background-color: rgba(46, 204, 113, 0.1);
            border-left: 4px solid var(--accent-green);
            padding: 1rem;
            margin-bottom: 1.5rem;
            color: var(--accent-green);
            border-radius: 0.25rem;
        }
        
        .social-links {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .social-link {
            width: 50px;
            height: 50px;
            background: var(--glass-bg);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
            font-size: 1.25rem;
            transition: all var(--transition-fast);
        }
        
        .social-link:hover {
            background: var(--accent-gold);
            color: var(--bg-primary);
            transform: translateY(-3px);
        }
        
        .map-container {
            margin-top: 5rem;
            border-radius: var(--radius-lg);
            overflow: hidden;
            height: 400px;
        }
        
        .map-container iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        
        @media (max-width: 768px) {
            .contact-grid {
                grid-template-columns: 1fr;
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
    
    <!-- Contact Hero -->
    <section class="contact-hero">
        <div class="container">
            <div class="hero-content animate-on-scroll">
                <h1 class="hero-title">Get In Touch</h1>
                <p class="hero-subtitle">Have questions or feedback? We'd love to hear from you.</p>
            </div>
        </div>
    </section>
    
    <!-- Contact Main -->
    <section class="contact-main">
        <div class="container">
            <div class="contact-grid">
                <div class="contact-info animate-on-scroll">
                    <h2>Contact Information</h2>
                    <p>Feel free to reach out to us using any of the methods below. We're here to help!</p>
                    
                    <div class="contact-info-item">
                        <div class="contact-info-icon">
                            <i class="fas fa-envelope"></i>
                        </div>
                        <div class="contact-info-content">
                            <div class="contact-info-title">Email</div>
                            <div class="contact-info-text">
                                <a href="mailto:<?php echo SITE_EMAIL; ?>"><?php echo SITE_EMAIL; ?></a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="contact-info-item">
                        <div class="contact-info-icon">
                            <i class="fab fa-discord"></i>
                        </div>
                        <div class="contact-info-content">
                            <div class="contact-info-title">Discord</div>
                            <div class="contact-info-text">
                                <a href="https://discord.gg/bishop" target="_blank">Join our Discord server</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="contact-info-item">
                        <div class="contact-info-icon">
                            <i class="fas fa-headset"></i>
                        </div>
                        <div class="contact-info-content">
                            <div class="contact-info-title">Support</div>
                            <div class="contact-info-text">
                                For technical support, please visit our <a href="/support.php">Support Center</a>.
                            </div>
                        </div>
                    </div>
                    
                    <div class="contact-info-item">
                        <div class="contact-info-icon">
                            <i class="fas fa-clock"></i>
                        </div>
                        <div class="contact-info-content">
                            <div class="contact-info-title">Response Time</div>
                            <div class="contact-info-text">
                                We typically respond within 24-48 hours during business days.
                            </div>
                        </div>
                    </div>
                    
                    <div class="social-links">
                        <a href="#" class="social-link" target="_blank"><i class="fab fa-discord"></i></a>
                        <a href="#" class="social-link" target="_blank"><i class="fab fa-twitter"></i></a>
                        <a href="#" class="social-link" target="_blank"><i class="fab fa-github"></i></a>
                        <a href="#" class="social-link" target="_blank"><i class="fab fa-instagram"></i></a>
                    </div>
                </div>
                
                <div class="contact-form-container animate-on-scroll delay-2">
                    <h2>Send a Message</h2>
                    
                    <?php if ($success): ?>
                        <div class="form-success">
                            <i class="fas fa-check-circle"></i> Your message has been sent successfully. We'll get back to you as soon as possible.
                        </div>
                    <?php endif; ?>
                    
                    <?php if ($error): ?>
                        <div class="form-error">
                            <i class="fas fa-exclamation-circle"></i> <?php echo $error; ?>
                        </div>
                    <?php endif; ?>
                    
                    <form class="contact-form" method="post" action="/contact.php">
                        <div class="form-group">
                            <label for="name" class="form-label">Name</label>
                            <input type="text" id="name" name="name" class="form-control" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="email" class="form-label">Email</label>
                            <input type="email" id="email" name="email" class="form-control" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="subject" class="form-label">Subject</label>
                            <input type="text" id="subject" name="subject" class="form-control" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="message" class="form-label">Message</label>
                            <textarea id="message" name="message" class="form-control" rows="5" required></textarea>
                        </div>
                        
                        <button type="submit" class="btn btn-primary">Send Message</button>
                    </form>
                </div>
            </div>
            
            <!-- Map -->
            <div class="map-container animate-on-scroll">
                <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d387193.30596552044!2d-74.25986548248684!3d40.69714941932609!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89c24fa5d33f083b%3A0xc80b8f06e177fe62!2sNew%20York%2C%20NY%2C%20USA!5e0!3m2!1sen!2sca!4v1619712000000!5m2!1sen!2sca" allowfullscreen="" loading="lazy"></iframe>
            </div>
        </div>
    </section>
    
    <!-- FAQ Section -->
    <section class="faq-section">
        <div class="container">
            <h2 class="section-title animate-on-scroll">Frequently Asked Questions</h2>
            
            <div class="glass-card animate-on-scroll delay-1">
                <div class="faq-item">
                    <div class="faq-question">How can I get support for BISHOP?</div>
                    <div class="faq-answer">
                        For technical support, you can join our Discord server, submit a support ticket through our Support Center, or email us at <?php echo SITE_EMAIL; ?>.
                    </div>
                </div>
                
                <div class="faq-item">
                    <div class="faq-question">I have a feature suggestion. How can I submit it?</div>
                    <div class="faq-answer">
                        We love hearing your ideas! You can submit feature suggestions through our Discord server or by using the contact form on this page.
                    </div>
                </div>
                
                <div class="faq-item">
                    <div class="faq-question">How do I report a bug?</div>
                    <div class="faq-answer">
                        If you encounter a bug, please report it through our Discord server or by emailing us at <?php echo SITE_EMAIL; ?>. Please include as much detail as possible, including steps to reproduce the issue.
                    </div>
                </div>
                
                <div class="faq-item">
                    <div class="faq-question">I'm interested in business partnerships. Who should I contact?</div>
                    <div class="faq-answer">
                        For business inquiries and partnership opportunities, please email us at <?php echo SITE_EMAIL; ?> with the subject line "Business Partnership".
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
