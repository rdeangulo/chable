# Residere WhatsApp Assistant

An intelligent virtual assistant for Residere real estate sales, capable of handling customer inquiries via WhatsApp.

## Features

- Customer engagement via WhatsApp
- Property information and recommendations
- Lead qualification and collection
- Image sharing capabilities
- Voice note transcription
- Block incoming spam numbers via the monitor interface

## Setup

1. Install dependencies:
   `
   pip install -r requirements.txt
   `

2. Configure environment variables in .env file. Ensure `TWILIO_STATUS_CALLBACK_URL` points to your webhook endpoint (e.g. `https://your-server.com/api/monitor/webhook/twilio`).

3. Apply database migrations using Alembic:
   `
   alembic upgrade head
   `

4. Manage database tables directly (optional):
   `
   python manage_db.py --help
   `
5. Run the application:
   `
   uvicorn app.main:app --reload
   `

## Deploying to Heroku

1. Create a Heroku app:
   `
   heroku create your-app-name
   `

2. Add PostgreSQL:
   `
   heroku addons:create heroku-postgresql:mini
   `

3. Configure environment variables:
   `
   heroku config:set OPENAI_API_KEY=your_key_here
   heroku config:set ASSISTANT_ID=your_assistant_id_here
   # Add other required variables
   `

4. Deploy:
   `
   git push heroku main
   `

5. Run migrations on Heroku:
   `
   heroku run alembic upgrade head
   `

## Blocking Spam

Use the monitor interface to block abusive numbers. Blocked conversations are listed in a dedicated **Spam** section at the bottom of the monitor. Incoming messages from these numbers are ignored.

To block or unblock a conversation, select it in the monitor and click the **Block** button in the conversation header. When a number is blocked the button changes to **Unblock**.

## Embeddable Widget

Expose the assistant on third‑party sites with a customizable widget. Set the
`ALLOWED_WIDGET_HOSTS` environment variable to a comma‑separated list of hostnames
allowed to load the widget.

Include the following snippet on an approved site:

```html
<div id="residere-widget"></div>
<script src="https://your-server.com/api/widget/embed.js?width=100%25&height=500px" async></script>
```

Query parameters let you customise the iframe:

- `width` – iframe width (default `100%`)
- `height` – iframe height (default `500px`)
- `max_width` – maximum width of the iframe (default `400px`)
- `border` – CSS border value (default `0`)

The widget validates the request origin and sets the `Access-Control-Allow-Origin`
header using the provided origin if it matches one of the hosts listed in
`ALLOWED_WIDGET_HOSTS`.

## License

[Your license information]
#   r e s i d e r e 
 
 
