# Vercel Deployment Guide

## Summary of Changes

Fixed the read-only file system error (`/var/task/static`) for Vercel deployment:

1. **Disabled static folder on Vercel** - Flask no longer tries to access the read-only `/var/task/static`
2. **QR codes are generated on-the-fly** - No files written during upload
3. **Proper Vercel structure** - Added `api/index.py` entry point for serverless functions
4. **Environment variables** - Credentials loaded from environment on Vercel, local file otherwise

## Deployment Steps

### 1. Set Environment Variables on Vercel

In your Vercel project dashboard:
- Go to **Settings** → **Environment Variables**
- Add these variables:

| Variable | Value |
|----------|-------|
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Paste entire contents of `credentials.json` as raw JSON |
| `SHEET_ID` | `1bIH-SmBWm6nyxpvJ4fAWZIZ-99eu_m9qS-N_34VW9oE` |
| `ADMIN_USERNAME` | `admin` (or your username) |
| `ADMIN_PASSWORD` | Your secure password |

**Important**: For `GOOGLE_SHEETS_CREDENTIALS_JSON`, copy the raw JSON from your credentials.json file:
```json
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  ...
}
```

### 2. Push Code to GitHub

```bash
git add .
git commit -m "Fix Vercel read-only filesystem error"
git push
```

### 3. Redeploy on Vercel

Vercel will automatically redeploy when you push. If not, manually trigger a redeploy from the Vercel dashboard.

## How It Works

### Local Development
- Uses `credentials.json` file locally
- Uses default Flask `static/` folder
- Works as before - no changes needed

### Vercel Deployment
- Reads credentials from `GOOGLE_SHEETS_CREDENTIALS_JSON` environment variable
- Creates temporary credentials file in `/tmp` (writable)
- Disables Flask static folder (not needed, all QR codes generated on-the-fly)
- Entry point: `api/index.py` → `app.py`

## Files Modified

- `app.py` - Flask configuration for Vercel
- `sheets_handler.py` - Support for environment variable credentials
- `vercel.json` - Vercel deployment configuration
- `api/index.py` - Serverless function entry point
- `wsgi.py` - WSGI wrapper (optional)

## Testing Upload

1. Login with your admin credentials
2. Upload a CSV with columns: `Student_ID`, `Name`, `Section`
3. Should see "Students uploaded successfully!" message
4. No more read-only file system errors!

## Troubleshooting

If you still see the `/var/task/static` error:
1. Check environment variables are set correctly
2. Verify `GOOGLE_SHEETS_CREDENTIALS_JSON` is valid JSON
3. Check Vercel build logs for errors
4. Ensure `SHEET_ID` is correct

For more help, check Vercel logs: `vercel logs --project annual-dinner`
