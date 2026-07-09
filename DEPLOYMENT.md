# Deployment Guide for Buzz Bee Naturals

This document covers hosting the Flask backend and the static site.

## Step 1: Push code to GitHub
Your project is already pushed to:

https://github.com/veronicah00/buzzbee.git

## Step 2: Deploy the Flask backend to Render
Render is a simple host for Python web apps.

1. Go to https://dashboard.render.com/
2. Create an account or sign in.
3. Click `New` → `Web Service`.
4. Connect your GitHub account and select `veronicah00/buzzbee`.
5. Configure the service:
   - **Name**: buzzbee-backend
   - **Region**: Choose the nearest region
   - **Branch**: `master`
   - **Root Directory**: leave empty
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
6. Add environment variables:
   - `ADMIN_PHONE` = `+254735754185`
   - `TWILIO_ACCOUNT_SID` = `<your Twilio account SID>`
   - `TWILIO_AUTH_TOKEN` = `<your Twilio auth token>`
   - `TWILIO_PHONE_NUMBER` = `<your Twilio phone number>`
   - `DEBUG` = `False`
7. Click `Create Web Service`.

Render will build and deploy your app, then provide a service URL.

### If Render fails to deploy
- Open the Render deploy log details.
- Copy the first error message or the failing step.
- Common issues:
  - missing packages in `requirements.txt`
  - invalid Python runtime
  - port or start command errors
- This repo now includes `runtime.txt` and `Procfile` to support Render.

## Step 3: Use the deployed backend URL in the frontend
After Render deploys, copy the service URL, for example:

```
https://buzzbee-backend.onrender.com
```

Then edit `order.html` and set:

```js
window.backendApiUrl = 'https://buzzbee-backend.onrender.com/api';
```

If you want me to update it automatically, provide the final Render service URL.

## Step 4: Test the live order flow
1. Open the frontend page in a browser.
2. Place an order.
3. Confirm the order reaches the Flask backend and returns success.
4. Confirm you receive a notification via Twilio or WhatsApp.

## Notes
- GitHub Pages can host only the static front-end. The backend must be on a separate server (Render, Railway, etc.).
- The current backend works locally and returns `201` for valid orders.
- You may want to add a real WhatsApp integration provider later if you want WhatsApp messages instead of SMS.
