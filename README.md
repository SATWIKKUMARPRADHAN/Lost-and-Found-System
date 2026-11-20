# Campus Lost and Found Management System

A production-ready web application built with **Python 3, Django 5, Bootstrap 5, and PostgreSQL/SQLite**, designed to reunite lost campus belongings securely through cryptographic verification.

---

## Key Features

- **Role-Based Access**:
  - **Student**: Register, login, report lost/found belongings, browse items with live multi-filter (category, location, report type), view details, submit cryptographic claims, track claim status.
  - **Administrator / Staff**: Dedicated custom dashboard (`/dashboard/`) with real-time statistics (Total Lost, Total Found, Pending Claims, Returned Items), claim review & approval/rejection actions, item return status marking, and inappropriate report moderation. Plus Django Admin (`/django-admin/`) as a secondary interface.
- **Cryptographic Verification Workflow**:
  - When reporting a **Found Item**, the student specifies a private verification question and expected answer.
  - The expected answer is stored as a **PBKDF2/Argon2 secure password hash** (via Django's `make_password`), never in plain text.
  - Claimants must solve the secret challenge (e.g., "What decal is on the back?"). Django evaluates the candidate answer with `check_password`.
  - Only claimants who pass the cryptographic check are queued for administrator handover approval.
  - Users are strictly prevented from claiming their own reports or filing duplicate claims.
- **Dual Database Architecture**:
  - **Local Development**: Automatic zero-config **SQLite** database (`db.sqlite3`).
  - **Production on Render**: Automatic **PostgreSQL** database via `DATABASE_URL`.
- **Zero-Pill Minimalist UI**:
  - Clean typography and layout inspired by Apple and Google design systems.
  - Responsive layouts across mobile, tablet, and desktop.

---

## Project Structure

```
campus_lostfound_project/
├── manage.py
├── requirements.txt         # Production & development dependencies
├── Procfile                 # Gunicorn worker for Render
├── build.sh                 # Render build script (pip, collectstatic, migrate)
├── render.yaml              # Render Infrastructure-as-Code Blueprint
├── .env.example             # Template for local & production environment variables
├── .gitignore
├── README.md
├── campus_lostfound/        # Django Project Configuration
│   ├── __init__.py
│   ├── settings.py          # Dual SQLite/Postgres + WhiteNoise + Cloudinary
│   ├── urls.py              # Root URL routing
│   ├── wsgi.py              # WSGI entrypoint for Gunicorn
│   └── asgi.py
├── core/                    # Main Application
│   ├── __init__.py
│   ├── admin.py             # Django Admin registration
│   ├── apps.py
│   ├── forms.py             # User registration, report item, claim verification
│   ├── models.py            # Item and Claim models with hash verification
│   ├── urls.py              # App URLs
│   ├── views.py             # Student views, claim workflow, admin dashboard
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py  # Ready-to-run database migrations
├── templates/               # Clean Bootstrap 5 Templates
│   ├── base.html            # Shared layout, navbar, messages, footer
│   ├── home.html            # Search, category & location filters, items grid
│   ├── item_detail.html     # Detailed item view and claim action
│   ├── report_item.html     # Report form with dynamic verification fields
│   ├── claim_item.html      # Secret question verification challenge
│   ├── my_items.html        # Student portal for tracking reports and claims
│   ├── admin_dashboard.html # Custom Administrator Dashboard
│   ├── login.html           # Authentication login
│   └── register.html        # Student registration
└── static/
    └── css/
        └── custom.css       # Apple/Google minimalist styles
```

---

## Local Development Quickstart

### 1. Prerequisites
- Python 3.10+ installed on your computer.
- Git.

### 2. Set Up Virtual Environment & Dependencies

```bash
# Clone or extract project
cd campus_lostfound_project

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS / Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(When `DATABASE_URL` is empty, Django automatically uses local SQLite `db.sqlite3`).*

### 4. Run Migrations & Create Administrator

```bash
# Apply database migrations
python manage.py migrate

# Create a staff superuser for accessing the Admin Dashboard
python manage.py createsuperuser
# Enter username (e.g. admin), email, and password
```

### 5. Start Local Development Server

```bash
python manage.py runserver
```
Open **http://127.0.0.1:8000** in your browser.

- Browse items & report lost/found items as a student.
- Log in with your superuser account and navigate to **http://127.0.0.1:8000/dashboard/** to access the Custom Administrator Dashboard.
- Secondary admin is at **http://127.0.0.1:8000/django-admin/**.

---

## Production Deployment on Render

### Step 1: Push Code to GitHub
1. Create a new repository on GitHub (e.g., `campus-lost-and-found`).
2. Push your `campus_lostfound_project` folder to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Campus Lost and Found system"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/campus-lost-and-found.git
   git push -u origin main
   ```

### Step 2: Create a PostgreSQL Database on Render
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** > **PostgreSQL**.
3. Name: `campus-lostfound-db`.
4. Database: `campus_lostfound`.
5. User: `campus_user`.
6. Region: Select the region nearest to you.
7. Plan: **Free**.
8. Click **Create Database**.
9. Once created, copy the **Internal Database URL** (or External Database URL).

### Step 3: Create Web Service on Render
1. In Render, click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Configure the service:
   - **Name**: `campus-lostfound`
   - **Region**: Same region as your database.
   - **Branch**: `main`
   - **Root Directory**: Leave blank (or specify if inside a subfolder).
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn campus_lostfound.wsgi:application`
   - **Instance Type**: **Free**

### Step 4: Configure Environment Variables in Render
In your Web Service settings, go to the **Environment** tab and add:

| Key | Value | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | *(Click Generate or enter a random 50+ character string)* | Essential for cryptographic tokens and session cookies. |
| `DEBUG` | `False` | Disables debug mode in production for security. |
| `ALLOWED_HOSTS` | `.onrender.com,localhost` | Allows Render subdomains. |
| `DATABASE_URL` | *(Paste Internal Database URL from Step 2)* | Automatically connects Django ORM to Postgres. |
| `PYTHON_VERSION` | `3.10.12` | Ensures consistent Python runtime. |

*(Optional Cloudinary Storage for persistent item photographs)*:
Sign up for a free account at [Cloudinary.com](https://cloudinary.com) and add:
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### Step 5: Deploy & Create Administrator
1. Click **Deploy Latest Commit**.
2. Render will execute `./build.sh` (installs packages, gathers static files via WhiteNoise, and applies all database migrations automatically).
3. Once the build completes and service is Live, click the **Shell** tab in Render Web Service and run:
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to set your admin username and password.
4. Your application is now live at `https://campus-lostfound.onrender.com`!

---

## How to Inspect Your Production PostgreSQL Database

### Option A: Using Render's Built-In Web Dashboard (Simplest)
1. In the Render Dashboard, open your PostgreSQL database (`campus-lostfound-db`).
2. Go to the **Metrics** & **Info** tab to view live connection counts, storage used, and server health.
3. You can click the **Connect** button at the top right to copy connection strings or launch a psql terminal directly.

### Option B: Using pgAdmin 4
1. Open pgAdmin 4 on your local computer.
2. Right-click **Servers** > **Register** > **Server...**
3. In the **General** tab:
   - Name: `Render Campus DB`
4. In the **Connection** tab:
   - Copy the **External Connection String** from your Render Database info page. It looks like:
     `postgres://user:password@dpg-xxxx.oregon-postgres.render.com/campus_lostfound`
   - **Host name/address**: `dpg-xxxx.oregon-postgres.render.com`
   - **Port**: `5432`
   - **Maintenance database**: `campus_lostfound`
   - **Username**: `campus_user`
   - **Password**: *(The password shown in Render)*
5. In the **Parameters** tab:
   - Set **SSL mode** to `Require`.
6. Click **Save**.
7. Navigate to **Databases > campus_lostfound > Schemas > public > Tables**. You will see `core_item`, `core_claim`, and `auth_user` tables and can run SQL queries directly!

---

## Free-Tier Hosting Limitations & Considerations

- **Render Web Service Inactivity Sleep**: Free-tier web services automatically spin down into a sleep state after 15 minutes of inactivity. The first request after sleep takes 30-50 seconds to wake up.
- **Render Free PostgreSQL Retention**: Render's free PostgreSQL instances provide 1 GB of storage and expire 30 days after creation. For a permanent production deployment, upgrade to Render's Hobby tier ($7/mo) or use a permanent free-tier provider like Supabase or Neon by simply updating the `DATABASE_URL` environment variable!
- **Ephemeral Filesystem**: Render instances do not preserve local uploaded files across restarts or redeployments. For persistent image uploads, the project has built-in support for Cloudinary (free tier includes 25GB storage and 25k monthly transformations).
