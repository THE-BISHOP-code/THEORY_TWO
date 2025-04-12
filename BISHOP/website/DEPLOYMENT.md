# BISHOP Website Deployment Guide

This guide provides instructions for deploying the BISHOP website to your hosting provider.

## Hosting Information

- **Website URL**: https://osiris.wuaze.com
- **Database Host**: sql304.infinityfree.com
- **Database Name**: if0_38711725_bishop
- **Database User**: if0_38711725
- **Database Password**: 1open1open1
- **FTP Host**: ftpupload.net
- **FTP User**: if0_38711725
- **FTP Password**: 1open1open1
- **FTP Port**: 21
- **FTP Root Directory**: /htdocs

## Deployment Methods

### Method 1: Automated FTP Deployment (Recommended)

1. Make sure your `.env` file is properly configured with the correct database and FTP credentials.
2. Run the deployment script by double-clicking on `deploy.bat` or running `php deploy-ftp.php` from the command line.
3. The script will:
   - Create a backup of your local files
   - Connect to the FTP server
   - Upload all necessary files
   - Create required directories
   - Skip sensitive files like `.env`, logs, etc.

### Method 2: Manual FTP Deployment

1. Connect to the FTP server using an FTP client like FileZilla:
   - Host: ftpupload.net
   - Username: if0_38711725
   - Password: 1open1open1
   - Port: 21
2. Upload all files to the `/htdocs` directory, except for:
   - `.env` (upload this separately and modify it on the server)
   - `.git` directory
   - `logs` directory
   - `backups` directory
   - `cache` directory
   - `node_modules` directory (if exists)
3. Make sure to set the correct permissions:
   - PHP files: 644
   - Directories: 755
   - Writable directories (logs, cache, storage): 777

### Method 3: Web-Based Deployment

1. Upload the `deploy-ftp.php` script to your server.
2. Access it via your browser: `https://osiris.wuaze.com/deploy-ftp.php?key=your_secret_deployment_key`
3. The script will perform the same actions as Method 1.

## Database Setup

1. Create the database if it doesn't exist already.
2. Import the database schema:
   - Use phpMyAdmin if available on your hosting control panel
   - Or run the migration script: `php migrate.php`

## Post-Deployment Tasks

1. Verify that the website is accessible at https://osiris.wuaze.com
2. Check that all pages load correctly
3. Test the login functionality
4. Verify that the database connection is working
5. Check that file uploads work correctly
6. Test the dashboard functionality

## Troubleshooting

If you encounter issues during deployment:

1. **FTP Connection Issues**:
   - Verify your FTP credentials
   - Check if your IP is allowed by the hosting provider
   - Try using passive mode

2. **Database Connection Issues**:
   - Verify your database credentials
   - Check if the database exists
   - Ensure the database user has the necessary permissions

3. **File Permission Issues**:
   - Make sure the directories that need to be writable have the correct permissions (777)
   - Check the ownership of the files

4. **500 Internal Server Error**:
   - Check the server error logs
   - Verify that the `.htaccess` file is correctly formatted
   - Make sure PHP version requirements are met

## Support

If you need assistance with deployment, please contact support at contact@example.com.
