
---
# Django Channels Real-Time Chat Application

This project is a real-time chat application built using Django, Django Channels, and WebSockets. It features a modern, single-page interface with a split-pane layout—displaying the chat list on the left and the active chat on the right. Users can engage in private and group chats with persistent message history and live updates, all without page reloads.

---

## Features

- **Authentication-first workflow**: Users must log in to access the dashboard
- **Real-time messaging**: Powered by Django Channels and WebSocket communication
- **Online status and last seen**: Displays live online indicators and last active times
- **Persistent chat history**: Previous messages load automatically when a conversation is opened
- **Private and group chat support**: Users can initiate one-on-one chats or create/join group conversations
- **Dynamic user experience**: All actions are handled using AJAX and WebSockets without page reloads
- **Password recovery via security question**: Users can reset their password using a predefined question set during registration (email not required)
- **Custom 404 error page**: A user-friendly and styled error page for invalid routes

---

## Technology Stack

| Component      | Technology                      |
|----------------|----------------------------------|
| Backend        | Django, Django REST Framework    |
| Real-Time      | Django Channels, WebSockets      |
| Frontend       | HTML, CSS, JavaScript, AJAX      |
| Authentication | Django's built-in auth system    |
| Database       | SQLite (default, easily switchable) |

---

## Project Structure

```

DjangoChannelsChatApp-main/
├── accounts/                # Handles registration, login, user profile, online status
├── ChatApp/                 # Core chat functionality, models, consumers, routing
│   └── templates/
│       └── dashboard.html   # Main real-time chat interface
├── ChatProject/             # Django project settings and root URLs
├── templates/               # login.html, register.html, 404.html, base.html
├── static/                  # CSS files, images, and other static assets
├── db.sqlite3               # Default development database
├── manage.py                # Django management script
├── README.md                # Project overview and documentation

````

---

## Application Flow

1. **Authentication**
   - The root URL (`/`) redirects to the login page.
   - Only authenticated users can access the main chat dashboard.

2. **Dashboard (`/dashboard/`)**
   - Split interface layout:
     - Left pane: Chat list (users and groups), new chat/group creation, online indicators.
     - Right pane: Active chat area with avatars, message input, and real-time updates.
   - All chat functionalities are handled asynchronously via WebSocket and AJAX.

3. **Real-Time Communication**
   - Messages are delivered instantly to all participants.
   - Online status and last seen are updated dynamically.
   - Conversation history is loaded efficiently without reloading the page.

---

## Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/meerabijaz/Django-Web-Application-Using-DRF-and-Web-Socket
````

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Apply database migrations**

   ```bash
   python manage.py migrate
   ```

4. **Create a superuser (optional)**

   ```bash
   python manage.py createsuperuser
   ```

5. **Start the development server**

   ```bash
   python manage.py runserver
   ```

6. **Access the application**

   Open your browser and navigate to: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Password Recovery

During registration, users are prompted to set a security question and answer. This is used for password recovery, allowing users to reset their password without the need for email-based verification. This feature is implemented to support local development and simplified recovery in test environments.

---

## Error Handling

* All forms include CSRF protection.
* A custom 404 page is used for improved user experience on invalid routes.
* Templates follow Django best practices using inheritance from `base.html`.

---

## Deployment Notes

To deploy the project in a production environment:

* Set `DEBUG = False` in `settings.py`
* Configure `ALLOWED_HOSTS` appropriately
* Use PostgreSQL or another production-grade database
* Replace `InMemoryChannelLayer` with `RedisChannelLayer` for scalability
* Use `collectstatic` and configure a web server (e.g., Nginx) to serve static files

---
