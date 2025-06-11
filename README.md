# DrugGPT - Drug Interaction Checker

A web application that helps users check drug interactions and side effects using FDA data and AI-powered analysis.

## Features

- Drug interaction checking
- Side effects information
- FDA data integration
- User-friendly interface
- Real-time responses

## Tech Stack

### Backend
- FastAPI
- Python 3.9+
- FDA API Integration
- OpenAI Integration

### Frontend
- Vue.js
- TypeScript
- Vite
- TailwindCSS

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── main.py       # Main application file
│   ├── fda_api.py    # FDA API integration
│   └── requirements.txt
└── frontend/         # Vue.js frontend
    ├── src/          # Source files
    ├── public/       # Static files
    └── package.json
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

## Environment Variables

### Backend
- `ENVIRONMENT`: development/production
- `FRONTEND_URL`: Frontend application URL
- `OPENAI_API_KEY`: Your OpenAI API key

### Frontend
- `VITE_API_URL`: Backend API URL

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Deployment

The application is configured for deployment on:
- Backend: Render
- Frontend: Netlify

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 