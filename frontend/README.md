# GraphVoyageAI Frontend

Modern React + TypeScript dashboard for the GraphVoyageAI travel planner.

## Features

- ⚛️ React 19 with TypeScript
- ⚡ Vite for lightning-fast development
- 🎨 Clean, modern UI design
- 📊 Real-time metrics dashboard with Recharts
- 🔄 API integration with FastAPI backend
- 📱 Fully responsive design
- 🎯 Type-safe development

## Tech Stack

- **Framework**: React 19
- **Language**: TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build:prod
```

The build output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable React components
│   │   └── Layout.tsx   # Main layout with navigation
│   ├── pages/           # Page components
│   │   ├── TravelPlanner.tsx  # Main travel planning interface
│   │   └── Dashboard.tsx      # Metrics dashboard
│   ├── services/        # API services
│   │   └── api.ts       # Axios configuration and API calls
│   ├── types/           # TypeScript type definitions
│   │   └── index.ts     # Shared types
│   ├── styles/          # CSS files
│   │   ├── index.css    # Global styles
│   │   └── App.css      # App-specific styles
│   ├── App.tsx          # Main App component
│   └── main.tsx         # Entry point
├── index.html           # HTML template
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies and scripts
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
VITE_API_URL=http://localhost:8000
```

For production, update to your deployed backend URL.

## Pages

### Travel Planner (`/`)

The main interface for planning trips with AI:
- Submit travel requests
- View supervisor reasoning and agent execution
- Human-in-the-loop approval flow
- View generated travel plans

### Dashboard (`/dashboard`)

Real-time metrics dashboard:
- Total requests and evaluation stats
- Pass rate and safety metrics
- Average and P95 latency
- Hourly request trends
- Success rate visualization
- Request status distribution

## API Integration

The frontend communicates with the FastAPI backend:

- `GET /health` - Health check
- `POST /api/travel` - Submit travel request
- `POST /api/travel/approve` - Approve/reject travel plan
- `GET /api/metrics` - Get system metrics

## Development

### Type Checking

```bash
npm run type-check
```

### Linting (when configured)

```bash
npm run lint
```

## Deployment

The frontend is served by the FastAPI backend in production:

1. Build the frontend:
```bash
npm run build:prod
```

2. The FastAPI app will automatically serve the built files from the `dist/` directory

For separate deployment (CDN, Netlify, Vercel):
- Set `VITE_API_URL` to your backend URL
- Deploy the `dist/` folder

## Contributing

1. Follow the existing code style
2. Use TypeScript types for all data
3. Keep components modular and reusable
4. Write clean, readable code
5. Test changes thoroughly

## License

Same as main project.
