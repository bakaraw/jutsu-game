# Jutsu Battle: Learn-by-Doing Roadmap

A web game where two players see each other side by side on video and fight by performing hand-sign combos. This roadmap tells you **what to build, what to learn, and where to read**. It doesn't give you the code. When you're stuck, the "Nudges" in each phase point you in a direction without handing you the answer.

> If a link has moved, search the page title. Docs get reorganized.

---

## The big picture

```
Your webcam → hand tracking → sign classifier → combo detector → "I cast fireball"
                                                                        │ WebSocket
                                           Server (referee: HP, chakra, cooldowns)
                                                                        │
                                  Both browsers show the result + play the effect

Video between players: WebRTC, peer-to-peer. The server only introduces them.
```

**Four rules to keep in your head the whole time:**

1. **Detection is local.** Never upload camera frames to a server for detection.
2. **The server is the referee.** Clients say "I cast X". The server decides if it's allowed and what happens.
3. **Modules talk through events, not imports.** Camera code shouldn't know Phaser exists, and vice versa.
4. **Risky part first.** Recognizing hand signs reliably (Phases 2 to 4) decides if this game works. Don't touch networking until it does.

## Stack

| Job | Tool |
|---|---|
| Tooling | Vite + TypeScript |
| Hand tracking | MediaPipe Tasks Vision (browser) |
| Sign classifier | KNN on landmark features |
| Game layer | Phaser 3 |
| Opponent video | WebRTC |
| Server | FastAPI + WebSockets |

## Suggested folder layout (grow into it, don't create it all on day one)

```
jutsu-game/
├── client/
│   └── src/
│       ├── core/       # event bus, shared types
│       ├── gesture/    # camera, tracking, features, classifier, combos
│       ├── game/       # Phaser scenes, effects
│       ├── net/        # game messages over WebSocket
│       ├── rtc/        # WebRTC video + signaling
│       └── ui/         # lobby, calibration, report screens
├── server/             # FastAPI
└── shared/             # data both sides read (jutsu definitions)
```

## How to work through this

- **One phase at a time.** Each has a checkpoint. Don't move on until you pass it.
- **Commit after every checkpoint.** You'll want somewhere to go back to.
- **Read before you code.** Skim the linked docs first, then try, then go back to the docs when stuck.
- **Make it ugly first.** Console logs and colored rectangles are fine. Polish comes last.

---

## Phase 0: Setup and mindset

**Goal:** a working toolchain.

**You need:** Node.js LTS, Python 3.11+, Git, a webcam, Chrome or Edge.

**Learn:**
- What npm is and what `package.json` does
- What a dev server is vs. a production build
- Why `localhost` can use the camera without HTTPS but your deployed site can't

**Docs:**
- Vite guide: https://vite.dev/guide/
- TypeScript handbook (read "The Basics" and "Everyday Types"): https://www.typescriptlang.org/docs/handbook/intro.html
- MDN, secure contexts: https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts

**Checkpoint:** you can run a Vite + TypeScript project and see a page at `localhost:5173`.

---

## Phase 1: Scaffold and the event bus

**Goal:** a clean project skeleton and a tiny way for modules to talk.

**Build:**
- Create the Vite project with the TypeScript template.
- Install Phaser and MediaPipe's vision package from npm.
- Make the folders you need *right now* (`core/`, `gesture/`, `game/`).
- Build a tiny event bus: a thing you can `on`, `off`, and `emit` named events on.
- Make a `shared/` folder holding a data file that describes your jutsu (name, hand-sign sequence, chakra cost, cooldown, damage). Get the client to import it.

**Learn:**
- The observer / pub-sub pattern, and why it keeps modules independent
- ES modules (`import` / `export`) and how TypeScript types event payloads
- Vite path aliases and TS `paths` (so you can import from `shared/` outside the client folder)
- How to import JSON in TypeScript (`resolveJsonModule`)

**Docs:**
- Observer pattern: https://gameprogrammingpatterns.com/observer.html
- Event queue pattern: https://gameprogrammingpatterns.com/event-queue.html
- Vite `resolve.alias`: https://vite.dev/config/shared-options.html#resolve-alias
- TS module resolution: https://www.typescriptlang.org/docs/handbook/modules/introduction.html

**Nudges:**
- If your editor complains about Node things in `vite.config.ts`, you probably need Node's type definitions as a dev dependency. Read the error message literally, it tells you.
- ES modules don't have `__dirname`. Look up how to get a file path from `import.meta.url`.

**Checkpoint:** one module emits an event, another logs it, and neither imports the other.

---

## Phase 2: Camera and hand skeleton

**Goal:** see your own hands tracked live, with a skeleton drawn on top.

**Build:**
- Ask for camera permission and show your webcam in a `<video>` element.
- Load MediaPipe's Hand Landmarker in VIDEO mode, 2 hands max.
- Every new frame, run detection and emit the result on your bus.
- Draw the 21 landmarks and connections on a canvas layered over the video.
- Mirror *your own* video so it feels like a mirror. Make sure the canvas mirrors with it.

**Learn:**
- `getUserMedia`, `MediaStream`, and why you'll reuse one stream for display, detection, and later WebRTC
- The 21-landmark hand model: which index is the wrist, fingertips, knuckles
- Normalized coordinates (0 to 1) vs. pixels
- `requestAnimationFrame` and why you only want to process *new* video frames
- Handedness (left/right) in MediaPipe's output, and the gotcha that mirroring can flip it
- Running a model in WASM + GPU, and why the first load is slow

**Docs:**
- Hand Landmarker overview (landmark diagram is here): https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
- Hand Landmarker for web: https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/web_js
- Try it in the browser first: https://mediapipe-studio.webapps.google.com/studio/demo/hand_landmarker
- MDN `getUserMedia`: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
- MDN `requestAnimationFrame`: https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame
- MDN Canvas basics: https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial

**Nudges:**
- Skeleton in the wrong place? Check that canvas size, video size, and CSS size agree.
- Skeleton mirrored the wrong way? Mirror the canvas the same way as the video.
- Slow or janky? Lower the camera resolution before anything else.
- The MediaPipe docs page has a drawing helper. Look for it before writing your own.

**Checkpoint:** both hands tracked smoothly at around 30fps, skeleton aligned with your real hands.

---

## Phase 3: Recognize hand signs

**Goal:** the app labels your current hand shape correctly, live.

This is the most important phase. Take your time.

**Build:**
1. **A feature function:** turns the landmarks of the current frame into a list of numbers.
2. **A recorder:** while you hold a sign, collect lots of samples under a label.
3. **A classifier:** given a new sample, find the closest recorded ones and vote.
4. **Persistence:** save samples so you don't re-record every refresh.
5. **An evaluation tool:** a way to see which signs get confused with which.

**Design questions to answer before coding:**
- How do I make features that don't change if I move my hand around the frame? (Think: relative to what?)
- How do I make them not change if I move closer to or farther from the camera? (Think: divided by what?)
- Two hands: how do I keep the left and right hand in a consistent order in the feature list? What do I do when only one hand is visible?
- How confident does the classifier need to be before I trust its answer? What should it say otherwise?

**Learn:**
- Feature engineering basics: normalization, translation and scale invariance
- K-nearest neighbors, and the effect of `k`
- Why you need a "none" class (hands resting, mid-transition)
- Train/test thinking, confusion matrices, and what "overfitting to yourself" looks like
- Why occlusion (fingers hiding fingers) breaks hand tracking, and why that matters for your sign design

**Docs:**
- KNN explained (scikit-learn, for the concepts, even though you're writing yours in TS): https://scikit-learn.org/stable/modules/neighbors.html
- Confusion matrix: https://scikit-learn.org/stable/modules/model_evaluation.html#confusion-matrix
- MDN `localStorage`: https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API
- Optional shortcut to compare against: MediaPipe's pretrained Gesture Recognizer: https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer

**Designing signs that actually work:**
- Real Naruto signs interlock fingers, which MediaPipe tracks badly. Make **simplified look-alikes** where all fingers stay visible.
- Differ by *which fingers are extended*, not by subtle angles.
- Start with **5 or 6 signs plus "none"**. Add more only when those are solid.
- Record each sign ~100 times while slowly varying distance, tilt, and position. Record in different lighting. Get a friend's hands in there too.

**Nudges:**
- If two signs keep getting confused, the fix is almost always **redesigning one sign**, not more data.
- If accuracy is great for you and bad for friends, you need data from other people, or per-player calibration.
- A feature list that's mostly zeros for a missing hand is fine. Just be consistent between recording and predicting.
- Do the leave-one-out idea: for each sample, pretend it's new and classify it using all the others. Count the mistakes per sign.

**Checkpoint:** 6+ signs and "none" recognized correctly most of the time, and you've looked at a confusion matrix and fixed at least one confused pair.

---

## Phase 4: Combo detection

**Goal:** performing a sequence of signs triggers a jutsu.

**Build:** a small state machine that watches the stream of predicted signs and emits "jutsu detected" when a defined sequence is completed.

**Design questions:**
- How long must a sign be held before it counts? (Too short = flicker triggers it. Too long = feels sluggish.)
- How do I count one hold once, instead of every frame?
- How long can the player pause between signs before the attempt resets?
- What if two jutsu share a prefix or one is the ending of another? Which wins?
- How do I let a player do the same sign twice in a row?

**Learn:**
- Finite state machines
- Debouncing vs. smoothing (hold-time vs. majority vote over recent frames)
- Time handling with `performance.now()`, not frame counts

**Docs:**
- State pattern: https://gameprogrammingpatterns.com/state.html
- MDN `performance.now()`: https://developer.mozilla.org/en-US/docs/Web/API/Performance/now

**Also build a tiny HUD** showing the current sign and the combo progress. You'll debug and play 10x faster with it.

**Nudges:**
- Test the combo logic **without a camera** by feeding it fake sign sequences from a debug key. Separates "is my logic right" from "is my recognition right".
- Choose combos where no jutsu's sequence ends with another's full sequence.

**Checkpoint:** performing a combo logs the jutsu name. Fumbling resets it. The HUD shows progress.

---

## Phase 5: Phaser overlay

**Goal:** a completed combo plays a visible effect over your video.

**Build:**
- Put a **transparent** Phaser canvas on top of the video panels.
- One scene, with HP and chakra bars and a function that plays a jutsu effect (start with a projectile moving from one side to the other, then a hit flash).
- Connect it: "jutsu detected" event → play the effect. (Offline for now: no server, no opponent.)

**Learn:**
- Phaser's game config, scenes, and lifecycle (`preload`, `create`, `update`)
- Game objects, tweens, and how to destroy things you create so you don't leak
- Layering with CSS: absolute positioning, `pointer-events`, z-index
- Keeping Phaser and the camera loop independent (each has its own loop; the bus connects them)

**Docs:**
- Phaser docs: https://docs.phaser.io/
- Official first-game tutorial: https://phaser.io/tutorials/making-your-first-phaser-3-game
- Examples to steal ideas from (tweens, particles): https://phaser.io/examples

**Nudges:**
- Start with colored shapes. Sprites later.
- Make a debug key that fires a jutsu so you can work on visuals without doing hand signs.
- When you add one file per jutsu, keep a lookup from jutsu name to its effect, so adding a jutsu doesn't mean editing the scene.

**Checkpoint:** you do the signs, and a projectile flies across the screen over your webcam.

---

## Phase 6: The server referee

**Goal:** two browsers join the same room, and casts are validated and shared by the server.

**Build:**
- A FastAPI app with one WebSocket endpoint.
- A way for two players to end up in the same room (start with a shared **friend code**).
- Server-side state per player: HP, chakra (with regeneration over time), per-jutsu cooldowns.
- Handling "cast" messages: check the jutsu exists, the player has enough chakra, the cooldown is over; then update state and broadcast results to both players.
- A win condition and a game-over message.
- Client side: a small WebSocket module that turns server messages into bus events, and sends cast events from your bus to the server.

**Design questions (write the answers down before coding):**
- What are all the message types, in each direction, and what's in each?
- What does the server do when a cast is invalid? What should the player see?
- Where does the server read the jutsu data from? (Hint: the same shared file as the client.)
- What happens if a player disconnects mid-match?
- How do two players get matched to each other and given IDs?

**Learn:**
- WebSockets: the handshake, message framing, connection lifecycle
- Async Python (`async` / `await`) and how FastAPI handles WebSockets
- Authoritative server model: why you never trust the client
- JSON message design, and optionally validating message shapes with Pydantic
- Time-based regeneration: compute it from timestamps instead of running a ticking loop

**Docs:**
- FastAPI tutorial: https://fastapi.tiangolo.com/tutorial/
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- MDN WebSocket API: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
- Python asyncio intro: https://docs.python.org/3/library/asyncio.html
- Pydantic: https://docs.pydantic.dev/latest/

**Nudges:**
- Keep rooms in a plain dictionary in memory. It's fine until you run multiple server instances.
- Clean up on disconnect, in a place that runs no matter how the connection ended.
- Test with two browser windows (different browsers help, since two tabs can fight over one camera).
- Add a "denied" message so you can show *why* a cast failed.

**Checkpoint:** two windows join the same code, either side casts, both screens show the effect, and HP/chakra come from the server.

---

## Phase 7: Opponent video with WebRTC

**Goal:** each player sees the other's webcam in the right-hand panel.

**Build:**
- Create a peer connection on each side and add your local camera tracks to it.
- Use your **existing WebSocket** as the signaling channel to pass the offer, answer, and ICE candidates between the two peers.
- Show the incoming remote stream in the second `<video>`.
- Clean up properly when the match ends or the opponent leaves.

**Learn:**
- What signaling is, and why WebRTC needs *something else* to introduce the peers
- SDP offers/answers, ICE candidates, STUN vs. TURN
- Who creates the offer (decide which player is the "initiator" and let the server tell them)
- The race condition: ICE candidates can arrive before the remote description is set. Think about how to process signals in order
- Why you mirror only your own video, never the opponent's

**Docs:**
- MDN WebRTC overview: https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API
- Connectivity (ICE, STUN, TURN explained well): https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Connectivity
- Signaling and video calling walkthrough: https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Signaling_and_video_calling
- Perfect negotiation (read after your first version works): https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Perfect_negotiation
- Official samples, great to poke at: https://webrtc.github.io/samples/
- WebRTC for the curious: https://webrtc.org/getting-started/overview

**Nudges:**
- Build it as a separate module that only talks to the rest through the bus.
- Get it working between two tabs on one machine first, then two devices.
- Black remote video? Check: did the track get added, was the answer sent back, are ICE candidates being relayed both directions, and is anything blocked by a strict network (see Phase 10)?
- Make sure the camera is started *before* matching, so there's a stream to send.

**Checkpoint:** two devices see each other's video, and casts still work.

---

## Phase 8: Matchmaking and lobby

**Goal:** a real flow instead of a hardcoded room.

**Build:**
- A lobby screen: **Find match**, **Enter friend code**, **Calibrate signs**.
- Server-side queue: first player waits, second player is paired with them.
- Skip / leave, rematch, and a results screen.
- A calibration screen so players can record their own signs (your recorder from Phase 3, made friendly).

**Learn:**
- Queue-based matchmaking and the edge cases: player leaves while waiting, double-joins, odd numbers
- Basic DOM UI. If it gets heavy, this is the point where a UI framework like Svelte or React earns its keep. Use it for these screens only, and keep it away from the camera and game loops.
- Per-user calibration data and why it beats one global model

**Docs:**
- MDN DOM introduction: https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model/Introduction
- Svelte tutorial (if you go that way): https://svelte.dev/tutorial
- React learn (if you go that way): https://react.dev/learn

**Checkpoint:** two strangers can queue up, get paired, fight, and either one can skip to the next match.

---

## Phase 9: Safety and moderation

**Goal:** don't build something that gets people hurt. Do this before any public random matchmaking.

Random video chat attracts abuse. It's the thing Omegle-style products fail at. Start with **friend codes only** and add random matching when these exist:

- **Accounts** required before matchmaking, plus an **age gate** (adults only) in signup and terms.
- A **report button** in every match, and a place to store reports.
- An always-visible, instant **skip**.
- **Bans** and **rate limits** (queue joins, reports).
- Consider starting each match with video blurred or off for a few seconds.
- A clear **privacy policy and terms**: say what you store and that video is peer-to-peer and not recorded.

**Learn:**
- Authentication basics (sessions or JWT, password hashing)
- Rate limiting
- The privacy and child-safety rules where you plan to operate

**Docs:**
- FastAPI security tutorial: https://fastapi.tiangolo.com/tutorial/security/
- OWASP cheat sheets (auth, rate limiting, etc.): https://cheatsheetseries.owasp.org/
- SQLModel (for storing users and reports): https://sqlmodel.tiangolo.com/
- Alembic migrations: https://alembic.sqlalchemy.org/

**Checkpoint:** you can ban an abusive account and a reported match leaves a record you can review.

---

## Phase 10: TURN, deployment, scaling

**Goal:** it works for real people on real networks.

**Learn and do:**
- **TURN.** Direct peer-to-peer fails for a notable share of players behind strict NATs, which shows up as a black remote video. You need a TURN relay. Easiest: a hosted TURN service, with credentials fetched from your server so secrets stay out of the client. Later: self-host coturn.
- **HTTPS and WSS.** The camera requires HTTPS in production, so your WebSocket must be `wss://`.
- **Environment config.** Don't hardcode the server URL. Use Vite env variables.
- **Self-host MediaPipe's files** (WASM and the model) instead of relying on a CDN.
- **Deploy** the frontend as static files and the backend somewhere that supports WebSockets.
- **Scaling.** In-memory rooms mean *one server instance*. When you outgrow that, move queue/room state to Redis and use sticky sessions.

**Docs:**
- Vite env variables: https://vite.dev/guide/env-and-mode.html
- Vite building for production: https://vite.dev/guide/build.html
- Vite static deploy guide: https://vite.dev/guide/static-deploy.html
- FastAPI deployment: https://fastapi.tiangolo.com/deployment/
- coturn: https://github.com/coturn/coturn
- MDN on ICE servers: https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection/RTCPeerConnection#iceservers
- Redis pub/sub: https://redis.io/docs/latest/develop/interact/pubsub/

**Checkpoint:** two people on different networks and different devices can play each other.

---

## Milestones at a glance

1. See your skeleton
2. Recognize 6+ signs reliably
3. Combos fire jutsu in the console
4. Cast jutsu over your own video
5. Server-refereed match via friend code
6. See your opponent's video
7. Random matchmaking, report, skip
8. TURN and deployed

## After it works

- Sprites, sound, screen shake, better effects
- More jutsu, each with a unique effect
- Blocks and counters (timed signs)
- Calibration saved to the player's account
- Ranked matches and leaderboards
- A stronger classifier trained offline in Python from exported landmark data, then loaded back in the browser

## Debugging habits that will save you hours

- **Isolate the layer.** Is it detection, classification, combo logic, networking, or rendering? Test each alone with fakes (debug keys, fake sign streams, a fake server message).
- **Log the boundary.** Print what goes *into* and *comes out of* each module via the bus.
- **Check the data, not the code.** Most "bugs" in Phase 3 are bad or inconsistent samples.
- **Use the browser devtools.** Network tab for WebSocket frames, `chrome://webrtc-internals` for WebRTC state, Console for everything else.
- **Change one thing at a time.**

## Common traps (concepts, not fixes)

- Mirroring: apply it to your own view only, and keep recording and predicting consistent about it.
- Hand order: left/right assignment changing between recording and predicting silently ruins accuracy.
- Frame spam: sending every detection to the server instead of only completed jutsu.
- Trusting the client: validating nothing on the server.
- Over-building: creating every folder and feature up front. Build the next checkpoint, then stop.

## Reading list, by topic

| Topic | Link |
|---|---|
| Vite | https://vite.dev/guide/ |
| TypeScript | https://www.typescriptlang.org/docs/ |
| MediaPipe Hand Landmarker | https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker |
| MediaPipe web guide | https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/web_js |
| getUserMedia | https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia |
| Canvas | https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API |
| Phaser | https://docs.phaser.io/ |
| Game programming patterns | https://gameprogrammingpatterns.com/ |
| KNN and evaluation | https://scikit-learn.org/stable/modules/neighbors.html |
| FastAPI | https://fastapi.tiangolo.com/ |
| WebSockets | https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API |
| WebRTC | https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API |
| WebRTC samples | https://webrtc.github.io/samples/ |
| Security basics | https://cheatsheetseries.owasp.org/ |
