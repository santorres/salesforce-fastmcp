# Salesforce FastMCP Connector

A FastMCP server providing 23 tools for interacting with Salesforce. This is a Python port of the Node.js Salesforce MCP connector, designed for deployment to FastMCP Cloud.

## Features

### Basic CRUD (8 tools)
- `salesforce_query` - Execute SOQL queries
- `salesforce_sobjects` - List available objects
- `salesforce_recent` - Fetch recent records
- `salesforce_search` - Execute SOSL searches
- `salesforce_describe` - Get object metadata
- `salesforce_create` - Create records
- `salesforce_update` - Update records
- `salesforce_delete` - Delete records

### Navigation & Relationships (3 tools)
- `salesforce_relationships` - Get related records
- `salesforce_lookup` - Search records by field
- `salesforce_hierarchy` - Navigate parent/child relationships

### Analytics (3 tools)
- `salesforce_aggregate` - Statistical analysis (COUNT, SUM, AVG, etc.)
- `salesforce_reports` - Access Salesforce reports
- `salesforce_trend_analysis` - Time-based trend analysis

### Business Intelligence (4 tools)
- `salesforce_pipeline` - Sales pipeline analysis
- `salesforce_case_insights` - Support case metrics
- `salesforce_lead_funnel` - Lead conversion funnel
- `salesforce_opportunities_by_partner` - Find opportunities by partner name (handles lookup syntax automatically)

## Setup

### Prerequisites
- Python 3.10+
- A Salesforce org with API access
- Salesforce Session ID (SID) or Access Token

### Installation

1. Clone or download this directory

2. Create a virtual environment:
   ```bash
   cd salesforce-fastmcp
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Salesforce credentials
   ```

### Getting Salesforce Credentials

#### Option 1: Session ID from Browser
1. Log into Salesforce in your browser
2. Open Developer Tools > Application > Cookies
3. Find the `sid` cookie value
4. Your base URL is: `https://your-instance.my.salesforce.com/services/data/v59.0`

#### Option 2: Salesforce CLI
```bash
sf org display --target-org your-org
# Use the "Access Token" and "Instance URL" values
```

#### Option 3: OAuth 2.0 (Recommended for Production)
Use a Salesforce Connected App with OAuth 2.0 flow to obtain refresh tokens for automatic token renewal.

## Running the Server

### Local stdio Mode (for Claude Desktop)
```bash
python server.py
```

### Local HTTP Mode (for testing)
```bash
fastmcp run server.py:mcp --transport http --port 8000
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "salesforce": {
      "command": "python",
      "args": ["/path/to/salesforce-fastmcp/server.py"],
      "env": {
        "SALESFORCE_BASE_URL": "https://your-instance.my.salesforce.com/services/data/v59.0",
        "SALESFORCE_SID": "your-session-id"
      }
    }
  }
}
```

## Two-Laptop Setup (Remote Connection)

If you can't run LLMs on the Salesforce-authenticated laptop, you can run the server on that laptop and connect from another machine via Tailscale/VPN:

### Server Laptop (where Salesforce authentication works)

1. **Get a fresh Salesforce Session ID (SID)**:
   ```bash
   # Method 1: Extract from Chrome cookies
   cd /path/to/salesforce-fastmcp
   node Scripts/extract-sid.js
   
   # Method 2: Or use Salesforce CLI
   sf org display --target-org your-org
   ```

2. **Test the SID**:
   ```bash
   node Scripts/test-token.js <your-sid>
   ```

3. **Update .env** with the working SID:
   ```bash
   cp .env.example .env
   # Edit .env with SALESFORCE_BASE_URL and SALESFORCE_SID
   ```

4. **Run the server** (ensures MCP_TRANSPORT is streamable-http):
   ```bash
   # Option A: Default streamable-http on port 8000
   python3 server.py
   
   # Option B: Explicit configuration
   MCP_TRANSPORT=streamable-http MCP_PORT=8000 python3 server.py
   ```

### AI Laptop (where Claude Desktop runs)

The server is now accessible via your Tailscale IP (e.g., `100.121.106.95:8000`). Two options to connect Claude Desktop:

**Option 1: Using wrapper.sh (recommended)**
```json
{
  "mcpServers": {
    "salesforce": {
      "command": "/path/to/salesforce-fastmcp/wrapper.sh"
    }
  }
}
```

The wrapper converts Claude Desktop's stdio to HTTP requests to the remote server. Customize the server IP via environment variable:
```bash
# In your shell environment or Claude settings:
export SALESFORCE_MCP_URL="http://<server-ip>:8000/mcp"
```

**Option 2: Direct HTTP connection** (if your Claude Desktop version supports it)
```json
{
  "mcpServers": {
    "salesforce": {
      "url": "http://<server-ip>:8000/mcp"
    }
  }
}
```

### Troubleshooting Remote Connection

- **"Connection refused" in wrapper.sh**: Ensure server is running on the other laptop and port 8000 is accessible via Tailscale
- **Tailscale IP changed**: Update `wrapper.sh` or the `SALESFORCE_MCP_URL` environment variable
- **Token expired**: Run `Scripts/extract-sid.js` again on the server laptop, update `.env`, and restart `server.py`

## Deploying to FastMCP Cloud

1. Push this project to a GitHub repository

2. Visit [fastmcp.cloud](https://fastmcp.cloud) and sign in

3. Connect your GitHub repository

4. Set environment variables in the FastMCP Cloud dashboard:
   - `SALESFORCE_BASE_URL`
   - `SALESFORCE_SID` (or `SALESFORCE_ACCESS_TOKEN`)

5. Deploy and get your cloud URL

### Using the Cloud-Hosted Server

Once deployed, you can connect to your server via the cloud URL provided by FastMCP.

## Example Usage

### Query Accounts
```
Use the salesforce_query tool with:
q: "SELECT Id, Name, Industry FROM Account LIMIT 10"
```

### Search for Contacts
```
Use the salesforce_lookup tool with:
object_name: "Contact"
search_term: "John"
search_fields: ["Name", "Email"]
```

### Get Pipeline Analysis
```
Use the salesforce_pipeline tool with:
timeframe: "THIS_QUARTER"
include_forecasting: true
```

### Aggregate Opportunity Data
```
Use the salesforce_aggregate tool with:
object_name: "Opportunity"
aggregates: [{"function": "SUM", "field": "Amount", "alias": "TotalValue"}]
group_by: "StageName"
```

### Find Opportunities by Partner
```
Use the salesforce_opportunities_by_partner tool with:
partner_name: "Inetum - Spain (Partner)"
is_closed: false
start_date: "2026-01-01"
```

## Working with Lookup Fields (IMPORTANT)

Salesforce lookup fields (like `Partner__c`, `Account__c`) store **record IDs**, not names. When querying by name, you must use the **relationship syntax** with `__r`:

### ❌ WRONG - This will fail with "invalid ID field" error:
```sql
SELECT Id, Name FROM Opportunity WHERE Partner__c = 'Inetum - Spain (Partner)'
```

### ✅ CORRECT - Use the relationship syntax:
```sql
SELECT Id, Name FROM Opportunity WHERE Partner__r.Name = 'Inetum - Spain (Partner)'
```

### Common Lookup Fields in Opportunity:
- `Partner__c` → use `Partner__r.Name` for partner name
- `Account__c` → use `Account.Name` or `Account__r.Name`
- `Owner__c` → use `Owner.Name`

### Helper Tool: salesforce_opportunities_by_partner

Instead of manually constructing SOQL queries with relationship syntax, use the dedicated helper tool:

```
Use the salesforce_opportunities_by_partner tool with:
partner_name: "Inetum - Spain (Partner)"
is_closed: false
stage_name: "Negotiation"
min_amount: 50000
start_date: "2026-01-01"
end_date: "2026-12-31"
limit: 50
```

This tool automatically handles the lookup relationship syntax and provides additional filtering options.

## Authentication Notes

- Session IDs expire after ~24 hours of inactivity
- For production use, consider implementing OAuth 2.0 with refresh tokens
- Never commit your `.env` file to version control

## Troubleshooting

### "INVALID_SESSION_ID" Error
Your session has expired. Obtain a new session ID and update your `.env` file.

### "Missing required environment variables"
Ensure both `SALESFORCE_BASE_URL` and `SALESFORCE_SID` (or `SALESFORCE_ACCESS_TOKEN`) are set.

### API Version Errors
Update the API version in your base URL (e.g., `v59.0` to `v60.0`) to match your Salesforce org.

## License

MIT
