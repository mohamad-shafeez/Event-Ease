# EventEase 🌐✨

EventEase is a robust, production-ready event management platform built with Python (Flask), MySQL, and modern Vanilla CSS. It facilitates seamless collaboration between event creators, attendees, and platform administrators, supercharged with Gemini AI for automated copy generation, pricing recommendations, and content moderation.

---

## 🛠️ Tech Stack & Dependencies

*   **Backend Framework:** Flask (3.1.0)
*   **Database:** MySQL (using `mysql-connector-python` with connection pooling)
*   **Session Management:** Flask-Session (filesystem-based session persistence)
*   **Security:** Flask-Bcrypt (password hashing)
*   **AI Integration:** Google Generative AI (Gemini API SDK)
*   **Asset Generation:** qrcode & Pillow (dynamic QR code generation for tickets)
*   **Background Tasks:** APScheduler (automated waitlist and status updates)
*   **Styling:** Vanilla CSS (Tailored HSL theme, custom UI components, responsive layout)

---

## 🚀 Key Features (Fully Working)

### 👥 Multi-Role Workspace
*   **Attendees (Users):**
    *   Browse events with advanced filters (category, city, dates, free/paid, search).
    *   Use **AI Smart Search** to find events using natural language.
    *   Book tickets, complete a simulated checkout, and receive a PDF/Image ticket containing a custom-generated **QR Code**.
    *   Participate in **Event Waitlists** for sold-out events.
    *   Leave star ratings and text reviews for past events.
    *   Bookmark/Save events to their profile.
    *   Follow creators to receive real-time dashboard notifications when they publish new events.
    *   Message creators directly regarding event logistics.
    *   Manage comprehensive profile settings and securely reset passwords via email token simulation.
*   **Creators:**
    *   Create, draft, edit, publish, or cancel events.
    *   Configure dynamic, type-specific registration questions.
    *   Leverage **Gemini AI Tools** within the creation wizard:
        *   *AI Description Generator:* Auto-writes 150-word descriptions.
        *   *AI Pricing Suggester:* Recommends fair ticket prices in INR with local market reasoning.
        *   *AI Social Media Promo Writer:* Auto-generates WhatsApp/social media copy with emojis.
    *   Access a dedicated **Creator Dashboard** with event stats (revenue, ticket sales, capacity fill rates).
    *   Manage event registrations, view attendee answers, and check-in attendees via ticket code scanning.
*   **Administrators (Admins):**
    *   Review platform-wide statistics (active users, creators, total revenue, event growth).
    *   Manage users (view profiles and instantly **ban/unban** accounts).
    *   Review and moderate events using **AI Content Moderation** (automatically flags policy violations).
    *   Manage global platform configurations (maintenance mode toggle, guest browsing permissions, ticket limits).

### 🤖 Gemini AI Assistant Integration
*   **Platform Chatbot:** Interactive AI assistant tailored to user role.
*   **Smart Search Parser:** Parses natural language phrases into structured database filters.
*   **Content Moderation:** Evaluates event metadata for safety classification (Safe, Warning, Flagged).

### ⏰ Background System Automation
*   **APScheduler Integration:** Automatically cancels expired draft events, updates event statuses, and manages waitlist promotion notifications.

---

## 📂 Project Structure

```
EventEase/
├── app.py                  # Application entry point & factory
├── config.py               # Flask configurations & environment variables
├── db.py                   # MySQL connection pooling & raw query helpers
├── extensions.py           # bcrypt & Session initializations
├── requirements.txt        # Application python dependencies
├── eventease.sql           # Complete unified SQL schema file
│
├── models/                 # Data Access Layer
│   ├── user_model.py
│   ├── event_model.py
│   ├── ticket_model.py
│   ├── message_model.py
│   └── analytics_model.py
│
├── routes/                 # Blueprints (Controllers)
│   ├── auth.py             # User Authentication
│   ├── profile.py          # Profiles, followers, saved events
│   ├── events.py           # Browse, Search, Creator CRUD, Reviews
│   ├── tickets.py          # Booking, Waitlist, QR Codes, Check-in
│   ├── ai.py               # Gemini AI helper endpoints
│   ├── messages.py         # Creator-User Messaging
│   ├── notifications.py    # Notification stream
│   ├── password_reset.py   # Secure Token Resets
│   └── admin.py            # Moderation & Platform Config
│
├── static/                 # Styles, Scripts, and Uploads
│   ├── css/                # Custom CSS Design System
│   ├── js/                 # Client logic and AI handlers
│   ├── uploads/            # Banners & Avatars
│   └── qr_tickets/         # Generated QR code files
│
├── templates/              # HTML Templates (Jinja2)
│   ├── admin/
│   ├── creator/
│   ├── events/
│   ├── tickets/
│   ├── user/
│   └── errors/
│
└── utils/                  # Background utility functions
    ├── ai_helper.py        # Gemini API connector
    ├── scheduler.py        # APScheduler task definitions
    ├── qr_generator.py     # qrcode helper
    └── email_sender.py     # SMTP Email Dispatch
```

---

## ⚙️ Installation & Setup

### 1. Database Setup
Ensure you have a running MySQL instance (local or XAMPP). Import the consolidated SQL schema:
```bash
mysql -u root -p < eventease.sql
```
*This script will create the `eventease_db` database and all required tables, indexes, and default platform configurations.*

### 2. Environment Configuration
Create a `.env` file in the root folder based on `.env.example`:
```env
# Flask Core
SECRET_KEY=your-secret-key-here

# MySQL Config
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=eventease_db

# Gemini AI API Key
GEMINI_API_KEY=your-google-gemini-api-key
```

### 3. Install Dependencies
Initialize a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🚀 Running the Application

Start the Flask server:
```bash
python app.py
```
By default, the server runs locally on **`http://localhost:5000`**.

### Default Administrator Seed
On initial startup, EventEase automatically seeds a default administrator account:
*   **Email:** `admin@eventease.com`
*   **Password:** `Admin@123`
*(Banned users, configuration updates, and dashboard statistics can be managed using this account).*
