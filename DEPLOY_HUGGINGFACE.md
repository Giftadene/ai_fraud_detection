# Deploying FraudGuard AI to Hugging Face Spaces

A comprehensive step-by-step guide to host the **Deborah Patrick N. Machine Learning-Based Fraud Detection System** on Hugging Face Spaces using Docker.

---

## Prerequisites

Before you begin, ensure you have:

- A [Hugging Face account](https://huggingface.co/join) (free tier works)
- Git installed on your local machine ([download](https://git-scm.com/downloads))
- The FraudGuard AI project files on your local machine
- Basic familiarity with the command line

---

## Step 1: Prepare the Project for Deployment

The project already includes all necessary files for Hugging Face Spaces:

| File | Purpose |
|---|---|
| `Dockerfile` | Defines the container environment |
| `requirements.txt` | Python dependencies (including gunicorn) |
| `.dockerignore` | Excludes unnecessary files from the build |
| `packages.txt` | System-level dependencies |
| `app.py` | Flask application entry point |

### Verify the Files

Open a terminal in the project root directory and confirm these files exist:

```bash
dir Dockerfile requirements.txt .dockerignore packages.txt app.py
```

All files should be present.

---

## Step 2: Create a Hugging Face Space

1. **Log in** to your Hugging Face account at [huggingface.co](https://huggingface.co)

2. **Click your profile picture** (top-right corner) → **"New Space"**

3. **Configure the Space:**
   - **Space Name:** `fraudguard-ai` (or any name you prefer)
   - **License:** `MIT` (recommended)
   - **Space SDK:** Select **`Docker`**
   - **Hardware:** `CPU basic` (free tier is sufficient)
   - **Make Public:** Toggle ON if you want public access (recommended for portfolio/demo)

4. Click **"Create Space"**

---

## Step 3: Connect Your Local Project to the Space

You have two options:

### Option A: Push via Git (Recommended)

```bash
# Clone your Hugging Face Space repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/fraudguard-ai
cd fraudguard-ai

# Copy all project files into this directory
# (copy from your FraudGuard project folder into the cloned space folder)
xcopy /E /I /Y "C:\path\to\ai_fraud_detection\*" "."

# Add, commit, and push
git add .
git commit -m "Initial deployment of FraudGuard AI"
git push
```

### Option B: Upload via Hugging Face Web Interface

1. Open your Space page on huggingface.co
2. Click the **"Files"** tab
3. Click **"Add file"** → **"Upload files"**
4. Drag and drop all project files (or select them manually)
5. Scroll down and click **"Commit changes"**

> **Note:** If uploading via web, make sure to include ALL files: `app.py`, `database.py`, `ml_engine.py`, `Dockerfile`, `requirements.txt`, `.dockerignore`, `packages.txt`, the entire `templates/` folder, and the entire `static/` folder.

---

## Step 4: Configure Environment Variables (Secrets)

Hugging Face Spaces allows you to set **Secrets** — environment variables that are encrypted and not visible in the source code.

1. Go to your Space page
2. Click the **"Settings"** tab
3. Scroll down to **"Repository Secrets"**
4. Click **"New secret"** and add these:

| Name | Value | Description |
|---|---|---|
| `FRAUDGUARD_ADMIN_PW` | `your_secure_admin_password` | Admin login password |
| `FRAUDGUARD_ANALYST_PW` | `your_secure_analyst_password` | Analyst login password |

> **Important:** If you do NOT set these secrets, the system will use the default values (`admin123` / `analyst123`) as defined in the `Dockerfile`. For production, always set strong custom passwords via Secrets.

---

## Step 5: Build and Deploy

Once you push the code or upload the files, Hugging Face Spaces automatically:

1. **Detects the `Dockerfile`** and starts building the Docker image
2. **Installs dependencies** (this takes 5-10 minutes on first build)
3. **Trains the ML model** automatically on startup
4. **Starts the server** on port 7860

### Monitor the Build

1. Go to your Space page
2. Click the **"Builder"** tab (or "Factory" tab in some views)
3. You will see the build log in real-time
4. Wait for the build to complete (look for: `"App is running"` or a green status indicator)

---

## Step 6: Access Your Deployed Application

Once the build succeeds:

1. Your Space will display a **direct URL** like:
   ```
   https://YOUR_USERNAME-fraudguard-ai.hf.space
   ```
2. Click the URL to open the **Landing Page** (served at the root `/`)
3. Click **"Sign In"** in the top navigation to go to the login page
4. Log in with the credentials you configured:
   - **Admin:** `admin` / `your_secure_admin_password`
   - **Analyst:** `analyst` / `your_secure_analyst_password`
5. You will be redirected to the **Dashboard** at `/app`

---

## Post-Deployment Checklist

Verify that everything works correctly after deployment:

- [ ] Landing page loads with the hero section and navigation
- [ ] "Deborah Patrick N." title displays correctly
- [ ] Sign In button leads to the login page
- [ ] Login works with admin credentials
- [ ] Dashboard loads with KPIs and charts
- [ ] Monitoring tab shows transaction data
- [ ] Alerts desk loads with pending alerts
- [ ] Model Lab shows XGBoost metrics
- [ ] Sandbox simulation works without errors
- [ ] User Management (admin only) allows creating users
- [ ] Profile page loads and allows bio/avatar editing
- [ ] FAQ and Contact sections render on the landing page

---

## Troubleshooting

### Build Fails

**Issue:** Docker build fails with a timeout or dependency error.

**Solutions:**
- Check the build logs in the **"Builder"** tab for specific error messages
- Ensure `requirements.txt` contains all dependencies (including `gunicorn`)
- Ensure `packages.txt` contains `build-essential` and `gcc` for compiling native extensions
- Restart the build by going to **Settings** → **"Factory rebuild"**

### App Crashes on Start

**Issue:** The app starts but immediately crashes.

**Solutions:**
- Check the runtime logs in the **"Factory"** tab
- The model training on first start requires about 30 seconds — wait for it
- Ensure the database and pickle files (`.db`, `.pkl`) are NOT in the `.dockerignore` — they should be generated fresh on each start
- If using a persistent volume, delete old database files via the Hugging Face file browser

### "Not Authenticated" Errors

**Issue:** API calls return 401 or redirect to the login page in a loop.

**Solutions:**
- Clear your browser cookies and cache for the Space domain
- Ensure you are logging in from the `/login` page (not directly accessing `/app`)
- Check that the session cookie is being set (browser developer tools → Application → Cookies)

### Port Binding Issues

**Issue:** The app fails to bind to the port.

**Solution:**
- The `Dockerfile` uses `$PORT` environment variable which Hugging Face automatically sets to `7860`
- Ensure the `CMD` in the `Dockerfile` uses `0.0.0.0:$PORT` (not `127.0.0.1` or a hardcoded port)

### XGBoost Build Errors

**Issue:** XGBoost fails to compile during pip install.

**Solution:**
- Ensure `packages.txt` includes `build-essential` and `gcc` (needed for compiling XGBoost)
- The `python:3.11-slim` base image in the `Dockerfile` is minimal — these packages add the C++ compiler that XGBoost requires

---

## Updating the Deployment

To update your deployed application after making changes:

```bash
# Navigate to your local space clone
cd fraudguard-ai

# Pull the latest (if others have made changes)
git pull

# Copy updated files
xcopy /E /I /Y "C:\path\to\ai_fraud_detection\*" "."

# Commit and push
git add .
git commit -m "Update: description of changes"
git push
```

Hugging Face Spaces will automatically rebuild and redeploy.

---

## Cost & Limitations

### Free Tier
- **CPU:** 2 vCPUs (shared)
- **RAM:** 16 GB
- **Storage:** 50 GB
- **Build time:** Limited (may timeout on large dependencies)
- **Sleeps after:** 48 hours of inactivity (wakes on next request, takes ~30s)

### Paid Tier (Pro)
- **CPU:** Dedicated
- **RAM:** Up to 64 GB
- **No sleep** — always on
- **Priority builds** — faster deployment

The FraudGuard AI system runs comfortably on the free tier for demonstration and testing purposes.

---

## Architecture Overview (Hugging Face Deployment)

```
User Browser
     │
     ▼
https://fraudguard-ai.hf.space
     │
     ▼
Hugging Face Spaces (Docker Container)
     │
     ├── /          → Landing page (landing.html)
     ├── /login     → Login page (login.html)
     ├── /app       → Dashboard (index.html) [requires auth]
     ├── /api/*     → REST API endpoints [most require auth]
     ├── /static/*  → Static files (images, etc.)
     │
     ├── app.py          (Flask entry point)
     ├── database.py     (SQLite + SQLAlchemy)
     ├── ml_engine.py    (XGBoost model)
     ├── templates/      (HTML templates)
     └── static/         (Static assets)
```

---

## Summary

| Step | Action | Time |
|---|---|---|
| 1 | Create Hugging Face account | 5 min |
| 2 | Create a new Space (Docker SDK) | 2 min |
| 3 | Push project files via Git or upload | 5 min |
| 4 | Configure Secrets (passwords) | 2 min |
| 5 | Wait for build to complete | 10-15 min |
| 6 | Access and verify the deployment | 5 min |
| **Total** | | **~30 minutes** |

---

*FraudGuard AI — Deborah Patrick N. Machine Learning-Based Fraud Detection System*
*Capstone Project &bull; FinTech Domain &bull; XGBoost Classifier*
