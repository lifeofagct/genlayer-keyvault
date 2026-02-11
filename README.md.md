# GenLayer API Key Vault

**Secure API key management for GenLayer smart contracts**

Stop hardcoding API keys in your contracts. GenLayer Key Vault provides encrypted storage, permission management, rate limiting, and key rotation for all your contract API needs.

---

## 🎯 Problem

Traditional smart contracts face a dilemma with API keys:

❌ **Hardcode in contract** → Keys exposed on blockchain  
❌ **Store off-chain** → Contract can't access them  
❌ **Use centralized service** → Defeats decentralization purpose  

**GenLayer Key Vault solves this.**

---

## ✨ Features

### 🔐 Security
- **Encrypted storage** - Keys encrypted at rest with Fernet encryption
- **Permission-based access** - Control which contracts can use which keys
- **No on-chain exposure** - Keys never stored on blockchain
- **Secure key rotation** - Update keys without redeploying contracts

### 📊 Management
- **Rate limiting** - Prevent abuse with configurable limits
- **Usage tracking** - Monitor API call patterns
- **Multi-service support** - Manage keys for all your APIs
- **Admin dashboard** - Visual interface for key management

### 🚀 Developer Experience
- **Simple SDK** - JavaScript library for easy integration
- **Contract examples** - Ready-to-use GenLayer contract patterns
- **REST API** - Standard HTTP interface
- **Complete docs** - Everything you need to get started

---

## 📦 What's Included

```
genlayer-keyvault/
├── keyvault_backend.py          # FastAPI backend service
├── keyvault_contracts.py        # GenLayer contract examples
├── keyvault_sdk.js              # JavaScript SDK
├── keyvault_dashboard.html      # Admin dashboard
└── README.md                    # This file
```

---

## 🚀 Quick Start

### 1. Start the Backend

```bash
# Install dependencies
pip install fastapi uvicorn cryptography

# Run the server
python keyvault_backend.py
```

Server starts at `http://localhost:8000`

### 2. Initialize Admin Access

```bash
curl -X POST http://localhost:8000/admin/init
```

**Save the admin token you receive!**

### 3. Create Your First Key

```javascript
import { KeyVaultClient } from './keyvault_sdk.js';

const vault = new KeyVaultClient('http://localhost:8000', 'your-admin-token');

await vault.createKey({
  service_name: 'openweathermap',
  api_key: 'your-actual-api-key',
  description: 'Weather API for insurance contracts',
  allowed_contracts: ['0x1234...'],  // Optional: restrict access
  rate_limit: 100  // 100 requests per hour
});
```

### 4. Use in Your Contract

```python
# { "Depends": "py-genlayer:test" }
from genlayer import *

class MyContract(gl.Contract):
    def __init__(self, vault_url: str):
        self.vault_url = vault_url
    
    @gl.public.write
    def get_weather(self, city: str) -> str:
        # Contract requests API key from vault
        # Vault checks permissions and rate limits
        # Returns decrypted key
        # Contract uses key for API call
        # Key is never exposed
        pass
```

### 5. Open the Dashboard

Open `keyvault_dashboard.html` in your browser to manage keys visually.

---

## 📚 Documentation

### Architecture

```
┌─────────────────────────────────────────┐
│  GenLayer Smart Contract                │
│  • Needs weather/price/news data        │
│  • No API keys in code                  │
└──────────────┬──────────────────────────┘
               │
               │ "Give me API key for OpenWeatherMap"
               ▼
┌─────────────────────────────────────────┐
│  Key Vault (This Service)               │
│  • Checks contract permissions          │
│  • Verifies rate limits                 │
│  • Decrypts and returns key             │
└──────────────┬──────────────────────────┘
               │
               │ Encrypted API key
               ▼
┌─────────────────────────────────────────┐
│  External API (Weather, Crypto, etc.)   │
│  • Receives authenticated request       │
│  • Returns data to contract             │
└─────────────────────────────────────────┘
```

### Security Model

**Encryption:**
- Keys encrypted using Fernet (symmetric encryption)
- Master key stored securely (environment variable)
- Keys decrypted only when needed

**Access Control:**
- Admin token required for management operations
- Contract signature required for key access
- Optional: whitelist specific contract addresses
- Rate limiting prevents abuse

**Best Practices:**
- Rotate keys regularly
- Use different keys for dev/prod
- Monitor usage statistics
- Set appropriate rate limits

---

## 🔧 API Reference

### Admin Endpoints

#### Initialize Admin Access
```
POST /admin/init
```
Returns admin token. **Call this once** and save the token.

#### Create Key
```
POST /admin/keys
Headers: X-Api-Token: <admin-token>
Body:
{
  "service_name": "openweathermap",
  "api_key": "actual-key-here",
  "description": "Optional description",
  "allowed_contracts": ["0x1234...", "0x5678..."],
  "rate_limit": 100
}
```

#### List Keys
```
GET /admin/keys
Headers: X-Api-Token: <admin-token>
```

#### Update Key
```
PUT /admin/keys/{key_id}
Headers: X-Api-Token: <admin-token>
Body:
{
  "active": true,
  "rate_limit": 200,
  "allowed_contracts": ["0x9abc..."]
}
```

#### Delete Key
```
DELETE /admin/keys/{key_id}
Headers: X-Api-Token: <admin-token>
```

#### Rotate Key
```
POST /admin/keys/{key_id}/rotate
Headers: X-Api-Token: <admin-token>
Body: { "new_api_key": "new-key-value" }
```

#### Usage Statistics
```
GET /admin/usage/{key_id}
Headers: X-Api-Token: <admin-token>
```

### Contract Endpoints

#### Get Key for Contract
```
POST /contract/get-key
Headers:
  X-Contract-Address: <contract-address>
  X-Signature: <contract-signature>
Body:
{
  "contract_address": "0x1234...",
  "service_name": "openweathermap"
}
```

Returns decrypted API key if authorized.

### Health Check
```
GET /health
```
Returns vault status and statistics.

---

## 💡 Use Cases

### 1. Weather Insurance

```python
class WeatherInsurance(gl.Contract):
    def __init__(self, vault_url: str):
        self.vault_url = vault_url
    
    @gl.public.write
    def process_claim(self, policy_id: str) -> str:
        # Get weather API key from vault
        api_key = self._get_key_from_vault("openweathermap")
        
        # Fetch weather data
        weather = self._fetch_weather(api_key, policy.location)
        
        # Process claim based on actual weather
        if self._matches_trigger(weather, policy.trigger):
            self._payout(policy)
```

### 2. Price Oracle

```python
class PriceOracle(gl.Contract):
    @gl.public.write
    def update_price(self, token: str) -> int:
        # Get CoinGecko API key
        api_key = self._get_key_from_vault("coingecko")
        
        # Fetch price
        price = self._fetch_price(api_key, token)
        
        # Store on-chain
        self.prices[token] = price
        return price
```

### 3. News Sentiment Analyzer

```python
class NewsOracle(gl.Contract):
    @gl.public.write
    def analyze_sentiment(self, topic: str) -> str:
        # Get NewsAPI key
        api_key = self._get_key_from_vault("newsapi")
        
        # Fetch headlines
        headlines = self._fetch_news(api_key, topic)
        
        # AI analyzes sentiment
        sentiment = self._analyze(headlines)
        return sentiment
```

---

## 🔐 Security Best Practices

### For Developers

**DO:**
✅ Rotate keys regularly (monthly recommended)  
✅ Use different keys for development and production  
✅ Set conservative rate limits initially  
✅ Monitor usage statistics  
✅ Restrict keys to specific contracts when possible  
✅ Store admin token securely (password manager)  

**DON'T:**
❌ Commit admin tokens to git  
❌ Share admin tokens  
❌ Use production keys in development  
❌ Set unlimited rate limits  
❌ Ignore usage spikes  

### For Production

1. **Environment Variables**
   ```bash
   export VAULT_MASTER_KEY="secure-key-here"
   export ADMIN_TOKEN="secure-token-here"
   ```

2. **HTTPS Only**
   - Use TLS for all vault communication
   - Never send keys over HTTP

3. **Database Backend**
   - Replace in-memory storage with PostgreSQL/MongoDB
   - Implement backup/restore procedures

4. **Monitoring**
   - Set up alerts for rate limit violations
   - Monitor for unusual access patterns
   - Log all key access attempts

---

## 🛠️ Development Setup

### Backend

```bash
# Install dependencies
pip install fastapi uvicorn cryptography pydantic

# Set environment variables
export VAULT_MASTER_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Run server
python keyvault_backend.py
```

### Frontend Dashboard

```bash
# No build step needed - just open in browser
open keyvault_dashboard.html
```

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Initialize
curl -X POST http://localhost:8000/admin/init

# Create test key
curl -X POST http://localhost:8000/admin/keys \
  -H "X-Api-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "test",
    "api_key": "test-key-123",
    "rate_limit": 10
  }'
```

---

## 🚢 Deployment

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY keyvault_backend.py .

ENV VAULT_MASTER_KEY=""

CMD ["python", "keyvault_backend.py"]
```

```bash
docker build -t genlayer-keyvault .
docker run -p 8000:8000 -e VAULT_MASTER_KEY="..." genlayer-keyvault
```

### Production Checklist

- [ ] Set up HTTPS/TLS
- [ ] Configure secure master key
- [ ] Set up database backend (PostgreSQL recommended)
- [ ] Implement backup strategy
- [ ] Configure monitoring and alerts
- [ ] Set up rate limiting at reverse proxy level
- [ ] Document admin token recovery process
- [ ] Test key rotation procedure
- [ ] Set up automated backups
- [ ] Configure CORS for specific domains only

---

## 📈 Roadmap

**v1.0** (Current)
- ✅ Basic key storage and retrieval
- ✅ Permission management
- ✅ Rate limiting
- ✅ Admin dashboard
- ✅ JavaScript SDK

**v1.1** (Planned)
- [ ] Database backend (PostgreSQL)
- [ ] Key versioning
- [ ] Audit logs
- [ ] Webhook notifications
- [ ] Advanced analytics

**v2.0** (Future)
- [ ] Multi-tenant support
- [ ] Key sharing between contracts
- [ ] Automated key rotation
- [ ] Integration with hardware security modules
- [ ] CLI tool

---

## 🤝 Contributing

Contributions welcome! Areas to improve:

- Additional SDK languages (Python, Go, Rust)
- Database backend implementations
- Enhanced security features
- More contract examples
- Performance optimizations

---

## 📄 License

MIT License - feel free to use in your projects!

---

## 🆘 Support

**Found a bug?** Open an issue on GitHub  
**Need help?** Check the examples or ask in GenLayer Discord  
**Have an idea?** Submit a feature request  

---

## 🎓 Learn More

- [GenLayer Documentation](https://docs.genlayer.com)
- [Smart Contract Best Practices](https://consensys.github.io/smart-contract-best-practices/)
- [API Security Guidelines](https://owasp.org/www-project-api-security/)

---

**Built with ❤️ for the GenLayer ecosystem**

Stop hardcoding API keys. Start using GenLayer Key Vault. 🔐
