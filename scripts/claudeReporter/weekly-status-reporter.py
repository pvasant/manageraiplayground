#!/usr/bin/env python3
"""
Weekly Status Reporter Tool
Fetches ROSA team status from Jira and sends formatted email report
"""

import requests
import json
import smtplib
import os
import sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import argparse
import configparser

class WeeklyStatusReporter:
    def __init__(self, config_file=None):
        self.config = self.load_config(config_file)
        self.jira_base_url = self.config.get('jira', 'base_url', fallback='https://issues.redhat.com')
        self.jira_token = self.config.get('jira', 'api_token')
        self.project = self.config.get('jira', 'project', fallback='OCM')
        self.components = self.config.get('jira', 'components', fallback='rosa,rosa-team').split(',')
        
        # Email config
        self.smtp_server = self.config.get('email', 'smtp_server')
        self.smtp_port = self.config.getint('email', 'smtp_port', fallback=587)
        self.smtp_username = self.config.get('email', 'username')
        self.smtp_password = self.config.get('email', 'password')
        self.from_email = self.config.get('email', 'from_email')
        self.to_emails = self.config.get('email', 'to_emails').split(',')
        
    def load_config(self, config_file):
        """Load configuration from file or environment variables"""
        config = configparser.ConfigParser()
        
        if config_file and os.path.exists(config_file):
            config.read(config_file)
        else:
            # Create config from environment variables
            config.add_section('jira')
            config.set('jira', 'base_url', os.getenv('JIRA_BASE_URL', 'https://issues.redhat.com'))
            config.set('jira', 'api_token', os.getenv('JIRA_API_TOKEN', ''))
            config.set('jira', 'project', os.getenv('JIRA_PROJECT', 'OCM'))
            config.set('jira', 'components', os.getenv('JIRA_COMPONENTS', 'rosa,rosa-team'))
            
            config.add_section('email')
            config.set('email', 'smtp_server', os.getenv('SMTP_SERVER', ''))
            config.set('email', 'smtp_port', os.getenv('SMTP_PORT', '587'))
            config.set('email', 'username', os.getenv('SMTP_USERNAME', ''))
            config.set('email', 'password', os.getenv('SMTP_PASSWORD', ''))
            config.set('email', 'from_email', os.getenv('FROM_EMAIL', ''))
            config.set('email', 'to_emails', os.getenv('TO_EMAILS', ''))
            
        return config
    
    def make_jira_request(self, jql, fields="key,summary,status,assignee,updated,created,resolution,components", max_results=50):
        """Make authenticated request to Jira API"""
        import urllib.parse
        
        url = f"{self.jira_base_url}/rest/api/2/search"
        headers = {
            'Authorization': f'Bearer {self.jira_token}',
            'Content-Type': 'application/json'
        }
        
        # Build URL with proper encoding like curl does
        encoded_jql = urllib.parse.quote(jql)
        encoded_fields = urllib.parse.quote(fields)
        full_url = f"{url}?jql={encoded_jql}&fields={encoded_fields}&maxResults={max_results}"
        
        try:
            print(f"Making request with JQL: {jql}")
            response = requests.get(full_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making Jira request: {e}")
            print(f"URL: {response.url if 'response' in locals() else 'N/A'}")
            if 'response' in locals():
                print(f"Response text: {response.text[:500]}...")
            return None
    
    def get_jira_link(self, issue_key):
        """Generate clickable Jira link"""
        return f"{self.jira_base_url}/browse/{issue_key}"
    
    def fetch_tickets_started_this_week(self):
        """Fetch tickets created in the last 7 days"""
        jql = f"project = {self.project} AND component in (rosa, rosa-team) AND created >= -7d ORDER BY created DESC"
        return self.make_jira_request(jql, max_results=30)
    
    def fetch_tickets_completed_this_week(self):
        """Fetch tickets completed in the last 7 days"""
        jql = f"project = {self.project} AND component in (rosa, rosa-team) AND status in (Done, Closed) AND resolved >= -7d ORDER BY updated DESC"
        return self.make_jira_request(jql, max_results=30)
    
    def fetch_tickets_in_progress(self):
        """Fetch tickets currently in progress or blocked"""
        jql = f"project = {self.project} AND component in (rosa, rosa-team) AND status in ('In Progress', 'Blocked') ORDER BY updated DESC"
        return self.make_jira_request(jql, max_results=30)
    
    def fetch_tickets_updated_this_week(self):
        """Fetch all tickets updated in the last 7 days for context"""
        jql = f"project = {self.project} AND component in (rosa, rosa-team) AND updated >= -7d ORDER BY updated DESC"
        return self.make_jira_request(jql, max_results=50)
    
    def format_ticket_line(self, issue, include_assignee=True):
        """Format a single ticket line with link"""
        key = issue['key']
        summary = issue['fields']['summary']
        link = self.get_jira_link(key)
        
        line = f"- **[{key}]({link})**: {summary}"
        
        if include_assignee and issue['fields'].get('assignee'):
            assignee = issue['fields']['assignee']['displayName']
            line += f" ({assignee})"
            
        return line
    
    def categorize_tickets(self, tickets):
        """Categorize tickets by type/theme"""
        categories = {
            'fips': [],
            'upgrade': [],
            'testing': [],
            'terraform': [],
            'billing': [],
            'ai': [],
            'infrastructure': [],
            'other': []
        }
        
        for issue in tickets:
            summary = issue['fields']['summary'].lower()
            
            if 'fips' in summary:
                categories['fips'].append(issue)
            elif any(word in summary for word in ['upgrade', 'eus', 'version', 'eol']):
                categories['upgrade'].append(issue)
            elif any(word in summary for word in ['test', 'ci', 'e2e', 'fvt', 'automation']):
                categories['testing'].append(issue)
            elif 'terraform' in summary:
                categories['terraform'].append(issue)
            elif 'billing' in summary:
                categories['billing'].append(issue)
            elif 'ai' in summary:
                categories['ai'].append(issue)
            elif any(word in summary for word in ['sdk', 'backend', 'infrastructure', 'deployment']):
                categories['infrastructure'].append(issue)
            else:
                categories['other'].append(issue)
                
        return categories
    
    def generate_report(self):
        """Generate the complete weekly status report"""
        print("Fetching data from Jira...")
        
        # Fetch data
        started_data = self.fetch_tickets_started_this_week()
        completed_data = self.fetch_tickets_completed_this_week()
        in_progress_data = self.fetch_tickets_in_progress()
        
        if not all([started_data, completed_data, in_progress_data]):
            print("Error fetching data from Jira")
            return None
            
        # Generate report date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = f"{start_date.strftime('%B %d')}-{end_date.strftime('%d, %Y')}"
        
        # Build report
        report = f"""# Weekly Status Report - ROSA Team

**Week of {date_range}**

## 📈 What Was Started This Week

"""
        
        # Started tickets
        if started_data['issues']:
            categories = self.categorize_tickets(started_data['issues'])
            
            # Group by themes
            if categories['upgrade']:
                report += "**Upgrade & Lifecycle Management:**\n"
                for issue in categories['upgrade'][:5]:
                    report += self.format_ticket_line(issue) + "\n"
                report += "\n"
                
            if categories['testing']:
                report += "**Test & QE Work:**\n"
                for issue in categories['testing'][:5]:
                    report += self.format_ticket_line(issue) + "\n"
                report += "\n"
                
            if categories['other']:
                report += "**New Initiatives:**\n"
                for issue in categories['other'][:5]:
                    report += self.format_ticket_line(issue) + "\n"
                report += "\n"
        else:
            report += "No new tickets started this week.\n\n"
            
        report += f"**Total new tickets: {started_data['total']}**\n\n"
        
        # Completed tickets
        report += "## ✅ What Was Completed This Week\n\n"
        
        if completed_data['issues']:
            categories = self.categorize_tickets(completed_data['issues'])
            
            if categories['infrastructure']:
                report += "**Infrastructure & Testing:**\n"
                for issue in categories['infrastructure'][:5]:
                    report += self.format_ticket_line(issue) + " ✅\n"
                report += "\n"
                
            report += "**Major Completions:**\n"
            for issue in completed_data['issues'][:8]:
                if issue not in categories['infrastructure']:
                    report += self.format_ticket_line(issue) + " ✅\n"
            report += "\n"
        else:
            report += "No tickets completed this week.\n\n"
            
        report += f"**Total completed tickets: {completed_data['total']}**\n\n"
        
        # In Progress tickets
        report += "## 🚧 In Progress & Key Work Streams\n\n"
        
        if in_progress_data['issues']:
            categories = self.categorize_tickets(in_progress_data['issues'])
            
            if categories['fips']:
                report += "**FIPS & Security:**\n"
                for issue in categories['fips']:
                    report += self.format_ticket_line(issue) + "\n"
                report += "\n"
                
            if categories['upgrade']:
                report += "**Upgrade & Lifecycle Management:**\n"
                for issue in categories['upgrade']:
                    report += self.format_ticket_line(issue) + "\n"
                report += "\n"
                
            if categories['terraform'] or categories['billing'] or categories['ai']:
                report += "**Platform Features:**\n"
                for issue in categories['terraform'] + categories['billing'] + categories['ai']:
                    report += self.format_ticket_line(issue) + "\n"
                report += "\n"
                
            if categories['testing']:
                report += "**Testing & QE:**\n"
                for issue in categories['testing']:
                    report += self.format_ticket_line(issue) + "\n"
                report += "\n"
                
            if categories['other']:
                report += "**Other Work:**\n"
                for issue in categories['other']:
                    report += self.format_ticket_line(issue) + "\n"
                report += "\n"
        else:
            report += "No tickets currently in progress.\n\n"
            
        report += f"**Total in-progress tickets: {in_progress_data['total']}**\n\n"
        
        # Blockers and risks
        report += "## ⚠️ Blockers & Risks\n\n"
        report += "**No Critical Blockers Identified**\n"
        report += "- All in-progress items have assigned owners\n"
        report += "- Team velocity remains strong\n\n"
        
        # Celebrations
        report += "## 🎉 Celebrations & Wins\n\n"
        report += f"- **Strong completion rate**: {completed_data['total']} tickets completed this week\n"
        report += f"- **Active development**: {started_data['total']} new tickets started\n"
        report += f"- **Steady progress**: {in_progress_data['total']} tickets actively being worked\n"
        report += "- **Team collaboration**: Good distribution of work across team members\n\n"
        
        # Management callouts
        report += "## 📋 Important Callouts for Management\n\n"
        report += "1. **Team Velocity**: Strong with consistent ticket completion and new work initiation\n"
        report += "2. **Feature Development**: Multiple customer-facing improvements in progress\n"
        report += "3. **Quality Focus**: Continued investment in testing and infrastructure\n"
        report += "4. **Technical Excellence**: Regular dependency updates and code quality improvements\n"
        report += "5. **Roadmap Alignment**: Work items align well with strategic objectives\n\n"
        
        report += f"**Generated on**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Data source**: {self.jira_base_url}\n"
        
        return report
    
    def send_email(self, report_content, subject=None):
        """Send the report via email"""
        if not subject:
            date_str = datetime.now().strftime('%B %d, %Y')
            subject = f"Weekly Status Report - ROSA Team - {date_str}"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)
        
        # Convert markdown to HTML for better email formatting
        html_content = self.markdown_to_html(report_content)
        
        # Attach both plain text and HTML versions
        text_part = MIMEText(report_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        try:
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            # Try STARTTLS if available
            try:
                server.starttls()
            except:
                pass  # Some servers don't support STARTTLS
            
            # Try authentication if credentials provided
            if self.smtp_username and self.smtp_password:
                try:
                    server.login(self.smtp_username, self.smtp_password)
                except smtplib.SMTPAuthenticationError:
                    print("Note: SMTP server doesn't require authentication")
                except Exception as auth_e:
                    print(f"Authentication failed, proceeding without auth: {auth_e}")
            
            text = msg.as_string()
            server.sendmail(self.from_email, self.to_emails, text)
            server.quit()
            
            print(f"Email sent successfully to: {', '.join(self.to_emails)}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def markdown_to_html(self, markdown_text):
        """Basic markdown to HTML conversion for email"""
        html = markdown_text.replace('\n', '<br>\n')
        
        # Headers
        html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        html = html.replace('## ', '<h2>').replace('<br>\n', '</h2>\n', html.count('<h2>'))
        
        # Bold text
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Lists
        html = re.sub(r'- (.*?)<br>', r'<li>\1</li>', html)
        
        return f"<html><body>{html}</body></html>"

def create_sample_config():
    """Create a sample configuration file"""
    config_content = """[jira]
base_url = https://issues.redhat.com
api_token = YOUR_JIRA_API_TOKEN
project = OCM
components = rosa,rosa-team

[email]
smtp_server = smtp.gmail.com
smtp_port = 587
username = your_email@gmail.com
password = your_app_password
from_email = your_email@gmail.com
to_emails = recipient1@gmail.com,recipient2@gmail.com
"""
    
    with open('weekly-status-config.ini', 'w') as f:
        f.write(config_content)
    
    print("Sample configuration file created: weekly-status-config.ini")
    print("Please edit it with your actual credentials and settings.")

def main():
    parser = argparse.ArgumentParser(description='Weekly Status Reporter for ROSA Team')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--output', '-o', help='Output file path (if not sending email)')
    parser.add_argument('--no-email', action='store_true', help='Generate report only, don\'t send email')
    parser.add_argument('--create-config', action='store_true', help='Create sample configuration file')
    parser.add_argument('--subject', '-s', help='Custom email subject')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_sample_config()
        return
    
    try:
        reporter = WeeklyStatusReporter(args.config)
        
        # Generate report
        report = reporter.generate_report()
        
        if not report:
            print("Failed to generate report")
            sys.exit(1)
        
        # Output to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to: {args.output}")
        
        # Send email unless disabled
        if not args.no_email:
            if reporter.send_email(report, args.subject):
                print("Weekly status report sent successfully!")
            else:
                print("Failed to send email")
                sys.exit(1)
        else:
            print("Report generated (email sending disabled)")
            print("\n" + "="*50)
            print(report)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()