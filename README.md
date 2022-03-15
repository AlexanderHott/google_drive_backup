# Auto Back-up with Google Drive

## Setup

Go to [Google Cloud](https://cloud.google.com). Click on Console, hover over APIs and Services then click Credentials. Create a project, select the project (if not already selected) and click on OAuth consent screen, select External and click on Create.

Give the app a name, a user support email, and a Developer contact email. Click save and continue. Skip adding scopes. Add your email as a test user, click save and continue.

Go back to the dashboard, click Create Credentails, click OAuth client ID, click Desktop App, enter a name, then click create.

Rename the `.env.example` file to `.env` and update the two values with the newly created credentials (no quotes).