# Claude Weekly Status Reporter

Automated Jira-based weekly status report generator with email delivery. Perfect for managers who need regular team status updates.

## ✨ Features

- 📊 **Smart Categorization**: Automatically groups tickets by FIPS, Upgrades, Testing, Platform Features
- 🔗 **Clickable Jira Links**: All tickets include direct Jira links
- 📧 **Email Integration**: Professional HTML formatted emails
- 🎯 **Team Metrics**: Shows started, completed, and in-progress tickets
- ⚙️ **Multi-Project Support**: Each manager can configure their own projects/components
- 🏢 **Corporate SMTP**: Works with corporate email systems

## 🚀 Quick Start for Any Manager

### 1. Setup (One-time)
```bash
cd scripts/claudeReporter
./setup-weekly-reporter.sh
```

### 2. Configure Your Project
Edit `weekly-status-config.ini` with your team details:

```ini
[jira]
base_url = https://your-jira-instance.com
api_token = YOUR_JIRA_API_TOKEN  # Get from Jira Profile → Personal Access Tokens
project = YOUR_PROJECT           # e.g., TEAM, AI, PLATFORM
components = your-component,team-component  # e.g., backend,frontend,mobile

[email]
smtp_server = smtp.your-company.com
smtp_port = 587
username = your.email@company.com
password = your_password         # Optional for corporate SMTP
from_email = your.email@company.com
to_emails = manager@company.com,skip-level@company.com
```

### 3. Run Your Weekly Report
```bash
# Send weekly report via email
python3 weekly-status-reporter.py

# Generate report without sending email
python3 weekly-status-reporter.py --no-email

# Save to file
python3 weekly-status-reporter.py --output my-team-report.md --no-email
```

## 📋 Real Examples for Different Teams

### AI Team Manager
```ini
[jira]
project = AI
components = ai-platform,ml-ops,data-pipeline

[email]
from_email = ai-manager@company.com
to_emails = cto@company.com,product-owner@company.com
```

### Platform Team Manager
```ini
[jira]
project = PLATFORM
components = infrastructure,security,devops

[email]
from_email = platform-lead@company.com
to_emails = engineering-director@company.com
```

### Multi-Component Team
```ini
[jira]
project = BACKEND
components = api,database,microservices,auth

[email]
from_email = backend-manager@company.com
to_emails = tech-director@company.com,product-manager@company.com
```

## 🎯 No-Code Usage for Managers

### Environment Variables (Zero Config Files)
Create a simple script for your team:

```bash
#!/bin/bash
# my-team-report.sh

export JIRA_API_TOKEN="your_jira_token"
export JIRA_PROJECT="AI"
export JIRA_COMPONENTS="ai-platform,ml-ops"
export FROM_EMAIL="ai-team@company.com"
export TO_EMAILS="manager@company.com,director@company.com"
export EMAIL_SUBJECT="AI Team Weekly Status - Week $(date +'%U')"

python3 weekly-status-reporter.py
```

### Custom Report Subjects
```bash
python3 weekly-status-reporter.py --subject "AI Team Sprint Review - Q3 2025"
python3 weekly-status-reporter.py --subject "Platform Team Weekly - Emergency Release Week"
```

## 🔧 Getting Your Jira API Token

1. Go to your Jira instance → Profile → Personal Access Tokens
2. Click **Create token** or **Personal Access Tokens**
3. Create new token with **Read** permissions
4. Copy the generated token (long alphanumeric string)

## 📊 Sample Report Output

```markdown
# Weekly Status Report - AI Team
**Week of September 02-09, 2025**

## 📈 What Was Started This Week (12 new tickets)
**Platform Features:**
- [AI-234](https://your-jira.com/browse/AI-234): ML Pipeline Auto-scaling (Sarah Chen)
- [AI-235](https://your-jira.com/browse/AI-235): GPU Resource Management (Mike Kumar)

## ✅ What Was Completed This Week (8 tickets)
- [AI-201](https://your-jira.com/browse/AI-201): Model Deployment Pipeline ✅
- [AI-198](https://your-jira.com/browse/AI-198): Data Lake Integration ✅

## 🚧 In Progress & Key Work Streams (15 active tickets)
**AI Platform:**
- [AI-220](https://your-jira.com/browse/AI-220): Real-time Inference Engine (Alex Rodriguez)
- [AI-215](https://your-jira.com/browse/AI-215): Model Registry Service (Jennifer Wu)
```

## 🤝 Sharing with Other Managers

### Option 1: Copy This Folder
```bash
# Each manager gets their own copy
cp -r scripts/claudeReporter /path/to/their/workspace/
```

### Option 2: Shared Instance
Managers can use the same installation with different config files:
```bash
cp weekly-status-config.ini ai-team-config.ini
cp weekly-status-config.ini platform-config.ini

# Each team runs with their config
python3 weekly-status-reporter.py --config ai-team-config.ini
python3 weekly-status-reporter.py --config platform-config.ini
```

## 🛠️ Troubleshooting

### "Project does not exist"
- Check exact project key in Jira (case sensitive)
- Verify you have access to the project

### "Component does not exist"  
- Go to your Jira project → Project Settings → Components
- Use exact component names (case sensitive)

### Email not sending
- Corporate SMTP usually doesn't need authentication
- Verify you're on corporate network/VPN
- Check email addresses are correct

## 📞 Support

This tool was created using Claude Code and is part of the [Manager AI Playground](https://github.com/pvasant/manageraiplayground).

For issues or enhancements, create an issue in the repository.