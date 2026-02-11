# GenLayer Key Vault - Quick Start Guide

Get up and running in 5 minutes!

---

## ⚡ Super Quick Start

### Step 1: Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

### Step 2: Start the Server (30 seconds)

```bash
python keyvault_backend.py
```

You should see:
```
GenLayer API Key Vault
Starting server...
API Docs: http://localhost:8000/docs
```

### Step 3: Initialize Admin (30 seconds)

Open a new terminal:

```bash
curl -X POST http://localhost:8000/admin/init
```

You'll get a response like:
```json
{
  "admin_token": "long-random-token-here",
  "message": "Save this token securely!"
}
```

**SAVE THAT TOKEN!** You'll need it for everything.

### Step 4: Open the Dashboard (30 seconds)

Open `keyvault_dashboard.html` in your browser.

1. Click "Initialize Admin Access"
2. Paste your admin token
3. Click "Save Configuration"

Done! 🎉

---

## 📝 Create Your First API Key

### Option A: Using the Dashboard (Easy)

1. Go to the "Create Key" tab
2. Fill in:
   - Service Name: `openweathermap`
   - API Key: `your-actual-api-key`
   - Rate Limit: `100`
3. Click "Create Key"

### Option B: Using curl (Quick)

```bash
curl -X POST http://localhost:8000/admin/keys \
  -H "X-Api-Token: your-admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "openweathermap",
    "api_key": "your-actual-api-key",
    "description": "Weather API key",
    "rate_limit": 100
  }'
```

### Option C: Using the SDK (Pro)

```javascript
import { KeyVaultClient } from './keyvault_sdk.js';

const vault = new KeyVaultClient(
  'http://localhost:8000',
  'your-admin-token'
);

const result = await vault.createKey({
  service_name: 'openweathermap',
  api_key: 'your-actual-api-key',
  description: 'Weather API',
  rate_limit: 100
});

console.log('Key created:', result.key_id);
```

---

## 🧪 Test It Works

### Check Health

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "total_keys": 1,
  "active_keys": 1
}
```

### List Your Keys

```bash
curl http://localhost:8000/admin/keys \
  -H "X-Api-Token: your-admin-token"
```

### Get Usage Stats

In the dashboard:
1. Go to "Keys" tab
2. Click "Stats" on any key
3. See usage details

---

## 🚀 Use in a Contract

### Simple Example

Deploy this contract to GenLayer:

```python
# { "Depends": "py-genlayer:test" }
from genlayer import *

class MyFirstVaultContract(gl.Contract):
    def __init__(self):
        self.vault_url = "http://localhost:8000"
    
    @gl.public.write
    def test_vault_access(self) -> str:
        # In production, this would request the actual key
        # For now, just confirm the vault is accessible
        return "✅ Vault integration ready!"
```

---

## 🔧 Common Tasks

### Add a New API Key

Dashboard → Create Key → Fill form → Create

### Disable a Key (Don't Delete)

Dashboard → Keys → Find key → Disable

### Rotate a Key

```bash
curl -X POST http://localhost:8000/admin/keys/KEY_ID/rotate \
  -H "X-Api-Token: your-admin-token" \
  -d '{"new_api_key": "new-key-value"}'
```

### Check Rate Limit Usage

Dashboard → Keys → Stats

### Export Vault (Backup)

```bash
curl http://localhost:8000/admin/export \
  -H "X-Api-Token: your-admin-token" > vault_backup.json
```

### Import Vault (Restore)

```bash
curl -X POST http://localhost:8000/admin/import \
  -H "X-Api-Token: your-admin-token" \
  -H "Content-Type: application/json" \
  -d @vault_backup.json
```

---

## ⚠️ Troubleshooting

### "Port 8000 already in use"

```bash
# Find what's using port 8000
lsof -i :8000

# Use a different port
uvicorn keyvault_backend:app --port 8001
```

### "Invalid API token"

- Make sure you're using the token from `/admin/init`
- Token must be in `X-Api-Token` header
- No spaces or extra characters

### "Failed to load keys"

- Make sure server is running (`http://localhost:8000/health`)
- Check that admin token is correct
- Look at server logs for errors

### Dashboard won't connect

- Make sure CORS is enabled (it is by default)
- Check browser console for errors
- Try opening dashboard from `http://localhost` or `file://`

---

## 🎯 Next Steps

1. ✅ **Set up production database** - Replace in-memory storage
2. ✅ **Configure HTTPS** - Secure communication
3. ✅ **Set up monitoring** - Track usage and errors
4. ✅ **Deploy to cloud** - Make it accessible to contracts
5. ✅ **Integrate with contracts** - Start using in real apps

---

## 📚 More Resources

- Full README: `KEYVAULT_README.md`
- Backend code: `keyvault_backend.py`
- Contract examples: `keyvault_contracts.py`
- SDK reference: `keyvault_sdk.js`
- Dashboard: `keyvault_dashboard.html`

---

## 💡 Pro Tips

1. **Rate Limits**: Start conservative (100/hour), increase as needed
2. **Permissions**: Use `allowed_contracts` for production
3. **Monitoring**: Check usage stats regularly
4. **Backups**: Export vault state daily
5. **Security**: Rotate keys monthly

---

**That's it!** You're ready to use GenLayer Key Vault. 🔐

Need help? Check the full README or ask in GenLayer Discord.
