import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import google.generativeai as genai

# --- Configuration ---
JIRA_PROJECT = "OCM"
JIRA_COMPONENTS = ["Rosa", "rosa-team"]  # Components to filter issues
DAYS_PAST = 7  # Changed from WEEKS_PAST to DAYS_PAST

# --- Environment Variable Setup ---
# Set these environment variables for security:
# export JIRA_SERVER_URL="https://issues.redhat.com"
# export JIRA_BEARER_TOKEN="your_jira_bearer_token"
# export GEMINI_API_KEY="your_gemini_api_key"
# export SMTP_SERVER="smtp.corp.redhat.com"  # or your company's SMTP server
# export SMTP_PORT="587"
# export EMAIL_USER="your-email@company.com"
# export EMAIL_PASSWORD="your-app-password"  # Use app password for Gmail
# export MANAGER_EMAIL="manager@company.com"

JIRA_SERVER_URL = os.getenv("JIRA_SERVER_URL")
JIRA_BEARER_TOKEN = os.getenv("JIRA_BEARER_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Validate environment variables
required_vars = [JIRA_SERVER_URL, JIRA_BEARER_TOKEN, GEMINI_API_KEY]
if not all(required_vars):
    print("Error: Please set all required environment variables:")
    print("JIRA_SERVER_URL, JIRA_BEARER_TOKEN, GEMINI_API_KEY")
   # print("  EMAIL_USER, EMAIL_PASSWORD, MANAGER_EMAIL")
    #print("Optional: SMTP_SERVER, SMTP_PORT (defaults to Gmail)")
    exit(1)

# --- Jira API Interaction ---
def fetch_jira_issues():
    """
    Connects to Jira using a bearer token and fetches issues from the last 7 days.
    """
    try:
        jira_api_search_url = f"{JIRA_SERVER_URL}/rest/api/2/search"

        headers = {
            "Authorization": f"Bearer {JIRA_BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        print(f"Attempting to connect to Jira at {jira_api_search_url}")

        # Calculate the start date for the query (last 7 days)
        start_date = (datetime.now() - timedelta(days=DAYS_PAST)).strftime('%Y-%m-%d')
        print(f"Fetching issues updated since: {start_date}")

        # Construct the JQL query for last 7 days
        components_str = ", ".join([f'"{c}"' for c in JIRA_COMPONENTS])
        jql_query = (
            f'project = "{JIRA_PROJECT}" AND component in ({components_str}) '
            f'AND updated >= "{start_date}" ORDER BY updated DESC'
        )
        print(f"JQL Query: {jql_query}")

        # Parameters for the Jira search API - include changelog
        params = {
            "jql": jql_query,
            "maxResults": 200,  # Increased limit
            "fields": "key,summary,status,assignee,reporter,issuetype,created,updated,priority,description",
            "expand": "changelog"  # This is key to get status change history
        }

        response = requests.get(jira_api_search_url, headers=headers, params=params)
        response.raise_for_status()

        jira_response_data = response.json()
        issues = jira_response_data.get("issues", [])
        print(f"Found {len(issues)} Jira issues from the last {DAYS_PAST} days.")

        return issues

    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred during Jira fetch: {err}")
        print(f"Response body: {err.response.text}")
        return None
    except requests.exceptions.RequestException as err:
        print(f"Request error occurred during Jira fetch: {err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during Jira fetch: {e}")
        return None

def analyze_status_transitions(issues):
    """
    Analyze which issues moved to specific statuses in the past 7 days
    """
    status_transitions = {
        "moved_to_in_progress": [],
        "moved_to_review": [],
        "moved_to_closed": [],
        "moved_to_done": [],
        "moved_to_resolved": [],
        "blocked_issues": [],
        "all_issues": []  # For context
    }
    
    cutoff_date = datetime.now() - timedelta(days=DAYS_PAST)
    
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"]["summary"]
        current_status = issue["fields"]["status"]["name"]
        assignee = issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "Unassigned"
        priority = issue["fields"]["priority"]["name"] if issue["fields"]["priority"] else "None"
        issue_type = issue["fields"]["issuetype"]["name"]
        description = issue["fields"].get("description", "")
        
        # Store all issues for context
        status_transitions["all_issues"].append({
            "key": key,
            "summary": summary,
            "current_status": current_status,
            "assignee": assignee,
            "priority": priority,
            "type": issue_type,
            "description": description
        })
        
        # Check for blocked issues
        if "blocked" in current_status.lower() or priority == "Blocker":
            status_transitions["blocked_issues"].append({
                "key": key,
                "summary": summary,
                "current_status": current_status,
                "assignee": assignee,
                "priority": priority,
                "type": issue_type
            })
        
        # Check changelog for status transitions
        changelog = issue.get("changelog", {})
        histories = changelog.get("histories", [])
        
        for history in histories:
            # Parse the created date of this history entry
            created_str = history["created"]
            # Remove timezone info and parse (JIRA format: 2024-01-15T10:30:45.123+0000)
            created_date = datetime.strptime(created_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            
            # Only consider changes in the last 7 days
            if created_date >= cutoff_date:
                for item in history.get("items", []):
                    if item.get("field") == "status":
                        from_status = item.get("fromString", "")
                        to_status = item.get("toString", "")
                        
                        issue_info = {
                            "key": key,
                            "summary": summary,
                            "from_status": from_status,
                            "to_status": to_status,
                            "date": created_date.strftime('%Y-%m-%d %H:%M'),
                            "assignee": assignee,
                            "priority": priority,
                            "type": issue_type,
                            "description": description
                        }
                        
                        # Check for transitions to target statuses
                        to_status_lower = to_status.lower()
                        
                        if "in progress" in to_status_lower or "progress" in to_status_lower:
                            status_transitions["moved_to_in_progress"].append(issue_info)
                        elif "review" in to_status_lower or "code review" in to_status_lower:
                            status_transitions["moved_to_review"].append(issue_info)
                        elif "closed" in to_status_lower:
                            status_transitions["moved_to_closed"].append(issue_info)
                        elif "done" in to_status_lower:
                            status_transitions["moved_to_done"].append(issue_info)
                        elif "resolved" in to_status_lower:
                            status_transitions["moved_to_resolved"].append(issue_info)
    
    return status_transitions

# --- Gemini API Interaction ---
def generate_report_with_gemini(status_transitions):
    """
    Sends the status transition data to the Gemini API to generate a formatted report.
    """
    if not status_transitions["all_issues"]:
        return "No Jira data available to generate a report."

    # Prepare data for Gemini
    report_data = {
        "started_items": status_transitions["moved_to_in_progress"],
        "completed_items": status_transitions["moved_to_closed"] + status_transitions["moved_to_done"] + status_transitions["moved_to_resolved"],
        "review_items": status_transitions["moved_to_review"],
        "blocked_items": status_transitions["blocked_issues"],
        "all_context": status_transitions["all_issues"][:20]  # Limit context for token efficiency
    }

    # Enhanced prompt for the specific format
    prompt_text = f"""
You are a technical project manager creating a weekly status report for the ROSA (Red Hat OpenShift Service on AWS) team. 

Based on the JIRA data provided, create a weekly status report that follows this EXACT format:

**Started**
[List items that moved to "In Progress" this week. For each item, include the JIRA key, title, and a brief explanation of what was started and why. Use narrative style like "We moved this to In Progress, given..." or "Team is working on..."]

**Completed** 
[List items that were completed/closed this week. Include JIRA key, title, and brief description of what was accomplished]

**Blocked / Off-track**
[List any items that are blocked or have blocker priority. Include JIRA key and explanation of the blocking issue]

**Risks**
[Identify potential risks based on the data - things like multiple blocked items, critical issues not progressing, etc.]

**Celebrations**
[Highlight significant accomplishments, particularly from completed items. Mention team members by name when possible]

Here is the JIRA data from the past {DAYS_PAST} days:

STARTED ITEMS (moved to In Progress):
{json.dumps(report_data["started_items"], indent=2)}

COMPLETED ITEMS:
{json.dumps(report_data["completed_items"], indent=2)}

REVIEW ITEMS:
{json.dumps(report_data["review_items"], indent=2)}

BLOCKED ITEMS:
{json.dumps(report_data["blocked_items"], indent=2)}

Please write the report in a conversational, manager-friendly tone. Focus on business impact and progress. Use the exact section headers shown above (Started, Completed, Blocked / Off-track, Risks, Celebrations).
Report covers OCM project activity for Rosa and rosa-team components from {(datetime.now() - timedelta(days=DAYS_PAST)).strftime('%B %d, %Y')} to {datetime.now().strftime('%B %d, %Y')}.
"""

    try:
        print("\nSending data to Gemini API for report generation...")
        response = model.generate_content(prompt_text)
        return response.text

    except Exception as err:
        print(f"An unexpected error occurred: {err}")
        return f"Failed to generate report: An unexpected error - {err}"

# --- Email Functionality ---
def send_report_email(report_content, jira_issues_count):
    """
    Sends the generated report to the manager via email.
    """
    try:
        # Get email environment variables
        EMAIL_USER = os.getenv("EMAIL_USER")
        EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
        MANAGER_EMAIL = os.getenv("MANAGER_EMAIL")
        SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        
        if not all([EMAIL_USER, EMAIL_PASSWORD, MANAGER_EMAIL]):
            print("Email environment variables not set. Skipping email send.")
            return False
        
        print(f"Attempting to send email to: {MANAGER_EMAIL}")
        print(f"Using SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = MANAGER_EMAIL
        msg['Subject'] = f"Weekly Status Report - OCM ROSA Team ({datetime.now().strftime('%B %d, %Y')})"
        
        # Email body
        email_body = f"""
Dear Team,

Please find the weekly status report for the OCM ROSA team below.

Report Summary:
- Period: Last {DAYS_PAST} days ({(datetime.now() - timedelta(days=DAYS_PAST)).strftime('%B %d, %Y')} to {datetime.now().strftime('%B %d, %Y')})
- Total Issues Analyzed: {jira_issues_count}
- Components: {', '.join(JIRA_COMPONENTS)}

{report_content}

Best regards,
Automated JIRA Reporting System
"""
        
        msg.attach(MIMEText(email_body, 'plain'))
        
        # Try different SMTP configurations for Red Hat
        smtp_configs = [
            # Red Hat internal SMTP (no auth)
            {"server": "smtp.corp.redhat.com", "port": 25, "use_auth": False, "use_tls": False},
            # Red Hat internal SMTP with TLS
            {"server": "smtp.corp.redhat.com", "port": 587, "use_auth": False, "use_tls": True},
            # Red Hat with authentication
            {"server": "smtp.corp.redhat.com", "port": 587, "use_auth": True, "use_tls": True},
            # Gmail fallback
            {"server": "smtp.gmail.com", "port": 587, "use_auth": True, "use_tls": True}
        ]
        
        for config in smtp_configs:
            try:
                print(f"Trying SMTP config: {config['server']}:{config['port']} (auth={config['use_auth']}, tls={config['use_tls']})")
                
                server = smtplib.SMTP(config["server"], config["port"])
                
                if config["use_tls"]:
                    server.starttls()
                
                if config["use_auth"]:
                    server.login(EMAIL_USER, EMAIL_PASSWORD)
                
                text = msg.as_string()
                server.sendmail(EMAIL_USER, MANAGER_EMAIL, text)
                server.quit()
                
                print(f"✅ Report successfully sent to {MANAGER_EMAIL}")
                return True
                
            except Exception as e:
                print(f"❌ Failed with {config['server']}: {e}")
                continue
        
        print("❌ All SMTP configurations failed.")
        return False
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Formatted Weekly Report Generation...")
    print(f"Configuration: Fetching last {DAYS_PAST} days of issues")
    print(f"Target: {JIRA_PROJECT} project, components: {', '.join(JIRA_COMPONENTS)}")
    
    # Fetch Jira issues
    jira_issues = fetch_jira_issues()

    if jira_issues:
        # Analyze status transitions
        transitions = analyze_status_transitions(jira_issues)
        
        # Generate report
        report_content = generate_report_with_gemini(transitions)
        
        print("\n" + "="*80)
        print("WEEKLY STATUS REPORT")
        print("="*80)
        print(report_content)
        print("="*80)
        
        # Send email
        send_report_email(report_content, len(jira_issues))
        
    else:
        print("Could not fetch Jira issues. Report generation aborted.")