# Kenyan Universities Interaction Platform

## 🎯 Project Overview

Interactive platform for Kenyan university students featuring:

- News updates
- Discussion forums
- Event calendars
- Resource sharing
- Live messaging

## 👥 Team & Features

### Live Communications

- **Live Chats & Messaging**
  - Frontend: Jean
  - Backend: Fidel

### Content & Engagement

- **Feeds & Trending**

  - Frontend: Fabian
  - Backend: Fidel
- **Polls**

  - Frontend: Debby
  - Backend: Victor
- **Event Calendar**

  - Full Stack: Incognito

### Community Features

- **Forums & Communities**

  - Frontend: Victor
  - Backend: Fidel
- **News Updates**

  - Full Stack: Mato
- **Maps**

  - Full Stack: Peter
- **Resource Sharing**

  - Full Stack: Samtech
- **Marketplace**

  - Full Stack: Victor
- **Student Profiles**

  - Full Stack: Fidel

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript (React/Vue/Angular)
- **Backend:** Django
- **Database:** SQLite
- **APIs:** REST

## ✅ TODO Progress Tracker

Use this list to track progress. Mark tasks as completed by adding a ✅ at the start.

### Live Communications

- [✅] **Live Chats & Messaging** - Frontend (Jean)

- [✅] **Live Chats & Messaging** - Backend (Fidel)

### Content & Engagement

- [ ] **Feeds & Trending** - Frontend (Fabian)

- [✅] **Feeds & Trending** - Backend (Fidel)

- ### Polls
- [✅] **Polls Creation and Views** - Frontend (Debby)
- [✅] **Polls Creation and Views** - Backend (Victor)

- [ ] **Event Calendar** - Frontend (Saints)
- [ ] **Event Calendar** - Backend (Incognito)

### Community Features

- [ ] **Forums & Communities** - Frontend (Victor)
- [ ] **Forums & Communities** - Backend (Fidel)
- [❌] **News Updates** - Full Stack (Mato)
- [ ] **Maps** - Full Stack (Peter)

- [✅] **Resource Sharing** - Full Stack (Samtech)

- [✅] **Marketplace** - Full Stack (Victor)

- [✅] **Student Profiles** - Full Stack (Fidel)


## 🚀 Development Setup

1️⃣ *Clone & Enter Project*

```bash
git clone https://github.com/KenyanAudo03/Campus_Interaction.git
cd Campus_Interaction
```

2️⃣ *Install Requirements*

```bash
pip install -r requirements.txt
```

3️⃣ *Initialize Database*

```bash
python manage.py makemigrations
python manage.py makemigrations profiles
python manage.py migrate
mkdir static staticfiles media
mkdir media/profile_pics
cp static/images/default-avatar.png media/profile_pics/default.png
```

4️⃣ *Start Server*

```bash
python manage.py runserver
```

5️⃣ *Create New App (if needed)*

```bash
django-admin startapp your_app
```
