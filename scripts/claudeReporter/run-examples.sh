#!/bin/bash

# Claude Weekly Status Reporter - Usage Examples
# This file shows different ways managers can use the reporter

echo "🚀 Claude Weekly Status Reporter - Examples"
echo ""

# Example 1: ROSA Team (default configuration)
echo "📊 Example 1: ROSA Team Report"
echo "python3 weekly-status-reporter.py --config weekly-status-config.ini"
echo ""

# Example 2: AI Team using environment variables
echo "🤖 Example 2: AI Team (Environment Variables)"
cat << 'EOF'
export JIRA_API_TOKEN="your_token"
export JIRA_PROJECT="AI"
export JIRA_COMPONENTS="ai-platform,ml-ops,data-pipeline"
export FROM_EMAIL="ai-team@redhat.com"
export TO_EMAILS="cto@redhat.com,ai-director@redhat.com"
export EMAIL_SUBJECT="AI Team Weekly Status - $(date +'%B %d, %Y')"
python3 weekly-status-reporter.py
EOF
echo ""

# Example 3: Platform Team
echo "🔧 Example 3: Platform Team Report"
cat << 'EOF'
# Create platform-config.ini with:
[jira]
project = PLATFORM
components = infrastructure,devops,security

[email]
from_email = platform-lead@redhat.com
to_emails = engineering-director@redhat.com,vp-engineering@redhat.com

# Run with:
python3 weekly-status-reporter.py --config platform-config.ini
EOF
echo ""

# Example 4: Save to file instead of email
echo "💾 Example 4: Save Report to File"
echo "python3 weekly-status-reporter.py --no-email --output team-report-\$(date +'%Y%m%d').md"
echo ""

# Example 5: Custom subject line
echo "📝 Example 5: Custom Subject Line"
echo "python3 weekly-status-reporter.py --subject \"Emergency Sprint Status - Critical Issues\""
echo ""

# Example 6: Multiple team setup
echo "👥 Example 6: Multiple Teams Setup"
cat << 'EOF'
# Create separate configs for each team
cp weekly-status-config.ini rosa-team.ini
cp weekly-status-config.ini ai-team.ini 
cp weekly-status-config.ini platform-team.ini

# Edit each config file for the specific team
# Then run weekly reports for all teams:
python3 weekly-status-reporter.py --config rosa-team.ini --subject "ROSA Team Weekly"
python3 weekly-status-reporter.py --config ai-team.ini --subject "AI Team Weekly"
python3 weekly-status-reporter.py --config platform-team.ini --subject "Platform Team Weekly"
EOF
echo ""

echo "✅ Copy and modify these examples for your team!"
echo "📚 See README.md for detailed configuration options"