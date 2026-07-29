from database import SessionLocal
from models import KnowledgeBase


SEED_ARTICLES = [
    {
        "title": "Resetting Your Account Password",
        "content": """If you have forgotten your account password, you can reset it by following these steps:
1. Go to the login page and click "Forgot Password"
2. Enter your registered email address
3. Check your inbox for a password reset link (valid for 30 minutes)
4. Click the link and enter your new password
5. Confirm the new password and submit

If you do not receive the reset email within 5 minutes, check your spam folder. If the issue persists, contact support with your registered email address.""",
        "category": "account",
        "tags": "password,reset,login,account"
    },
    {
        "title": "Billing and Invoice FAQ",
        "content": """Billing Cycle: Invoices are generated on the 1st of each month for the previous month's usage.
Payment Methods: We accept Visa, Mastercard, American Express, and PayPal.
Payment Terms: Net 15 from invoice date.
Late Payment: A 1.5% monthly late fee applies after 15 days past due.

To update your billing information, go to Settings > Billing > Payment Methods.
To download an invoice, go to Settings > Billing > Invoices.
For billing disputes, please contact billing@company.com with your account details and invoice number.""",
        "category": "billing",
        "tags": "billing,invoice,payment,subscription"
    },
    {
        "title": "Troubleshooting API Connection Issues",
        "content": """If you are experiencing API connection issues, try the following steps:

1. Verify your API key is correct and active in Settings > API Keys
2. Check that your IP address is whitelisted (Settings > Security > IP Whitelist)
3. Ensure you are using the correct API endpoint: https://api.company.com/v2/
4. Verify your request format matches our API documentation
5. Check the API status page at https://status.company.com for any ongoing incidents

Common error codes:
- 401: Invalid or missing API key
- 403: IP not whitelisted or insufficient permissions
- 429: Rate limit exceeded (1000 requests/minute)
- 500: Internal server error - contact support

For rate limiting, consider implementing exponential backoff in your integration.""",
        "category": "technical",
        "tags": "api,connection,technical,error,integration"
    },
    {
        "title": "Setting Up User Roles and Permissions",
        "content": """The platform supports four user roles:

1. Admin: Full access to all features and settings
2. Manager: Can manage users and projects, view reports
3. Editor: Can create and edit content but cannot manage users
4. Viewer: Read-only access

To set up roles:
1. Go to Settings > Users
2. Select a user from the list
3. Click "Edit Permissions"
4. Choose the appropriate role from the dropdown
5. Click Save

Note: Only Admins can create or delete other Admin accounts.
Role changes take effect immediately upon saving.""",
        "category": "account",
        "tags": "roles,permissions,users,admin"
    },
    {
        "title": "Guided Onboarding for New Users",
        "content": """Welcome to the platform! Here is a quick onboarding guide:

Day 1: Complete your profile and verify your email
- Add a profile photo and set your display name
- Configure notification preferences

Week 1: Explore key features
- Create your first project
- Invite team members (up to 5 on the Starter plan)
- Set up your first integration

Month 1: Optimize your workflow
- Configure automation rules
- Set up custom dashboards
- Review usage analytics

For guided walkthroughs, click the "Help" icon in the top-right corner of any page.
Our knowledge base and video tutorials are available at docs.company.com.""",
        "category": "general",
        "tags": "onboarding,new user,getting started,guide"
    },
    {
        "title": "Data Export and Backup Procedures",
        "content": """Exporting Your Data:

You can export your data in CSV, JSON, or PDF formats from the Settings menu.

Available exports:
- Project data: Settings > Data > Export Projects
- User activity logs: Settings > Data > Export Logs
- Analytics reports: Analytics > Export

Backup Schedule:
- Automatic daily backups are maintained for 30 days
- Weekly backups are retained for 3 months
- Monthly backups are retained for 12 months

To request a manual backup or data deletion, contact privacy@company.com.
Enterprise customers can request custom backup schedules through their account manager.""",
        "category": "general",
        "tags": "export,backup,data,privacy"
    },
    {
        "title": "Common Error Messages and Solutions",
        "content": """Here are solutions to frequently encountered error messages:

"Storage limit exceeded": Upgrade your plan or delete unused files from Settings > Storage.
"Invalid email format": Ensure the email address contains @ and a valid domain.
"Session expired": You have been logged out due to inactivity. Log in again.
"Two-factor authentication required": Complete 2FA setup in Settings > Security.
"Feature not available on your plan": Upgrade your subscription to access this feature.
"Concurrent session limit reached": Log out from other devices or contact support.

If an error persists after trying the suggested solution, please submit a support ticket with a screenshot of the error message and the steps you took before encountering it.""",
        "category": "technical",
        "tags": "errors,troubleshooting,common issues"
    },
    {
        "title": "Subscription Plans and Upgrading",
        "content": """Available Plans:

Starter: $29/month - Up to 5 users, 10 projects, basic analytics
Professional: $99/month - Up to 25 users, unlimited projects, advanced analytics
Enterprise: Custom pricing - Unlimited users, dedicated support, custom integrations

Upgrading Your Plan:
1. Go to Settings > Billing > Plan
2. Review the available plans and features
3. Select your new plan
4. Confirm the change (prorated billing applies)

Downgrading: You can downgrade at any time. Changes take effect at the next billing cycle.
Cancellation: Cancel anytime from Settings > Billing > Plan. Your data will be available for 30 days after cancellation.

For Enterprise inquiries, contact sales@company.com.""",
        "category": "billing",
        "tags": "plans,subscription,upgrade,pricing"
    },
    {
        "title": "Report a Bug or Feature Request",
        "content": """To report a bug or request a feature:

Bug Reports:
1. Go to Help > Report a Bug
2. Describe the issue in detail, including steps to reproduce
3. Attach screenshots or screen recordings if possible
4. Include your browser version and OS details
5. Select the severity: Low, Medium, High, or Critical

Feature Requests:
1. Go to Help > Suggest a Feature
2. Describe what you would like to see added
3. Explain how this would benefit your workflow
4. Upvote existing feature requests at feedback.company.com

Our team reviews bug reports within 24 hours (Critical: 4 hours) and feature requests monthly.
You will receive updates via email when your report status changes.""",
        "category": "general",
        "tags": "bug,feature,request,report,feedback"
    },
    {
        "title": "Integrating with Third-Party Tools",
        "content": """Supported Integrations:

Slack: Receive notifications and updates in your Slack workspace
- Connect: Settings > Integrations > Slack
- Configure which events trigger notifications

GitHub: Link repositories and track commits
- Connect: Settings > Integrations > GitHub
- Requires repo read access

Jira: Sync issues and project status
- Connect: Settings > Integrations > Jira
- Two-way sync supported

Zapier: Connect with 2000+ apps
- Connect: Settings > Integrations > Zapier
- Custom workflows supported

Webhook: Build custom integrations
- Endpoint: Configure in Settings > Integrations > Webhooks
- Supports JSON payloads with HMAC-SHA256 signing

Each integration can be enabled or disabled independently. API rate limits apply to integration requests.""",
        "category": "technical",
        "tags": "integrations,third-party,slack,github,jira,zapier,webhook"
    },
]


def seed_knowledge_base(db=None):
    if db is None:
        db = SessionLocal()
    try:
        existing = db.query(KnowledgeBase).count()
        if existing > 0:
            return
        for article in SEED_ARTICLES:
            kb = KnowledgeBase(**article)
            db.add(kb)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_knowledge_base()
