#!/bin/bash

# Weekly Status Reporter Setup Script

echo "Setting up Weekly Status Reporter..."

# Make the Python script executable
chmod +x weekly-status-reporter.py

# Check if Python requests library is available
python3 -c "import requests" 2>/dev/null || {
    echo "Installing required Python packages..."
    pip3 install requests
}

# Copy example config if config doesn't exist
if [ ! -f "weekly-status-config.ini" ]; then
    cp weekly-status-config.ini.example weekly-status-config.ini
    echo "Created configuration file: weekly-status-config.ini"
    echo "Please edit this file with your email settings."
else
    echo "Configuration file already exists: weekly-status-config.ini"
fi

echo ""
echo "Setup complete! Usage examples:"
echo ""
echo "1. Create/update configuration:"
echo "   ./weekly-status-reporter.py --create-config"
echo ""
echo "2. Generate report and send email:"
echo "   ./weekly-status-reporter.py"
echo ""
echo "3. Generate report only (no email):"
echo "   ./weekly-status-reporter.py --no-email"
echo ""
echo "4. Save report to file:"
echo "   ./weekly-status-reporter.py --output weekly-report.md --no-email"
echo ""
echo "5. Use custom config file:"
echo "   ./weekly-status-reporter.py --config custom-config.ini"
echo ""
echo "6. Custom email subject:"
echo "   ./weekly-status-reporter.py --subject 'ROSA Weekly Update - Special Edition'"
echo ""
echo "Email Configuration Notes:"
echo "- For Gmail: Use App Password (not regular password)"
echo "- Enable 2FA and generate App Password in Google Account settings"
echo "- For corporate email: Check with IT for SMTP settings"
echo ""
echo "Environment Variables (alternative to config file):"
echo "export JIRA_API_TOKEN='your_token'"
echo "export SMTP_SERVER='smtp.gmail.com'"
echo "export SMTP_USERNAME='your_email@gmail.com'"
echo "export SMTP_PASSWORD='your_app_password'"
echo "export FROM_EMAIL='your_email@gmail.com'"
echo "export TO_EMAILS='recipient1@gmail.com,recipient2@gmail.com'"