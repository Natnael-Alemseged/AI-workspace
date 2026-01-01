# Moving app.db to data/ Directory

The `app.db` file in the project root should be moved to the `data/` directory for better organization.

## ⚠️ Current Status

The file `app.db` is currently **in use** and cannot be moved while the application is running.

## 📋 Steps to Move

1. **Stop the application** (if running):
   ```bash
   # Stop any running uvicorn/FastAPI processes
   # Press Ctrl+C in the terminal running the server
   ```

2. **Move the database file**:
   ```bash
   # Windows (PowerShell)
   Move-Item -Path "app.db" -Destination "data/app.db" -Force

   # Linux/Mac
   mv app.db data/app.db
   ```

3. **Update DATABASE_URL** in `.env` (if needed):
   ```env
   # Change from:
   DATABASE_URL=sqlite:///./app.db

   # To:
   DATABASE_URL=sqlite:///./data/app.db
   ```

4. **Restart the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

## ✅ Verification

After moving, verify the application works:

1. Check the application starts without errors
2. Test database operations (login, create data, etc.)
3. Confirm `data/app.db` exists and is being used

## 🗑️ Cleanup

Once verified, you can delete this file:
```bash
rm MOVE_APP_DB.md
```

## 📚 Related

- See `data/README.md` for database management information
- See `.gitignore` - the `data/` directory is already excluded from git
