# Sistema-de-Agendamento

## `Frontend`
```Bash
cd frontend
npm install axios bootstrap
npm run dev
```

## `Backend`

```Bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy aiosqlite python-multipart reportlab python-dotenv
pip install "fastapi[standard]"
uvicorn app.main:app --reload
```



