# Gemini AI Setup Guide

## Problem Identified

The frontend is receiving `"gemini_enabled": false` and `"gemini_success": false` because the `GEMINI_API_KEY` environment variable is not set in the production (Vercel) environment.

## Current Status

✅ **Code is correct**: The application properly checks for `GEMINI_API_KEY`
❌ **Environment variable missing**: `GEMINI_API_KEY` is not configured in Vercel

## How to Fix

### 1. Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key (starts with `AIza...`)

### 2. Set Environment Variable in Vercel

#### Option A: Via Vercel Dashboard
1. Go to your [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project (`ai-health-screening`)
3. Go to **Settings** > **Environment Variables**
4. Add a new environment variable:
   - **Name**: `GEMINI_API_KEY`
   - **Value**: Your API key from step 1
   - **Environments**: Check "Production", "Preview", and "Development"
5. Click **Save**
6. **Redeploy** your application

#### Option B: Via Vercel CLI
```bash
# Install Vercel CLI if not already installed
npm i -g vercel

# Add environment variable
vercel env add GEMINI_API_KEY

# When prompted, enter your API key
# Select: Production, Preview, Development (all environments)

# Redeploy
vercel --prod
```

### 3. Verify the Fix

After setting the environment variable and redeploying:

1. Go to your deployed application
2. Fill out the health assessment form
3. Submit the form
4. Check the response in browser developer tools
5. You should now see:
   ```json
   {
     "gemini_enabled": true,
     "gemini_success": true,
     "ai_analysis": {
       "model_used": "Google gemini-2.0-flash-lite"
     }
   }
   ```

### 4. Test API Endpoint Directly

You can test the API endpoint directly to verify Gemini is working:

```bash
curl -X POST https://your-vercel-app.vercel.app/api/assess-health \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "age": 30,
    "gender": "female",
    "symptoms": "mild headache and fatigue for 2 days",
    "medical_history": "none",
    "current_medications": "none"
  }'
```

## Environment Variable Names

⚠️ **Important**: There's an inconsistency in documentation:
- **Code uses**: `GEMINI_API_KEY` ✅ (correct)
- **README mentions**: `GOOGLE_API_KEY` ❌ (incorrect)

Always use `GEMINI_API_KEY` as that's what the code expects.

## Troubleshooting

### Still seeing `gemini_enabled: false`?

1. **Double-check the environment variable name**: Must be exactly `GEMINI_API_KEY`
2. **Verify the API key is valid**: Test it with Google AI Studio
3. **Redeploy after setting**: Environment variables require a redeploy
4. **Check all environments**: Set for Production, Preview, and Development

### API Key Invalid?

- Make sure you copied the full key (usually starts with `AIza`)
- Verify the key works in Google AI Studio
- Check if there are any usage restrictions on your Google account

### Local Development

For local development, create a `.env` file:

```bash
# .env (do not commit to git)
GEMINI_API_KEY=your_actual_api_key_here
```

## Next Steps

1. Set `GEMINI_API_KEY` in Vercel environment variables
2. Redeploy the application
3. Test the health assessment form
4. Verify `gemini_enabled: true` and `gemini_success: true` in responses
5. Update README.md to use correct `GEMINI_API_KEY` variable name

Once this is done, the AI Health Assessment System will be fully functional with Gemini AI integration!
