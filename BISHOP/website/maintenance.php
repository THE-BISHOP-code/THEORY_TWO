<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Maintenance - <?php echo SITE_NAME; ?></title>
    
    <!-- Favicon -->
    <link rel="icon" href="/assets/img/favicon.ico">
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --bg-primary: #0f1218;
            --bg-secondary: #1a1f2a;
            --text-primary: #ffffff;
            --text-secondary: #b8c0d2;
            --accent-gold: #ffd700;
            --accent-blue: #3498db;
            --glass-bg: rgba(30, 39, 51, 0.6);
            --glass-border: rgba(255, 255, 255, 0.1);
            --radius-lg: 1rem;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html, body {
            height: 100%;
        }
        
        body {
            font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(30, 60, 114, 0.2) 0%, transparent 30%),
                radial-gradient(circle at 90% 80%, rgba(91, 33, 182, 0.2) 0%, transparent 40%);
            background-attachment: fixed;
        }
        
        .maintenance-container {
            max-width: 600px;
            text-align: center;
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-lg);
            padding: 3rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        
        .maintenance-icon {
            font-size: 4rem;
            margin-bottom: 1.5rem;
            color: var(--accent-gold);
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, var(--text-primary), var(--accent-gold));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        p {
            color: var(--text-secondary);
            margin-bottom: 2rem;
            font-size: 1.1rem;
        }
        
        .maintenance-progress {
            width: 100%;
            height: 10px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 5px;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }
        
        .maintenance-bar {
            height: 100%;
            width: 75%;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-gold));
            border-radius: 5px;
            animation: progress 2s ease-in-out infinite alternate;
        }
        
        @keyframes progress {
            0% { width: 60%; }
            100% { width: 90%; }
        }
        
        .maintenance-eta {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 2rem;
        }
        
        .social-links {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .social-link {
            width: 40px;
            height: 40px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
            transition: all 0.3s ease;
        }
        
        .social-link:hover {
            background: var(--accent-gold);
            color: var(--bg-primary);
            transform: translateY(-3px);
        }
    </style>
</head>
<body>
    <div class="maintenance-container">
        <div class="maintenance-icon">
            <i class="fas fa-tools"></i>
        </div>
        <h1>We're Under Maintenance</h1>
        <p>We're currently performing scheduled maintenance to improve your experience. We'll be back online shortly.</p>
        
        <div class="maintenance-progress">
            <div class="maintenance-bar"></div>
        </div>
        
        <div class="maintenance-eta">
            Estimated completion: <strong>1 hour</strong>
        </div>
        
        <p>In the meantime, you can follow us on social media for updates:</p>
        
        <div class="social-links">
            <a href="#" class="social-link" target="_blank"><i class="fab fa-discord"></i></a>
            <a href="#" class="social-link" target="_blank"><i class="fab fa-twitter"></i></a>
            <a href="#" class="social-link" target="_blank"><i class="fab fa-github"></i></a>
        </div>
    </div>
</body>
</html>
