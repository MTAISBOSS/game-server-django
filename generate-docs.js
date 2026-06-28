const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  PageBreak, LevelFormat, Header, Footer, SimpleField, TabStopType,
  TabStopPosition, ExternalHyperlink
} = require('docx');
const fs = require('fs');

// ─── Colours ─────────────────────────────────────────────────────────────────
const C = {
  primary:   '2E4057',
  accent:    '048A81',
  light:     'E8F4F3',
  header:    '1A2E40',
  rowAlt:    'F5F9F9',
  white:     'FFFFFF',
  border:    'C5D8D6',
  text:      '1A1A2E',
  muted:     '6B7280',
  danger:    'DC2626',
  warning:   'D97706',
  success:   '059669',
  code:      'F3F4F6',
  codeBorder:'D1D5DB',
};

// ─── Helpers ─────────────────────────────────────────────────────────────────
const W = 9360; // content width DXA (1" margins on Letter)

function hr(color = C.accent) {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color, space: 1 } },
    spacing: { before: 80, after: 80 },
    children: [],
  });
}

function spacer(before = 160, after = 80) {
  return new Paragraph({ spacing: { before, after }, children: [] });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 160 },
    children: [new TextRun({ text, bold: true, size: 36, color: C.header, font: 'Arial' })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, color: C.primary, font: 'Arial' })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, color: C.accent, font: 'Arial' })],
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 100 },
    children: [new TextRun({ text, size: 22, color: C.text, font: 'Arial', ...opts })],
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: 'bullets', level },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 22, color: C.text, font: 'Arial' })],
  });
}

function numbered(text, level = 0) {
  return new Paragraph({
    numbering: { reference: 'numbers', level },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 22, color: C.text, font: 'Arial' })],
  });
}

function code(text) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: C.codeBorder };
  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [W],
    rows: [new TableRow({
      children: [new TableCell({
        borders: { top: border, bottom: border, left: border, right: border },
        shading: { fill: 'F0F4F4', type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 160, right: 160 },
        width: { size: W, type: WidthType.DXA },
        children: [new Paragraph({
          children: [new TextRun({ text, font: 'Courier New', size: 18, color: '1F2937' })],
        })],
      })],
    })],
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

// ─── Table builders ──────────────────────────────────────────────────────────
function headerRow(cells, widths) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new TableRow({
    tableHeader: true,
    children: cells.map((text, i) => new TableCell({
      borders,
      shading: { fill: C.primary, type: ShadingType.CLEAR },
      margins: { top: 100, bottom: 100, left: 120, right: 120 },
      width: { size: widths[i], type: WidthType.DXA },
      children: [new Paragraph({
        children: [new TextRun({ text, bold: true, size: 20, color: C.white, font: 'Arial' })],
      })],
    })),
  });
}

function dataRow(cells, widths, shade = false) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
  const borders = { top: border, bottom: border, left: border, right: border };
  return new TableRow({
    children: cells.map((text, i) => new TableCell({
      borders,
      shading: { fill: shade ? C.rowAlt : C.white, type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      width: { size: widths[i], type: WidthType.DXA },
      children: [new Paragraph({
        children: [new TextRun({ text: String(text), size: 20, color: C.text, font: 'Arial' })],
      })],
    })),
  });
}

function table(headers, rows, widths) {
  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      headerRow(headers, widths),
      ...rows.map((r, i) => dataRow(r, widths, i % 2 === 1)),
    ],
  });
}

// ─── ASCII/Text UML diagrams (embedded as code blocks) ───────────────────────
const ARCH_DIAGRAM = `
┌─────────────────────────────────────────────────────────────────┐
│                     UNITY GAME CLIENT                           │
│                   (C# SDK — REST/HTTP JSON)                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP :80 (Nginx)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       NGINX REVERSE PROXY                       │
│    /ws/  ──► Daphne :8001    |    /* ──► Gunicorn :8000         │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
               ▼                          ▼
   ┌───────────────────┐       ┌──────────────────────┐
   │  Daphne (ASGI)    │       │  Gunicorn (WSGI)     │
   │  WebSocket        │       │  REST API + Dashboard │
   │  Live Stats       │       │  4 workers            │
   └─────────┬─────────┘       └──────────┬───────────┘
             │                            │
             ▼                            ▼
   ┌─────────────────────────────────────────────────┐
   │               DJANGO APPLICATION                │
   │  ┌──────────┐ ┌─────────┐ ┌──────────────────┐ │
   │  │   Auth   │ │ Profile │ │   Leaderboard    │ │
   │  │  Service │ │  App    │ │       App        │ │
   │  └──────────┘ └─────────┘ └──────────────────┘ │
   │  ┌──────────┐ ┌─────────────────────────────┐   │
   │  │Resources │ │      Dashboard (Web UI)     │   │
   │  │   App    │ │   Login/Players/LB/Catalog  │   │
   │  └──────────┘ └─────────────────────────────┘   │
   └────────────────────────┬────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
   ┌──────────────────┐       ┌───────────────────────┐
   │   PostgreSQL 16  │       │      Redis 7          │
   │   game_django    │       │  Cache + Channel Layer │
   │   (all models)   │       │  + Celery Broker      │
   └──────────────────┘       └───────────────────────┘
              │
              ▼
   ┌──────────────────┐
   │  Celery Worker   │
   │  Background tasks│
   └──────────────────┘
`.trim();

const DB_SCHEMA = `
players                          profiles
──────────────────────           ──────────────────────
id          UUID PK              player_id  UUID PK FK→players
device_id   TEXT UNIQUE          username   TEXT UNIQUE
phone       TEXT UNIQUE          display_name TEXT
country_code TEXT                bio        TEXT
platform    TEXT                 avatar_id  TEXT
app_version TEXT                 frame_id   TEXT
role        TEXT                 country    TEXT
is_banned   BOOL                 level      INT
is_staff    BOOL                 xp         BIGINT
created_at  TIMESTAMPTZ          created_at TIMESTAMPTZ
updated_at  TIMESTAMPTZ

player_stats                     wallets
──────────────────────           ──────────────────────
player_id   UUID PK FK→players   player_id  UUID PK FK→players
games_played INT                 coins      BIGINT ≥0
wins        INT                  gems       BIGINT ≥0
losses      INT                  tickets    BIGINT ≥0
win_streak  INT                  updated_at TIMESTAMPTZ
best_streak INT
total_xp    BIGINT
total_score BIGINT

seasons                          leaderboard_entries
──────────────────────           ──────────────────────
id          UUID PK              id         UUID PK
name        TEXT                 player_id  UUID FK→players
starts_at   TIMESTAMPTZ          season_id  UUID FK→seasons
ends_at     TIMESTAMPTZ          score      BIGINT
is_active   BOOL                 updated_at TIMESTAMPTZ
created_at  TIMESTAMPTZ          UNIQUE(player_id, season_id)

item_catalog                     player_inventory
──────────────────────           ──────────────────────
item_id     TEXT PK              id         UUID PK
name        TEXT                 player_id  UUID FK→players
description TEXT                 item_id    TEXT FK→item_catalog
category    TEXT                 quantity   INT ≥0
currency    TEXT                 metadata   JSONB
price       BIGINT               acquired_at TIMESTAMPTZ
is_available BOOL                UNIQUE(player_id, item_id)
metadata    JSONB

transactions                     otp_codes
──────────────────────           ──────────────────────
id          UUID PK              id         UUID PK
player_id   UUID FK→players      player_id  UUID FK→players
type        TEXT                 phone      TEXT
currency    TEXT                 code_hash  TEXT
amount      BIGINT               attempts   INT
balance_after BIGINT             expires_at TIMESTAMPTZ
reason      TEXT                 verified_at TIMESTAMPTZ
created_at  TIMESTAMPTZ          created_at TIMESTAMPTZ
`.trim();

const AUTH_FLOW = `
Device Login Flow                    Phone OTP Flow
─────────────────────                ─────────────────────────────────
Unity                                Unity
  │                                    │
  ├─POST /auth/device──────────►  API  ├─POST /auth/phone/link ──►  API
  │  {device_id, platform}          │  │  {phone_number} + JWT        │
  │                                 │  │                              │
  │                         Player.get_or_create()          OTPCode.create()
  │                                 │  │                   send_otp() via Twilio
  │                                 │  │                              │
  │◄─{access_token,                 │  │◄─{message: "OTP sent"}      │
  │   refresh_token,                │  │                              │
  │   player_id,                    │  ├─POST /auth/phone/verify ──► API
  │   is_new_player}                │  │  {phone, otp} + JWT          │
  │                                 │  │                         verify_otp()
  │                                 │  │                         link phone
  │  [token expires in 2h]          │  │◄─{new access+refresh tokens} │
  │                                 │  │
  ├─POST /auth/refresh ──────────► API  Token Refresh Flow
  │  {refresh_token}                │  ─────────────────────
  │                         blacklist old token              │
  │                         issue new pair                   │
  │◄─{new access_token,             │  ├─POST /auth/refresh ──────► API
  │   new refresh_token}            │  │  {refresh_token}             │
  │                                 │  │                   blacklist old
  │                                 │  │                   issue new pair
  │                                 │  │◄─{access_token, refresh_token}
`.trim();

const KUBERNETES_DIAGRAM = `
┌──────────────────── Kubernetes Cluster ─────────────────────────┐
│  Namespace: game-backend                                        │
│                                                                 │
│  ┌─────────────────── game-nginx (2 pods) ──────────────────┐  │
│  │  LoadBalancer Service → :80                              │  │
│  │  Routes /ws/ → game-ws | /* → game-api                  │  │
│  └───────────┬───────────────────────┬───────────────────────┘  │
│              │                       │                          │
│   ┌──────────▼──────┐   ┌────────────▼──────────┐             │
│   │  game-api       │   │  game-ws              │             │
│   │  (3 pods + HPA) │   │  (2 pods)             │             │
│   │  Gunicorn :8000 │   │  Daphne :8001         │             │
│   │  max 10 replicas│   │  WebSocket            │             │
│   └──────────┬──────┘   └────────────┬──────────┘             │
│              │                       │                          │
│              └───────────┬───────────┘                          │
│                          │                                      │
│   ┌──────────────────────▼──────────────────────────────────┐  │
│   │  game-celery (2 pods)  ─────►  redis-service           │  │
│   │  Background tasks             Redis :6379               │  │
│   └────────────────────────────────────────────────────────┘  │
│                          │                                      │
│   ┌──────────────────────▼───────────────┐                     │
│   │  postgres-service (StatefulSet)      │                     │
│   │  PostgreSQL :5432 + 20Gi PVC         │                     │
│   └──────────────────────────────────────┘                     │
│                                                                 │
│  Jobs: game-migrate (once) → game-seed (once)                  │
│  Secrets: game-secrets  |  ConfigMap: game-config              │
└─────────────────────────────────────────────────────────────────┘
`.trim();

const API_ENDPOINTS = `
Request Lifecycle
─────────────────────────────────────────────────────
Unity Client
    │
    ├── GET /profile/me
    │       │
    │       ▼
    │   Nginx (rate limit: 60/min)
    │       │
    │       ▼
    │   Gunicorn → Django Router → MyProfileView.get()
    │       │
    │       ├── JWTAuthentication.authenticate()
    │       │       └── Decode token → load Player from DB
    │       │
    │       ├── ensure_profile(player)  ← get or create
    │       │
    │       ├── Cache check: profile:{player_id}  ← Redis
    │       │       hit  → return cached JSON (60s TTL)
    │       │       miss → SELECT * FROM profiles WHERE player_id=?
    │       │               → cache result → return JSON
    │       │
    │       ▼
    │   HTTP 200 { player_id, username, level, xp, ... }
    │
    └── POST /leaderboard/score
            │
            ▼
        Nginx → Gunicorn → SubmitScoreView.post()
            │
            ├── JWT auth → load Player
            │
            ├── Season.get_active()  ← cached or DB
            │
            ├── SELECT FOR UPDATE leaderboard_entries
            │   (row-level lock — safe for concurrent submits)
            │
            ├── UPDATE score if higher
            ├── INSERT score_history
            ├── COMMIT
            │
            ├── cache.delete_pattern('lb:*')  ← Redis
            │
            └── HTTP 200 { new_score, rank, is_highscore }
`.trim();

// ─── Document assembly ────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: 'bullets',
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: '•',
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }, {
          level: 1, format: LevelFormat.BULLET, text: '◦',
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1080, hanging: 360 } } },
        }],
      },
      {
        reference: 'numbers',
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: '%1.',
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  styles: {
    default: { document: { run: { font: 'Arial', size: 22, color: C.text } } },
    paragraphStyles: [
      {
        id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, font: 'Arial', color: C.header },
        paragraph: { spacing: { before: 400, after: 160 }, outlineLevel: 0 },
      },
      {
        id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: 'Arial', color: C.primary },
        paragraph: { spacing: { before: 300, after: 120 }, outlineLevel: 1 },
      },
      {
        id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, font: 'Arial', color: C.accent },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 },
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.accent, space: 1 } },
          children: [
            new TextRun({ text: 'Game Backend — Technical Documentation', size: 18, color: C.muted, font: 'Arial' }),
            new TextRun({ text: '        Django + PostgreSQL + Redis + Docker + Kubernetes', size: 18, color: C.muted, font: 'Arial' }),
          ],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.accent, space: 1 } },
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          children: [
            new TextRun({ text: 'Confidential — Game Backend v1.0', size: 18, color: C.muted, font: 'Arial' }),
            new TextRun({ text: '\tPage ', size: 18, color: C.muted, font: 'Arial' }),
            new SimpleField("PAGE"),
          ],
        })],
      }),
    },
    children: [

      // ── COVER ──────────────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 1440, after: 240 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: 'GAME BACKEND', size: 64, bold: true, color: C.header, font: 'Arial' })],
      }),
      new Paragraph({
        spacing: { before: 0, after: 120 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: 'Technical Documentation & Architecture Guide', size: 30, color: C.accent, font: 'Arial' })],
      }),
      hr(C.accent),
      spacer(120, 120),
      table(
        ['Property', 'Value'],
        [
          ['Version',       '1.0.0'],
          ['Stack',         'Django 5 · PostgreSQL 16 · Redis 7 · Docker · Kubernetes'],
          ['Architecture',  'Monolithic Django with modular apps'],
          ['API Protocol',  'REST (JSON) — same endpoints as Node.js version'],
          ['Auth',          'JWT (access 2h · refresh 30d) + Device ID + Phone OTP'],
          ['Dashboard',     'Django web views with live WebSocket stats'],
          ['Deployment',    'Docker Compose (dev) · Kubernetes (production)'],
        ],
        [3000, 6360]
      ),
      pageBreak(),

      // ── 1. OVERVIEW ────────────────────────────────────────────────────────
      h1('1. Project Overview'),
      hr(),
      p('This document describes the architecture, data models, API endpoints, deployment configuration, and operational guide for the Game Backend — a Django-based backend service for mobile and desktop games built with Unity.'),
      spacer(),
      p('The backend provides all the infrastructure a game needs: player authentication (device-based and phone OTP), profile management, a seasonal leaderboard, and a full resource economy (currencies, inventory, shop). It also ships with a web-based admin dashboard for live monitoring and management.'),

      spacer(120),
      h2('1.1 Technology Stack'),
      table(
        ['Layer', 'Technology', 'Purpose'],
        [
          ['Web Framework',   'Django 5.0',         'API routing, ORM, admin, template views'],
          ['REST API',        'Django REST Framework', 'Serializers, viewsets, JWT auth'],
          ['WebSocket',       'Django Channels + Daphne', 'Live dashboard stats'],
          ['Database',        'PostgreSQL 16',       'Primary data store'],
          ['Cache / Broker',  'Redis 7',             'API caching, channel layer, Celery'],
          ['Task Queue',      'Celery',              'Background jobs'],
          ['HTTP Server',     'Gunicorn (4 workers)', 'WSGI — REST API and dashboard'],
          ['WS Server',       'Daphne',              'ASGI — WebSocket connections'],
          ['Reverse Proxy',   'Nginx',               'SSL termination, routing, rate limiting'],
          ['Containerisation','Docker + Compose',    'Local development and VPS deployment'],
          ['Orchestration',   'Kubernetes',          'Production at scale'],
        ],
        [2400, 2800, 4160]
      ),

      pageBreak(),

      // ── 2. ARCHITECTURE ────────────────────────────────────────────────────
      h1('2. System Architecture'),
      hr(),
      p('The following diagram shows all components and how they connect. Unity communicates only with Nginx on port 80. All internal services are isolated inside Docker/Kubernetes networking.'),
      spacer(),
      code(ARCH_DIAGRAM),

      spacer(200),
      h2('2.1 Component Roles'),
      table(
        ['Component', 'Instances', 'Port', 'Role'],
        [
          ['Nginx',        '2 (K8s)',    '80/443', 'Entry point — routes HTTP vs WebSocket, rate limiting, SSL'],
          ['Gunicorn',     '3–10 (HPA)', '8000',   'WSGI server — handles all REST API and dashboard requests'],
          ['Daphne',       '2',          '8001',   'ASGI server — handles WebSocket connections for live dashboard'],
          ['Celery Worker','2',          '—',      'Background tasks — scheduled jobs, async operations'],
          ['PostgreSQL',   '1 (STS)',    '5432',   'Primary database — all persistent data in one DB'],
          ['Redis',        '1',          '6379',   'Leaderboard cache (30s TTL), channel layer, Celery broker'],
        ],
        [1800, 1600, 1200, 4760]
      ),

      spacer(200),
      h2('2.2 Django App Structure'),
      p('The Django project is organised into five apps, each handling one domain:'),
      table(
        ['App', 'URL prefix', 'Models', 'Responsibility'],
        [
          ['auth_service', '/auth/',        'Player, OTPCode, RefreshTokenRecord', 'Authentication, JWT, OTP, ban management'],
          ['profile',      '/profile/',     'Profile, PlayerStats',               'Usernames, avatars, XP, level, search'],
          ['leaderboard',  '/leaderboard/', 'Season, LeaderboardEntry, ScoreHistory', 'Scores, rankings, season management'],
          ['resources',    '/resources/',   'Wallet, Transaction, CatalogItem, PlayerInventory, DailyReward', 'Economy — currencies, shop, inventory'],
          ['dashboard',    '/',             '—',                                   'Web admin UI — all 4 domains, live stats'],
        ],
        [1500, 1500, 2800, 3560]
      ),

      pageBreak(),

      // ── 3. DATA MODELS ─────────────────────────────────────────────────────
      h1('3. Database Schema (UML)'),
      hr(),
      p('All models live in a single PostgreSQL database (game_django). Relationships and field types are shown below. UUID primary keys are used throughout for security and distributed compatibility.'),
      spacer(),
      code(DB_SCHEMA),

      spacer(200),
      h2('3.1 Entity Relationships'),
      table(
        ['From', 'Relationship', 'To', 'Notes'],
        [
          ['Player',           '1 → 1',   'Profile',           'Created on first profile update'],
          ['Player',           '1 → 1',   'PlayerStats',       'Created alongside Profile'],
          ['Player',           '1 → 1',   'Wallet',            'Created on first resource access'],
          ['Player',           '1 → 1',   'DailyReward',       'Created on first daily claim'],
          ['Player',           '1 → N',   'OTPCode',           'Multiple OTP requests, one verified per flow'],
          ['Player',           '1 → N',   'Transaction',       'Full audit log of currency changes'],
          ['Player',           '1 → N',   'LeaderboardEntry',  'One entry per season'],
          ['Player',           '1 → N',   'PlayerInventory',   'One row per unique item owned'],
          ['Player',           '1 → N',   'ScoreHistory',      'Every score submission recorded'],
          ['Season',           '1 → N',   'LeaderboardEntry',  'Many players ranked per season'],
          ['CatalogItem',      '1 → N',   'PlayerInventory',   'Same item can be owned by many players'],
        ],
        [2000, 1400, 2000, 3960]
      ),

      pageBreak(),

      // ── 4. AUTH ────────────────────────────────────────────────────────────
      h1('4. Authentication Flow (UML)'),
      hr(),
      p('The system supports two authentication methods. Device-based login is automatic and requires no user input — it is the default for new players. Phone linking is optional and enables account recovery.'),
      spacer(),
      code(AUTH_FLOW),

      spacer(200),
      h2('4.1 JWT Token Specification'),
      table(
        ['Token', 'Lifetime', 'Claims', 'Storage'],
        [
          ['Access Token',  '2 hours',  'player_id, device_id, phone, role, exp', 'Unity: memory only'],
          ['Refresh Token', '30 days',  'player_id, device_id, phone, exp',        'Unity: PlayerPrefs'],
        ],
        [1800, 1600, 3600, 2360]
      ),
      spacer(120),
      p('Refresh tokens are rotated on every use — the old token is blacklisted (stored in rest_framework_simplejwt_blacklistedtoken) and a new pair is issued. This prevents token theft via replay attacks.'),

      spacer(200),
      h2('4.2 Device ID Generation (Unity)'),
      p('The Unity SDK generates a stable anonymous device ID using the following logic:'),
      numbered('Read SystemInfo.deviceUniqueIdentifier (hardware ID)'),
      numbered('SHA-256 hash it (so raw hardware ID never leaves the device)'),
      numbered('Take first 32 hex characters'),
      numbered('Store in PlayerPrefs so it survives reinstalls on Android; regenerate fresh UUID on iOS if unavailable'),

      pageBreak(),

      // ── 5. API REFERENCE ───────────────────────────────────────────────────
      h1('5. REST API Reference'),
      hr(),
      p('All endpoints are served at http://your-server:80. All endpoints except device login and token refresh require a Bearer token in the Authorization header.'),
      spacer(),
      code(API_ENDPOINTS),

      spacer(200),
      h2('5.1 Auth Endpoints'),
      table(
        ['Method', 'Path', 'Auth', 'Description'],
        [
          ['POST', '/auth/device',        'No',  'Register or login with device ID. Creates account if first time.'],
          ['POST', '/auth/phone/link',    'Yes', 'Request OTP SMS to link phone number to current account.'],
          ['POST', '/auth/phone/verify',  'Yes', 'Verify OTP and complete phone link. Returns new tokens.'],
          ['POST', '/auth/phone/login',   'No',  'Send OTP to existing phone-linked account.'],
          ['POST', '/auth/phone/confirm', 'No',  'Verify OTP for phone-only login. Returns tokens.'],
          ['POST', '/auth/refresh',       'No',  'Rotate refresh token. Old token is blacklisted.'],
          ['POST', '/auth/logout',        'No',  'Blacklist refresh token (logout).'],
          ['GET',  '/health',             'No',  'Health check. Returns {status: ok}.'],
        ],
        [800, 2200, 800, 5560]
      ),

      spacer(200),
      h2('5.2 Profile Endpoints'),
      table(
        ['Method', 'Path', 'Description'],
        [
          ['GET',   '/profile/me',             'Get own full profile (level, XP, avatar, phone_linked)'],
          ['PATCH', '/profile/me',             'Update username, display_name, bio, country'],
          ['PATCH', '/profile/me/avatar',      'Update avatar_id and frame_id'],
          ['GET',   '/profile/me/stats',       'Get win/loss/streak/XP statistics'],
          ['GET',   '/profile/{player_id}',    'Get any player\'s public profile + stats'],
          ['GET',   '/profile/?q=',            'Search players by username (max 50 results)'],
        ],
        [800, 2600, 5960]
      ),

      spacer(200),
      h2('5.3 Leaderboard Endpoints'),
      table(
        ['Method', 'Path', 'Description'],
        [
          ['GET',  '/leaderboard/',                  'Global board — current season, paginated'],
          ['GET',  '/leaderboard/top?count=10',       'Top N players (max 100), Redis-cached 30s'],
          ['GET',  '/leaderboard/me',                 'My rank and score in current season'],
          ['POST', '/leaderboard/score',              'Submit match score. Adds to cumulative total.'],
          ['POST', '/leaderboard/friends',            'Leaderboard filtered to provided friend IDs'],
          ['GET',  '/leaderboard/seasons',            'List all seasons'],
          ['GET',  '/leaderboard/seasons/current',    'Get active season details'],
          ['GET',  '/leaderboard/seasons/{id}',       'Get leaderboard for specific season'],
        ],
        [800, 2800, 5760]
      ),

      spacer(200),
      h2('5.4 Resources Endpoints'),
      table(
        ['Method', 'Path', 'Description'],
        [
          ['GET',  '/resources/wallet',                        'Coins, gems, tickets balances'],
          ['GET',  '/resources/inventory',                     'All owned items with quantities'],
          ['POST', '/resources/inventory/{id}/consume',        'Use/consume an inventory item'],
          ['GET',  '/resources/catalog',                       'Shop catalog (filter by ?category=)'],
          ['POST', '/resources/catalog/{item_id}/purchase',    'Buy item — deducts currency, adds to inventory'],
          ['GET',  '/resources/transactions',                  'Paginated transaction history'],
          ['POST', '/resources/daily-reward',                  'Claim daily login reward (7-day streak)'],
        ],
        [800, 2800, 5760]
      ),

      pageBreak(),

      // ── 6. DASHBOARD ───────────────────────────────────────────────────────
      h1('6. Admin Dashboard'),
      hr(),
      p('The dashboard is a server-rendered web UI built with Django views and Tailwind CSS. It is accessible at http://your-server/ and requires a staff or admin account to log in.'),

      spacer(),
      h2('6.1 Dashboard Pages'),
      table(
        ['URL', 'Page', 'Features'],
        [
          ['/',                    'Home',           'Live stats cards (total players, banned, transactions), registration chart (7d), score submissions chart (24h), active season info. Stats update via WebSocket.'],
          ['/players/',            'Players List',   'Searchable, filterable, paginated table. Filter by role, ban status, search by device ID / phone / username.'],
          ['/players/{id}/',       'Player Detail',  'Full player view: identity, wallet, stats, leaderboard rank, inventory, 20 most recent transactions. Actions: ban/unban, grant currency, grant item.'],
          ['/leaderboard/',        'Leaderboard',    'Full ranked table for any season. Season selector dropdown.'],
          ['/seasons/',            'Seasons',        'Create seasons (name, date range, set active). Activate, delete inactive seasons.'],
          ['/catalog/',            'Item Catalog',   'Add new items, toggle availability, delete items. Live toggle via AJAX (no page reload).'],
          ['/django-admin/',       'Django Admin',   'Full model-level CRUD — raw access to all tables.'],
          ['/api/docs/',           'Swagger UI',     'Auto-generated OpenAPI documentation for all REST endpoints.'],
        ],
        [2000, 1600, 5760]
      ),

      spacer(200),
      h2('6.2 Live Stats (WebSocket)'),
      p('The dashboard home page opens a WebSocket connection to /ws/stats/ (served by Daphne via Django Channels). The connection is authenticated — staff/admin only. Stats counters update in real time without page reload.'),
      bullet('Total players'),
      bullet('New registrations today'),
      bullet('Banned players'),
      bullet('Transactions today'),
      bullet('Active season name'),

      pageBreak(),

      // ── 7. DOCKER ──────────────────────────────────────────────────────────
      h1('7. Docker Deployment'),
      hr(),
      p('Docker Compose is the recommended way to run the full stack locally or on a single VPS. Seven services are defined:'),

      spacer(),
      h2('7.1 Services'),
      table(
        ['Service', 'Image / Build', 'Depends On', 'Notes'],
        [
          ['postgres',  'postgres:16-alpine',  '—',               'Persistent volume: postgres_data'],
          ['redis',     'redis:7-alpine',      '—',               'Max 512MB, allkeys-lru eviction, password protected'],
          ['migrate',   'Dockerfile',          'postgres healthy', 'Runs once: python manage.py migrate --noinput'],
          ['seed',      'Dockerfile',          'migrate',         'Runs once: creates superuser, Season 1, catalog items'],
          ['api',       'Dockerfile',          'migrate, redis',  'Gunicorn 4 workers on :8000, health check on /health'],
          ['ws',        'Dockerfile.ws',       'migrate, redis',  'Daphne on :8001, WebSocket only'],
          ['celery',    'Dockerfile',          'migrate, redis',  'Celery worker, 2 concurrency'],
          ['nginx',     'nginx:alpine',        'api, ws',         'Port 80/443 exposed, routes /ws/ to Daphne'],
        ],
        [1400, 2000, 1800, 4160]
      ),

      spacer(200),
      h2('7.2 Quick Start'),
      numbered('Extract the project archive'),
      numbered('cp .env.example .env  (then fill in secrets)'),
      numbered('docker compose up --build'),
      numbered('Open http://localhost — log in with admin / your ADMIN_PASSWORD'),
      numbered('Unity: set Base URL to http://your-server-ip'),

      spacer(120),
      p('The two Dockerfiles serve different purposes:'),
      bullet('Dockerfile — Gunicorn (WSGI). Handles all HTTP requests to the REST API and the dashboard. 4 sync workers by default.'),
      bullet('Dockerfile.ws — Daphne (ASGI). Handles WebSocket connections for the live dashboard only. Nginx routes /ws/ requests here.'),

      pageBreak(),

      // ── 8. KUBERNETES ──────────────────────────────────────────────────────
      h1('8. Kubernetes Deployment'),
      hr(),
      p('For production at scale, the project ships with seven Kubernetes manifest files (k8s/00-07) that deploy the full stack to any Kubernetes cluster.'),

      spacer(),
      code(KUBERNETES_DIAGRAM),

      spacer(200),
      h2('8.1 Manifests'),
      table(
        ['File', 'Contents'],
        [
          ['00-namespace-secrets.yaml', 'Namespace: game-backend. Secret: game-secrets (DB password, JWT secrets, Twilio, admin credentials).'],
          ['01-configmap.yaml',         'Non-secret environment variables shared by all pods (DB host, Redis URL, log level).'],
          ['02-postgres.yaml',          'StatefulSet with 20Gi PVC, headless Service. Configured for game workloads (shared_buffers, work_mem).'],
          ['03-redis.yaml',             'Deployment (1 replica), ClusterIP Service. 512MB max memory, allkeys-lru.'],
          ['04-jobs.yaml',              'Job: game-migrate (python manage.py migrate). Job: game-seed (creates superuser + data). Both run once.'],
          ['05-api-deployment.yaml',    'Deployment (3 replicas), ClusterIP Service, HPA (2–10 pods, 70% CPU / 80% memory thresholds).'],
          ['06-ws-celery.yaml',         'WebSocket Deployment (2 replicas) + Celery Deployment (2 replicas).'],
          ['07-nginx.yaml',             'Nginx ConfigMap + Deployment (2 replicas) + LoadBalancer Service on port 80.'],
        ],
        [2600, 6760]
      ),

      spacer(200),
      h2('8.2 Deploying to Kubernetes'),
      numbered('Build and push Docker images to your registry'),
      numbered('Replace YOUR_REGISTRY/game-backend-django:latest in k8s/04-07 with your actual image'),
      numbered('Fill in secrets: kubectl create secret generic game-secrets --from-env-file=.env -n game-backend'),
      numbered('Apply manifests in order: kubectl apply -f k8s/'),
      numbered('Wait for migrate job: kubectl wait --for=condition=complete job/game-migrate -n game-backend'),
      numbered('Get external IP: kubectl get svc game-nginx-service -n game-backend'),

      pageBreak(),

      // ── 9. UNITY SDK ───────────────────────────────────────────────────────
      h1('9. Unity C# SDK'),
      hr(),
      p('The Unity SDK is four C# files that go in Assets/Scripts/Backend/. The GameBackendClient MonoBehaviour must be attached to a persistent GameObject. All other classes are instantiated automatically.'),

      spacer(),
      h2('9.1 SDK Files'),
      table(
        ['File', 'Class(es)', 'Purpose'],
        [
          ['GameBackendClient.cs', 'GameBackendClient', 'MonoBehaviour singleton. HTTP engine, token storage in PlayerPrefs, auto token refresh when expired.'],
          ['AuthClient.cs',        'AuthClient',         'LoginWithDevice, RequestPhoneLink, VerifyPhoneLink, RequestPhoneLogin, VerifyPhoneLogin, RefreshToken, Logout.'],
          ['GameBackendModels.cs', 'ProfileClient, LeaderboardClient, ResourcesClient + all data models', 'All three service clients and C# model classes matching the API JSON.'],
          ['GameExample.cs',       'GameExample',        'Full working example showing device login → daily reward → leaderboard → score submit → shop flow.'],
        ],
        [2200, 2800, 4360]
      ),

      spacer(200),
      h2('9.2 Minimal Usage Example'),
      code(
`IEnumerator Start() {
    // Login (or register if first time on this device)
    yield return GameBackendClient.Instance.Auth.LoginWithDevice(
        onSuccess: (res) => {
            Debug.Log("Player: " + res.player_id);
            Debug.Log("New player: " + res.is_new_player);
            StartCoroutine(LoadGame());
        },
        onError: (err) => Debug.LogError("Login failed: " + err.Message)
    );
}

IEnumerator LoadGame() {
    // Claim daily reward
    yield return GameBackendClient.Instance.Resources.ClaimDailyReward(
        ok:  (r) => Debug.Log("Coins: +" + r.coins_earned + " (Day " + r.day_streak + ")"),
        err: (e) => Debug.LogWarning(e.Message)
    );

    // Submit a score after a match
    yield return GameBackendClient.Instance.Leaderboard.SubmitScore(
        score:   1500,
        matchId: "match_001",
        ok:  (r) => Debug.Log("Rank: #" + r.rank + (r.is_highscore ? " — New best!" : "")),
        err: (e) => Debug.LogWarning(e.Message)
    );
}`
      ),

      spacer(200),
      h2('9.3 Setup Steps'),
      numbered('Copy the 4 .cs files to Assets/Scripts/Backend/'),
      numbered('Install Newtonsoft.Json: Window > Package Manager > + > Add by name > com.unity.nuget.newtonsoft-json'),
      numbered('Create a GameObject named "GameBackend" in your first scene'),
      numbered('Attach GameBackendClient.cs to it'),
      numbered('Set Base URL to http://your-server-ip in the Inspector'),
      numbered('Check Persist Across Scenes'),
      numbered('The SDK handles token refresh automatically — no manual token management needed'),

      pageBreak(),

      // ── 10. PERFORMANCE ────────────────────────────────────────────────────
      h1('10. Performance & Scaling'),
      hr(),
      h2('10.1 Benchmarks'),
      table(
        ['Operation', 'Expected Latency', 'Throughput (2 CPU / 4GB)'],
        [
          ['Device login',       '20–50ms',  '—'],
          ['Get profile (cached)', '3–8ms',  '—'],
          ['Get profile (DB)',   '10–25ms',  '—'],
          ['Submit score',       '20–50ms',  '—'],
          ['Get leaderboard (cached)', '3–10ms', '—'],
          ['Mixed reads + writes', '—',      '300–600 RPS'],
          ['Read-only',           '—',       '800–1500 RPS'],
        ],
        [2800, 2200, 4360]
      ),

      spacer(200),
      h2('10.2 Caching Strategy'),
      table(
        ['Data', 'Cache Key', 'TTL', 'Invalidated When'],
        [
          ['Public profile',       'profile:{player_id}',      '60s',  'Profile update'],
          ['Global leaderboard',   'lb:global:{season}:{page}', '30s', 'Score submitted'],
          ['Top players',          'lb:top:{season}:{count}',   '30s', 'Score submitted'],
        ],
        [2000, 2800, 1200, 3360]
      ),

      spacer(200),
      h2('10.3 Scaling Recommendations'),
      table(
        ['Concurrent Players', 'Recommended Server', 'Changes Needed'],
        [
          ['1–100',    '2 CPU / 2GB VPS ($12/mo)',    'None — defaults work'],
          ['100–500',  '4 CPU / 4GB VPS ($24/mo)',    'None'],
          ['500–2000', '8 CPU / 8GB VPS ($80/mo)',    'Gunicorn workers: 8'],
          ['2000–10000','K8s: 3 nodes 4CPU/8GB each','HPA kicks in, add Redis replica'],
          ['10000+',   'K8s: 5+ nodes',               'Read replicas for PostgreSQL'],
        ],
        [2200, 3000, 4160]
      ),

      pageBreak(),

      // ── 11. SECURITY ───────────────────────────────────────────────────────
      h1('11. Security'),
      hr(),
      table(
        ['Concern', 'Mitigation'],
        [
          ['JWT theft',          'Short-lived access tokens (2h). Refresh token rotation with blacklisting.'],
          ['OTP brute force',    'Max 3 attempts per OTP. 5 requests per 10 minutes rate limit at Nginx.'],
          ['SQL injection',      'Django ORM with parameterised queries throughout.'],
          ['API abuse',          '60 req/min per IP at Nginx. DRF throttling as second layer.'],
          ['Wallet overdraft',   'SELECT FOR UPDATE row-level lock on wallet before debit. CHECK constraint coins >= 0.'],
          ['Concurrent scores',  'SELECT FOR UPDATE on leaderboard_entries. Atomic transaction.'],
          ['Secrets',            '.env never committed. Kubernetes Secrets for production.'],
          ['Device ID privacy',  'SHA-256 hashed before storage. Raw hardware ID never leaves the device.'],
          ['Admin access',       'Dashboard requires is_staff=True or role=admin. Separate from player auth.'],
          ['CORS',               'Configurable via CORS_ALLOW_ALL / CORS_ORIGINS env vars.'],
        ],
        [2400, 6960]
      ),

      spacer(400),
      hr(C.accent),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 200 },
        children: [new TextRun({ text: 'Game Backend — Technical Documentation v1.0', size: 18, color: C.muted, font: 'Arial', italics: true })],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/mnt/user-data/outputs/GameBackend-Documentation.docx', buffer);
  console.log('Done: GameBackend-Documentation.docx');
}).catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
