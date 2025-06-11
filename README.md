# DrugGPT - Drug Interaction Checker

A web application that helps users check drug interactions and side effects using FDA data.

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

### Frontend
- React
- TypeScript
- Vite
- TailwindCSS

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
