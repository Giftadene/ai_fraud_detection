# Hosting FraudGuard AI Locally Using XAMPP

A step-by-step guide to deploy **Deborah Patrick N. Machine Learning-Based Fraud Detection System** using XAMPP's Apache server as a reverse proxy for the Python Flask application.

---

## Overview

This guide uses XAMPP's **Apache** web server to serve the FraudGuard AI Flask application on your local network. Apache acts as a **reverse proxy** — it receives all HTTP requests on port 80 and forwards them to the Flask application running on port 5000.

```
User Browser
     │
     ▼
http://localhost                  ← Apache (port 80, XAMPP)
     │
     ▼  (reverse proxy)
http://127.0.0.1:5000             ← Flask (port 5000)
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Windows 10/11 | — | Tested on Windows |
| XAMPP | 8.x or later | Download from [apachefriends.org](https://www.apachefriends.org/download.html) |
| Python | 3.10 – 3.12 | Download from [python.org](https://www.python.org/downloads/) |
| Git (optional) | — | For cloning the project |

> ⚠️ **Important:** Do NOT use Python 3.13+ — some dependencies may not be compatible.

---

## Step 1: Install XAMPP

1. Download XAMPP from [https://www.apachefriends.org/download.html](https://www.apachefriends.org/download.html)
2. Run the installer
3. Accept the default components (**Apache** is the only required component)
4. Choose installation directory (default: `C:\xampp`)
5. Complete the installation
6. Launch **XAMPP Control Panel** (as Administrator)

---

## Step 2: Install Python

1. Download Python 3.11 from [https://www.python.org/downloads/release/python-3119/](https://www.python.org/downloads/release/python-3119/)
   - Scroll down and select **"Windows installer (64-bit)"**
2. Run the installer
3. **IMPORTANT:** Check **"Add Python to PATH"** at the bottom of the installer
4. Click **"Install Now"**
5. Wait for installation to complete
6. Verify by opening **Command Prompt** and running:
   ```
   python --version
   ```
   You should see: `Python 3.11.x`

---

## Step 3: Set Up the Project Folder

1. Create a folder for the project:
   ```
   C:\xampp\htdocs\fraudguard
   ```

2. Copy all FraudGuard AI project files into this folder. Your folder should contain:
   ```
   C:\xampp\htdocs\fraudguard\
   ├── app.py
   ├── database.py
   ├── ml_engine.py
   ├── Dockerfile
   ├── requirements.txt
   ├── templates/
   │   ├── landing.html
   │   ├── login.html
   │   └── index.html
   ├── static/
   │   ├── logo.png
   │   └── favicon.png
   └── XAMPP_DEPLOYMENT.md
   ```

---

## Step 4: Install Python Dependencies

1. Open **Command Prompt** as Administrator
2. Navigate to the project folder:
   ```
   cd C:\xampp\htdocs\fraudguard
   ```

3. Create a virtual environment (recommended):
   ```
   python -m venv venv
   ```

4. Activate the virtual environment:
   ```
   venv\Scripts\activate
   ```
   You should see `(venv)` appear at the beginning of the command prompt line.

5. Install all dependencies:
   ```
   pip install -r requirements.txt
   ```
   This will install Flask, Pandas, NumPy, Scikit-learn, XGBoost, and Gunicorn.

   > ⏱ **First run:** This may take 5–10 minutes as it compiles XGBoost.

---

## Step 5: Test Flask Standalone

Before integrating with XAMPP, verify the Flask app runs correctly on its own:

1. With the virtual environment still activated, run:
   ```
   set FRAUDGUARD_ADMIN_PW=admin123
   set FRAUDGUARD_ANALYST_PW=analyst123
   python app.py
   ```

2. Open your browser and visit:
   ```
   http://127.0.0.1:5000
   ```
   You should see the FraudGuard AI landing page with the title **"Deborah Patrick N. Machine Learning-Based Fraud Detection System"**.

3. Click **"Sign In"** → log in with:
   - **Username:** `admin`
   - **Password:** `admin123`

4. Verify the dashboard loads with KPIs, charts, and navigation tabs.

5. Press **Ctrl+C** in the terminal to stop Flask when done.

---

## Step 6: Create a Startup Script for Flask

Create a file called `start_flask.bat` in the project folder (`C:\xampp\htdocs\fraudguard\start_flask.bat`) with this content:

```batch
@echo off
cd /d "C:\xampp\htdocs\fraudguard"
call venv\Scripts\activate.bat
set FRAUDGUARD_ADMIN_PW=admin123
set FRAUDGUARD_ANALYST_PW=analyst123
python app.py
```

To test: Double-click `start_flask.bat` — a terminal window opens showing Flask starting. Access `http://127.0.0.1:5000` to confirm. Close the terminal to stop Flask.

> **Note:** Flask must be running BEFORE you start Apache. Keep this terminal window open while using the system.

---

## Step 7: Configure Apache as a Reverse Proxy

Now we configure Apache (in XAMPP) to forward all requests from port 80 to the Flask application on port 5000.

### 7.1 Enable Required Apache Modules

1. Open **XAMPP Control Panel**
2. Click **"Config"** next to Apache → **"Apache (httpd.conf)"**
3. Find these lines and **uncomment them** (remove the `#` at the start):

   ```apache
   LoadModule proxy_module modules/mod_proxy.so
   LoadModule proxy_http_module modules/mod_proxy_http.so
   LoadModule rewrite_module modules/mod_rewrite.so
   LoadModule proxy_wstunnel_module modules/mod_proxy_wstunnel.so
   ```

   If any of the above lines do NOT exist in the file, add them at the end of the `LoadModule` section near the top of the file.

4. **Save the file**

### 7.2 Enable Virtual Hosts

1. In the same `httpd.conf` file, find this line:
   ```apache
   #Include conf/extra/httpd-vhosts.conf
   ```
2. **Remove the `#`** at the beginning so it becomes:
   ```apache
   Include conf/extra/httpd-vhosts.conf
   ```
3. **Save the file**

### 7.3 Configure the Virtual Host

1. Open **XAMPP Control Panel**
2. Click **"Config"** next to Apache → **"Apache (httpd-vhosts.conf)"**
   (File location: `C:\xampp\apache\conf\extra\httpd-vhosts.conf`)

3. **Replace the entire content** of the file with this:

   ```apache
   # FraudGuard AI - Reverse Proxy Configuration
   
   <VirtualHost *:80>
       ServerName localhost
       DocumentRoot "C:/xampp/htdocs"
       
       ProxyRequests Off
       ProxyPreserveHost On
       
       # Exclude XAMPP's own paths from proxying
       ProxyPass /phpmyadmin !
       ProxyPass /dashboard !
       ProxyPass /img !
       ProxyPass /webalizer !
       
       # Proxy everything else to Flask
       ProxyPass / http://127.0.0.1:5000/
       ProxyPassReverse / http://127.0.0.1:5000/
   </VirtualHost>
   ```

4. **Save the file**

---

## Step 8: Start Everything

### 8.1 Start Flask

1. Navigate to `C:\xampp\htdocs\fraudguard`
2. **Double-click** `start_flask.bat`
3. A terminal window opens. Wait until you see:
   ```
   * Running on http://127.0.0.1:5000
   ```

### 8.2 Start Apache

1. Open **XAMPP Control Panel**
2. Click **"Start"** next to **Apache**
3. The status should turn **green** and show port **80**

### 8.3 Access the Application

1. Open your browser
2. Go to: **http://localhost**
3. You should see the **FraudGuard AI landing page**
4. Click **"Sign In"** in the top navigation bar
5. Log in with:
   - **Username:** `admin`
   - **Password:** `admin123`
6. You will be redirected to the **dashboard** at `http://localhost/app`

---

## Step 9: Make the System Accessible on Your Local Network

### 9.1 Find Your Computer's IP Address

1. Open **Command Prompt**
2. Run:
   ```
   ipconfig
   ```
3. Look for **"IPv4 Address"** under your active network adapter. Example: `192.168.1.100`

### 9.2 Configure Windows Firewall

1. Open **Windows Security** → **Firewall & network protection**
2. Click **"Allow an app through firewall"**
3. Click **"Change settings"** → **"Allow another app"**
4. Browse to `C:\xampp\apache\bin\httpd.exe` and add it
5. Make sure both **Private** and **Public** are checked

### 9.3 Access from Other Devices

Other devices on your local network can now access:
```
http://192.168.1.100
```
(Replace `192.168.1.100` with your actual IP address)

---

## Step 10: (Optional) Use a Custom Domain Name

To access the system using a friendly name like `http://fraudguard.local`:

### 10.1 Edit Windows Hosts File

1. Open **Notepad as Administrator**
2. Open file: `C:\Windows\System32\drivers\etc\hosts`
3. Add this line at the bottom:
   ```
   127.0.0.1  fraudguard.local
   ```
4. Save and close

### 10.2 Update Apache Virtual Host

Edit `C:\xampp\apache\conf\extra\httpd-vhosts.conf` and add:

```apache
<VirtualHost *:80>
    ServerName fraudguard.local
    
    ProxyRequests Off
    ProxyPreserveHost On
    
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
</VirtualHost>
```

### 10.3 Restart Apache

In XAMPP Control Panel, click **"Stop"** then **"Start"** next to Apache.

### 10.4 Access via Custom Domain

```
http://fraudguard.local
```

---

## Troubleshooting

### Apache fails to start ("Apache shutdown unexpectedly")

This is the most common XAMPP error. Follow these checks in order:

**1. Port 80 is already in use**

Something else is using port 80. To check:

```
netstat -ano | findstr :80
```

Look for `LISTENING` on `0.0.0.0:80` or `[::]:80`. Note the PID (last column), then run:

```
tasklist /fi "PID YOUR_PID"
```

| If it's... | Fix it by... |
|---|---|
| **IIS** | Open "Turn Windows features on/off" → uncheck "Internet Information Services" |
| **Skype** | Settings → Advanced → Connection → uncheck "Use port 80 and 443" |
| **Docker Desktop** | Stop Docker or change its port settings |
| **WSL** | `net stop wslservice` in Command Prompt (Admin) |

**Quick workaround:** Change Apache to port 8080 instead:
- Open `C:\xampp\apache\conf\httpd.conf`
- Change `Listen 80` to `Listen 8080`
- Change `ServerName localhost:80` to `ServerName localhost:8080`
- Access at `http://localhost:8080`

**2. Check Apache configuration for errors**

Open Command Prompt and run:
```
C:\xampp\apache\bin\httpd.exe -t
```
This will show the exact error message if any config file has a syntax error.

**3. Missing Visual C++ Redistributable**

Download and install from:
https://aka.ms/vs/17/release/vc_redist.x64.exe

Then restart your computer.

---

### Landing page loads but "Sign In" shows "Not Found"

**Cause:** Apache is trying to serve `/login` from its own file system instead of forwarding it to Flask.

**Fix:** Make sure your `httpd-vhosts.conf` proxies the **entire root** `/` to Flask, not just a sub-path like `/fraudguard`. Use the configuration from **Step 7.3** above.

---

### "Service Unavailable" or 503 error

**Cause:** Flask is not running. Apache is trying to proxy requests to `127.0.0.1:5000` but nothing is listening there.

**Fix:** Double-click `start_flask.bat` and wait for Flask to start.

---

### Pages load but no data (blank tables/charts)

**Cause:** Flask started but the database initialization or model training failed.

**Fix:** Check the Flask terminal window for error messages. Then:
1. Stop Flask (Ctrl+C)
2. Delete old database and model files:
   ```
   del database.db
   del fraud_model.pkl
   del scaler.pkl
   del metrics.pkl
   ```
3. Restart `start_flask.bat`
4. The first run will recreate the database and train the model

---

### Login fails — "Invalid username or password"

**Cause:** The database was recreated but without default users, or credentials don't match.

**Fix:**
1. Make sure the terminal running Flask shows:
   ```
   [INFO] Using default admin password.
   ```
2. Check that `start_flask.bat` sets the environment variables:
   ```
   set FRAUDGUARD_ADMIN_PW=admin123
   set FRAUDGUARD_ANALYST_PW=analyst123
   ```
3. If still failing, delete `database.db` and restart Flask to trigger a fresh seed.

---

### Apache starts but browser shows XAMPP dashboard instead of FraudGuard

**Cause:** The `httpd-vhosts.conf` file is not being loaded (the `Include` line is still commented out).

**Fix:** Verify that `C:\xampp\apache\conf\httpd.conf` has this line UNCOMMENTED:
```apache
Include conf/extra/httpd-vhosts.conf
```
(Remove the `#` at the beginning.)

---

### Can't access from other devices on the network

**Fix:**
1. Ensure both devices are on the **same Wi-Fi / network**
2. Ensure **Windows Firewall** allows Apache (`httpd.exe`)
3. Use the correct IP address (`ipconfig` to check)
4. Temporarily disable Windows Firewall to test (re-enable afterward)

---

## Quick Command Reference

| Action | Command / Steps |
|---|---|
| **Start Flask** | Double-click `start_flask.bat` |
| **Start Apache** | XAMPP Control Panel → "Start" on Apache |
| **Stop Flask** | Close the terminal window, or press Ctrl+C |
| **Stop Apache** | XAMPP Control Panel → "Stop" on Apache |
| **Test Apache config** | `C:\xampp\apache\bin\httpd.exe -t` |
| **Check port 80** | `netstat -ano \| findstr :80` |
| **Delete old database** | `del C:\xampp\htdocs\fraudguard\database.db` |
| **Check Python version** | `python --version` |

---

## Startup Order

Always start services in this order:

```
1. Start Flask (start_flask.bat)
           ↓
2. Start Apache (XAMPP Control Panel)
           ↓
3. Open browser → http://localhost
```

---

## System Architecture

```
                         Local Network / Browser
                                │
                                ▼
                    ┌─────────────────────────┐
                    │   Apache (XAMPP)         │
                    │   Port 80 (or 8080)      │
                    │   Reverse Proxy          │
                    │   httpd-vhosts.conf      │
                    └──────────┬──────────────┘
                               │
                     ProxyPass / → http://127.0.0.1:5000/
                               │
                    ┌──────────▼──────────────┐
                    │   Flask (Python)         │
                    │   Port 5000              │
                    │   FraudGuard AI App      │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │   SQLite Database        │
                    │   database.db            │
                    └─────────────────────────┘
```

---

*FraudGuard AI — Deborah Patrick N. Machine Learning-Based Fraud Detection System*
*Capstone Project &bull; FinTech Domain &bull; XGBoost Classifier*
