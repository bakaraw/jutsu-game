# File system guide

```
jutsu-game/
├── client/                      # Vite + TS
│   ├── index.html
│   ├── public/
│   │   ├── models/              # self-hosted hand_landmarker.task + wasm
│   │   └── assets/              # sprites, audio, effects
│   └── src/
│       ├── main.ts              # boot only
│       ├── config/              # constants, key binds, ICE server config
│       ├── core/
│       │   ├── bus.ts           # event bus (the only link between modules)
│       │   ├── types.ts         # shared TS types, message shapes
│       │   └── state.ts         # client-side match state (render only)
│       ├── gesture/             # your camera only, no Phaser/WebRTC imports
│       │   ├── camera.ts        # getUserMedia, one stream shared by everything
│       │   ├── tracker.ts       # MediaPipe wrapper
│       │   ├── normalize.ts
│       │   ├── classifier.ts    # KNN
│       │   ├── recorder.ts      # sign calibration mode
│       │   └── combo.ts
│       ├── rtc/                 # opponent video, no game logic
│       │   ├── peer.ts          # RTCPeerConnection setup/teardown
│       │   ├── signaling.ts     # offer/answer/ICE over WebSocket
│       │   └── media.ts         # attach local/remote streams to <video>
│       ├── net/                 # game messages, separate from signaling
│       │   ├── socket.ts        # WebSocket client + reconnect
│       │   ├── matchmaking.ts   # join queue, skip, leave
│       │   └── handlers.ts      # server state -> bus events
│       ├── game/                # Phaser overlay, no MediaPipe/WebRTC imports
│       │   ├── scenes/          # Boot, Battle (transparent), Result
│       │   ├── entities/        # Projectile, HitEffect
│       │   ├── jutsu/           # one file per jutsu
│       │   └── ui/              # HP/chakra bars, combo display
│       └── ui/                  # DOM screens
│           ├── lobby/           # queue, friend code, "finding opponent..."
│           ├── match/           # side-by-side video layout + Phaser mount
│           ├── calibration/     # sign recording wizard
│           ├── report/          # report/skip modal
│           └── auth/            # login, age gate
│
├── server/                      # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                 # REST: auth, profiles, samples, reports, ice-creds
│   │   ├── ws/
│   │   │   ├── matchmaking.py   # queue + pairing
│   │   │   ├── signaling.py     # relay offer/answer/ICE between paired sockets
│   │   │   ├── battle.py        # cast events -> referee
│   │   │   └── rooms.py         # room manager (friend codes + random)
│   │   ├── game/                # authoritative state, cooldowns, damage
│   │   ├── models/              # users, matches, samples, reports, bans
│   │   ├── schemas/             # pydantic REST + WS message shapes
│   │   ├── moderation/          # report handling, bans, rate limits
│   │   ├── core/                # config, security, db session
│   │   └── services/
│   ├── migrations/              # alembic
│   ├── tests/
│   └── pyproject.toml
│
├── infra/
│   ├── coturn/                  # TURN server config
│   └── docker-compose.yml       # api + postgres + redis + coturn
│
├── shared/
│   └── jutsu.json               # combos, cooldowns, damage
│
├── ml/                          # optional offline training
│   ├── data/
│   └── train.py
│
└── README.md

```
