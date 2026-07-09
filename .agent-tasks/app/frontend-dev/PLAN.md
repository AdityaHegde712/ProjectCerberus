# PLAN — @app/frontend-dev

**Role**: Dashboard UI — React + Vite + TypeScript.

## Project Setup

- Scaffold under `dashboard/` using Vite React-TS template
- Install deps: `react-router-dom`, `axios` (or fetch), `canvas` for overlay
- Dark theme (`#121212` background, `#e0e0e0` text) per user preference

## Tasks

### 3.1 — Scaffold project

- `npm create vite@latest dashboard -- --template react-ts`
- Install dependencies
- Set up project structure (components/, pages/, hooks/, api/)
- Configure Vite proxy for API calls (dev mode)

### 3.3 — Build UploadForm component

- Drag-and-drop zone + file picker button
- File type validation (.mp4, .avi, .mov — video formats)
- Upload progress indicator
- Calls API to get presigned URL, then uploads to S3 directly
- Creates job message in SQS via API
- Shows success/error toast

### 3.5 — Build JobStatusList component

- Table of jobs with columns: Job ID, Status, Created, Worker, Actions
- Auto-polls every 5 seconds for status updates
- Color-coded status badges (pending=gray, processing=blue, done=green, error=red)
- Click job → navigate to result viewer

### 3.7 — Build ResultViewer component

- Two-panel layout:
  - **Left**: Detection table — class_name, confidence, bbox coordinates
  - **Right**: Canvas element rendering first frame with bounding boxes overlaid
- Fetch detection JSON from S3 (presigned URL)
- Draw boxes on Canvas using coordinates
- Handle empty state (no detections)
- Handle loading state

## Component Tree

```
App
├── UploadPage
│   └── UploadForm
├── JobsPage
│   └── JobStatusList
└── ResultPage
    └── ResultViewer
        ├── DetectionTable
        └── FrameCanvas
```

## Output Files

```
dashboard/
  src/
    components/
      UploadForm.tsx
      JobStatusList.tsx
      ResultViewer.tsx
      DetectionTable.tsx
      FrameCanvas.tsx
    pages/
      UploadPage.tsx
      JobsPage.tsx
      ResultPage.tsx
    api/
      client.ts          -- API + S3 client calls
    hooks/
      useJobPolling.ts   -- polling hook
      useResult.ts       -- result data hook
    App.tsx
    main.tsx
```

## Verification

All component tests in `dashboard/src/__tests__/` pass. Manual: `npm run dev` → upload a test file → verify flow.
