
# AI_WORKFINDER
Work finder application with AI functionality.

Team: 
- Roman Nadkernychnyi 
- Maksim Pyanin
- Bohdan Hrytsai
- Maksym Stepaniuk

Functionality:
1. Multi Ai-agent system for autonomos searching:
   - Ai-Agent for searching 
   - Ai-Agent for scrapping
   - Ai-Agent for filtering
   - Ai-Agent for applying
   - File storage system for usefull files
2. Web application for interacting with backend:
   - Authentication system
   - Multiagent Ai interaction system
   - File storaging
   - System for applying search parametres
 
# How to start an app
# Frontend: 
From job-agent-frontend/ folder:
```
npm run dev
```
# Backend: 

From backend/ folder: 

For the first time run:
``` 
pip install -r requirements.txt

python venv venv
```
For regular run:
```
source venv/bin/activate

uvicorn app.main:app --reload --port 8001
```
# Container(MongoDB):
In Docker CLI:

``` 
docker run -d --name mongodb -p 27017:27017 mongo:6 
```
