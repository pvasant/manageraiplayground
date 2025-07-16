# JIRA Weekly Status Report Generator

An automated tool that generates professional weekly status reports from JIRA issues using Google Gemini AI.

## Features

- **JIRA Integration**: Fetches issues from specified JIRA projects and components
- **Status Transition Tracking**: Analyzes which issues moved to In Progress, Review, or Closed states
- **AI-Powered Reports**: Uses Google Gemini AI to generate manager-friendly narrative reports
- **Email Automation**: Automatically sends reports via email with SMTP fallback options
- **Configurable**: Fully configurable via environment variables
- **Security-First**: No hardcoded credentials - all sensitive data via environment variables

## Report Format

The tool generates reports with these sections:

- **Started**: Items that moved to "In Progress" with explanations
- **Completed**: Items that were finished with accomplishments
- **Blocked / Off-track**: Items facing obstacles
- **Risks**: Potential issues identified from the data
- **Celebrations**: Team achievements and recognition

## Requirements

- Python 3.7+
- JIRA access with bearer token authentication
- Google Gemini AI API key
- (Optional) SMTP server access for email reports

## Installation

1. Clone this repository
2. Install required dependencies:
   ```bash
   pip install requests google-generativeai
   ```

## Configuration

### Environment Variables

Copy `env_setup_template.sh` to `env_setup.sh` and customize with your values:

```bash
# Required
export JIRA_SERVER_URL="https://your-jira-instance.com"
export JIRA_BEARER_TOKEN="your_jira_bearer_token"
export JIRA_PROJECT="YOUR_PROJECT"
export JIRA_COMPONENTS="component1,component2"
export GEMINI_API_KEY="your_gemini_api_key"

# Optional (for email reports)
export EMAIL_USER="your-email@company.com"
export EMAIL_PASSWORD="your_password"
export MANAGER_EMAIL="recipient@company.com"
export SMTP_SERVER="smtp.yourcompany.com"
export SMTP_PORT="587"

# Optional (defaults provided)
export DAYS_PAST="7"
```

### JIRA Authentication

1. Generate a JIRA bearer token from your JIRA instance
2. Ensure your token has read access to the specified project and components

### Gemini AI Setup

1. Get a Google Gemini AI API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set the `GEMINI_API_KEY` environment variable

## Usage

### Basic Usage

1. Set up environment variables:
   ```bash
   source env_setup.sh
   ```

2. Run the report generator:
   ```bash
   python3 weekly_report_generator.py
   ```

### Automation

You can automate this with cron jobs:

```bash
# Run every Friday at 5 PM
0 17 * * 5 /path/to/your/env_setup.sh && python3 /path/to/weekly_report_generator.py
```

## Example Output

```
**Started**
• PROJECT-123 - Implement new authentication system
  We moved this to In Progress given the completion of the security review...

**Completed**
• PROJECT-120 - Fix login bug
  John Smith successfully resolved the authentication issue affecting mobile users...

**Blocked / Off-track**
• PROJECT-125 - Database migration
  Blocked waiting for infrastructure team approval...

**Risks**
• Multiple blocked items could delay the Q3 release...

**Celebrations**
• Great work by Jane Doe completing the API refactoring ahead of schedule!
```

## Customization

### Project Configuration

Modify these variables in your environment setup:

- `JIRA_PROJECT`: Your JIRA project key
- `JIRA_COMPONENTS`: Comma-separated list of components to track
- `DAYS_PAST`: Number of days to look back (default: 7)

### Report Customization

The Gemini AI prompt can be customized in the `generate_report_with_gemini()` function to adjust:

- Report tone and style
- Section headers
- Content focus areas
- Team-specific terminology

### SMTP Configuration

The tool tries multiple SMTP configurations automatically:

1. Company SMTP without authentication (port 25)
2. Company SMTP with TLS (configured port)
3. Company SMTP with authentication
4. Gmail fallback

## Security

- **No hardcoded credentials**: All sensitive data via environment variables
- **Bearer token authentication**: Secure JIRA access
- **Environment isolation**: Credentials separate from code
- **Optional email**: Email functionality only enabled when configured

## Troubleshooting

### JIRA Connection Issues

- Verify your JIRA_SERVER_URL is correct
- Check bearer token permissions
- Ensure the project and components exist

### Email Issues

- Verify SMTP server settings
- Check firewall/network restrictions
- Try different authentication methods (the script tries multiple)

### Gemini AI Issues

- Verify your API key is valid
- Check API quotas and limits
- Ensure you have access to the Gemini 2.0 Flash model

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review environment variable configuration
3. Open an issue with detailed error messages and configuration (excluding sensitive data) 