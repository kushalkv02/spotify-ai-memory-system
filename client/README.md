# Reverie — Spotify-clone client with an AI memory chatbot

A Vue 3 + Vite single-page app that mimics a Spotify-style listening
experience, paired with a chat panel backed by a "Spotify AI memory"
service. The chatbot can see (and talk about) what you've played, liked,
skipped, and followed, and can turn conversational preferences ("more
chill electronic in the evenings") into playback recommendations.

## Stack
- **Vue 3** (`<script setup>`) + **Vite**
- **Pinia** for state (chat / player / user)
- **vue-router** for the shell views
- **axios** for talking to the backend memory API

## Getting started
```bash
npm install
cp .env.example .env   # then point VITE_API_BASE_URL at your backend
npm run dev
```

## Backend contract
This client expects a REST API (see `.env.example` for the base URL) with
roughly the following surface — adjust `src/services/*.js` if your backend
differs:

| Method | Path                       | Purpose                                   |
|--------|----------------------------|--------------------------------------------|
| GET    | /tracks/feed               | Personalized home feed                     |
| GET    | /tracks/search?q=          | Search tracks/artists/albums               |
| GET    | /library                   | Liked tracks, followed artists, playlists   |
| GET    | /playlists/:id             | Playlist detail                            |
| GET    | /albums/:id                | Album detail                               |
| GET    | /artists/:id               | Artist detail                               |
| POST   | /interactions/play         | Log a play event                            |
| POST   | /interactions/skip         | Log a skip event                            |
| POST   | /interactions/like         | Toggle a like                               |
| POST   | /chat/messages              | Send a chat message, get assistant reply    |
| GET    | /chat/messages              | Fetch chat history                          |
| GET    | /chat/quick-replies         | Contextual preference quick-replies         |

## Structure
See `src/` — `components/` (chatbot, layout, tracks), `store/` (pinia),
`services/` (API layer), `views/` (routed pages), `router/`.
