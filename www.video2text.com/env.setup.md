# Environment Setup Instructions

## Step 1: Create .env.local file

Create a file named `.env.local` in the Frontend directory with the following content:

```bash
# For local development (using local backend)
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000

# For production (using external backend)
# NEXT_PUBLIC_API_BASE_URL=https://model-evaluation.onrender.com

# Environment
NODE_ENV=development
```

## Step 2: Restart the frontend

After creating the `.env.local` file, restart your frontend development server:

```bash
# Stop the current frontend (Ctrl+C)
# Then restart it
cd Frontend
npm run dev
# or
pnpm dev
```

## Step 3: Verify configuration

The frontend should now:
- Use `http://localhost:5000` for API calls when in development
- Automatically fall back to the external backend if local is not available
- Load environment variables properly

## Troubleshooting

If you still get "Failed to fetch" errors:

1. **Check if local backend is running:**
   ```bash
   lsof -ti:5000
   ```

2. **Check if frontend is running:**
   ```bash
   lsof -ti:3000
   ```

3. **Verify environment variables are loaded:**
   - Check browser console for any environment-related logs
   - Ensure `.env.local` file is in the correct location

4. **Test local backend directly:**
   ```bash
   curl http://localhost:5000/api/indexes
   ``` 