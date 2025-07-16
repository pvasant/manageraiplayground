#!/bin/bash

# Weekly Report Environment Variables Setup Template
# Copy this file and customize with your actual values
# Usage: source env_setup.sh

echo "Setting up environment variables for weekly report..."

# JIRA Configuration
export JIRA_SERVER_URL="https://your-jira-instance.com"
export JIRA_BEARER_TOKEN="your_jira_bearer_token_here"
export JIRA_PROJECT="YOUR_PROJECT"
export JIRA_COMPONENTS="component1,component2"

# Gemini AI Configuration
export GEMINI_API_KEY="your_gemini_api_key_here"

# Email Configuration (Optional - only needed if you want email reports)
export EMAIL_USER="your-email@company.com"
export EMAIL_PASSWORD="your_email_password_here"
export MANAGER_EMAIL="recipient@company.com"

# SMTP Configuration (Optional)
export SMTP_SERVER="smtp.yourcompany.com"
export SMTP_PORT="587"

# Report Configuration (Optional - defaults provided)
export DAYS_PAST="7"  # Number of days to look back

echo "✅ Environment variables set successfully!"
echo "You can now run: python3 weekly_report_generator.py"
echo ""
echo "To verify variables are set, run: env | grep -E '(JIRA|GEMINI|EMAIL|SMTP)'" 