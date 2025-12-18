# Ableton Triage Assistant

A macOS application for triaging, organizing, and managing Ableton Live projects through a 5-phase workflow.

## Features

### Phase 1: Deep Scan
- Crash-proof directory crawling with permission handling
- Semantic filename decoding (Key, BPM, keywords)
- Backup folder analysis for "sweat equity" calculation
- Version clustering (groups v1, v2, FINAL variants)
- Signal scoring algorithm (0-100)

### Phase 2: Virtual Triage
- Dashboard sorted by Signal Score
- Instant audio preview with waveform visualization
- Triage actions: Trash, Salvage, Must Finish

### Phase 3: Hygiene Loop
- Track harvesting progress for Salvage projects
- Track "Collect All and Save" status for Must Finish projects

### Phase 4: Grand Migration
- Dependency validation (checks for external file references)
- Safe file operations with rollback capability
- JSON manifest logging
- Archive and curated folder organization

### Phase 5: Studio Manager
- Genre tagging
- Production status tracking
- Drag-and-drop priority ordering

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Database**: SQLite
- **Audio**: Wavesurfer.js
- **Packaging**: PyInstaller + pywebview

## Development Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8765
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Building for Production

```bash
chmod +x build/build_macos.sh
./build/build_macos.sh
```

The built application will be in `build/dist/Ableton Triage Assistant.app`

## Project Structure

```
AbletonSalvageGemini/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── models/    # Database models
│   │   ├── services/  # Business logic
│   │   └── utils/     # Utilities
│   └── tests/
├── frontend/          # React frontend
│   └── src/
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       ├── services/
│       └── types/
├── data/              # Database and manifests
│   ├── manifests/
│   └── rollback/
└── build/             # Build scripts
```

## License

MIT

# AbletonProjectTriageMain
