# WhatsApp Automation

An automated system for sending scheduled polls/messages to a WhatsApp group. This project uses GreenAPI to interact with WhatsApp, GitHub Actions for workflow execution, and Pipedream for cron-based scheduling triggers with Helsinki timezone, because GitHub Actions does not meet the requirements of precisely timed triggers (unpredictable delays).

## Message and Poll Variants

- **Canceled Day**  
  - Message:  
    ```
    Huomio, tänään treeni on peruttu!
    ```
  - Sent as a simple WhatsApp message.

- **Exceptional Day**  
  - Poll:  
    ```
    Huomio, poikkeuksellinen treeni! Tänään vääntämään klo {startTime}?
    ```
  - Sent as a WhatsApp poll with options:
    - Kyllä
    - Ei

- **Regular Training Day**  
  - Poll:  
    ```
    Tänään vääntämään klo {startTime}?
    ```
  - Sent as a WhatsApp poll with options:
    - Kyllä
    - Ei

- **No Training**  
  - No message is sent; script exits with info.

## Technology Stack

### GreenAPI

GreenAPI is a WhatsApp API service that enables programmatic interaction with WhatsApp, including sending polls to groups.

- **How to use GreenAPI**: [GreenAPI before start](https://green-api.com/en/docs/before-start/)
- **Documentation**: [sendPoll](https://green-api.com/en/docs/api/sending/SendPoll/), [sendMessage](https://green-api.com/en/docs/api/sending/SendMessage/)

GreenAPI uses personal phone number as an instance. It works as an additional virtual device in cloud for WhatsApp account.

The script constructs the API URL as:
```
{GREENAPI_URL}/waInstance{INSTANCE_ID}/sendPoll/{API_TOKEN}
```

### GitHub Actions

GitHub Actions handles the automated execution of the poll script.

#### Setup Instructions

1. **Fork or clone this repository** to your GitHub account

2. **Create a GitHub Classic Personal Access Token**:
   - Go to **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
   - Click **Generate new token (classic)**
   - Give it a descriptive name (e.g., "WhatsApp Poll Automation")
   - Select scopes: `repo` (full control of private repositories)
   - Click **Generate token** and copy it immediately

3. **Configure Repository Secrets**:
   - Navigate to your repository → **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret** and add each of the following:

   | Secret Name | Description |
   |-------------|-------------|
   | `GREENAPI_URL` | Base URL for GreenAPI (e.g., `https://api.green-api.com`) |
   | `GREENAPI_INSTANCE_ID` | Your GreenAPI instance ID |
   | `GREENAPI_API_TOKEN` | Your GreenAPI API token |
   | `WHATSAPP_CHAT_ID` | Target WhatsApp group ID (format: `1234567890@g.us`) |
   | `SANITY_SCHEDULE_URL` | URL to fetch training schedule from Sanity |

4. **Enable GitHub Actions**:
   - Go to the **Actions** tab in your repository
   - If prompted, enable workflows for the repository

5. **Test the Workflow**:
   - Go to **Actions** → **WhatsApp Poll Automation**
   - Click **Run workflow** → Enable **Force run** checkbox → **Run workflow** (with current code it will works only on Tuesday and Saturday)

### Pipedream

Pipedream provides an alternative automation platform for triggering the GitHub Actions workflow on a schedule. Useful service for testing cron intervals: https://cronjob.xyz/

#### Workflow: Tuesday and Friday Poll Trigger

**Setup Instructions**:

1. **Create a new Pipedream workflow**:
   - Go to [Pipedream](https://pipedream.com/) and sign in
   - Click **New Workflow**

2. **Add a Cron Schedule trigger**:
   - Select **Schedule → Custom** module as the trigger, use Helsinki timezone
   - Configure the time and day of the week (Tuesday at 13:00 for instance, if training starts at 18:00)
   - Repeat steps above for Saturday (10:00, if training starts at 12:00)

3. **Add an HTTP Request action**:
   - Add a new step → Search and add **POST_request** module
   - Configure:
     - **Method**: `POST`
     - **URL**: `https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/daily-poll.yml/dispatches`
     - **Headers**:
       ```
       User-Agent: pipedream/1
       Authorization: Bearer {YOUR_GITHUB_PAT}
       Content-Type: application/json
       Accept: application/vnd.github+json
       ```
     - **Body**:
       ```json
       {"ref": "main"}

       or

       {"ref": "master"}
       ```

3. **Deploy the workflow**

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GREENAPI_URL` | Yes | Base URL for GreenAPI service |
| `GREENAPI_INSTANCE_ID` | Yes | Your GreenAPI instance identifier |
| `GREENAPI_API_TOKEN` | Yes | Authentication token for GreenAPI |
| `WHATSAPP_CHAT_ID` | Yes | WhatsApp group ID to send polls to |
| `SANITY_SCHEDULE_URL` | Yes | URL to fetch training schedule from Sanity |

## Local Development

1. Clone the repository
2. Create a `.env` file with the required environment variables:
   ```
   GREENAPI_URL=https://api.green-api.com
   GREENAPI_INSTANCE_ID=your_instance_id
   GREENAPI_API_TOKEN=your_api_token
   WHATSAPP_CHAT_ID=your_group_id@g.us
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the script:
   ```bash
   python main.py
   ```

## Development & Testing

- To use sample schedule data (for testing), set `USE_SAMPLE_RESPONSE = True` in `main.py`.

## License

MIT