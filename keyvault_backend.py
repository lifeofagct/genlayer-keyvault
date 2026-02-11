"""
GenLayer API Key Vault - Backend Service
=========================================

Secure API key management for GenLayer smart contracts.

Features:
- Encrypted key storage
- Contract-level permissions
- Key rotation
- Usage tracking
- Rate limiting
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet
from typing import Optional, List, Dict
import hashlib
import secrets
import time
import json
import os

# Initialize FastAPI
app = FastAPI(
    title="GenLayer Key Vault",
    description="Secure API key management for GenLayer contracts",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Encryption setup
MASTER_KEY = os.getenv("VAULT_MASTER_KEY", Fernet.generate_key())
cipher_suite = Fernet(MASTER_KEY)

# In-memory storage (in production: use PostgreSQL/MongoDB)
vault_storage = {
    "keys": {},          # key_id -> encrypted key data
    "contracts": {},     # contract_address -> permissions
    "usage": {},         # key_id -> usage stats
    "api_tokens": {}     # api_token -> admin data
}

# Models
class CreateKeyRequest(BaseModel):
    service_name: str
    api_key: str
    description: Optional[str] = ""
    allowed_contracts: List[str] = []
    rate_limit: int = 100  # requests per hour

class UpdateKeyRequest(BaseModel):
    api_key: Optional[str] = None
    allowed_contracts: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    active: Optional[bool] = None

class ContractKeyRequest(BaseModel):
    contract_address: str
    service_name: str

class UsageStats(BaseModel):
    total_calls: int
    last_used: float
    rate_limit_hits: int
    active: bool

# Authentication
def verify_admin_token(x_api_token: str = Header(...)):
    """Verify admin API token"""
    if x_api_token not in vault_storage["api_tokens"]:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return vault_storage["api_tokens"][x_api_token]

def verify_contract_signature(x_contract_address: str = Header(...),
                              x_signature: str = Header(...)):
    """Verify contract signature (simplified for demo)"""
    # In production: verify actual cryptographic signature
    if not x_contract_address or not x_signature:
        raise HTTPException(status_code=401, detail="Missing authentication")
    return x_contract_address

# Helper functions
def encrypt_key(api_key: str) -> str:
    """Encrypt API key"""
    return cipher_suite.encrypt(api_key.encode()).decode()

def decrypt_key(encrypted_key: str) -> str:
    """Decrypt API key"""
    return cipher_suite.decrypt(encrypted_key.encode()).decode()

def generate_key_id(service_name: str) -> str:
    """Generate unique key ID"""
    timestamp = str(time.time())
    random_part = secrets.token_hex(8)
    return hashlib.sha256(f"{service_name}{timestamp}{random_part}".encode()).hexdigest()[:16]

def check_rate_limit(key_id: str, rate_limit: int) -> bool:
    """Check if rate limit is exceeded"""
    if key_id not in vault_storage["usage"]:
        vault_storage["usage"][key_id] = {
            "calls": [],
            "total_calls": 0,
            "last_used": 0,
            "rate_limit_hits": 0
        }
    
    usage = vault_storage["usage"][key_id]
    now = time.time()
    one_hour_ago = now - 3600
    
    # Remove old calls
    usage["calls"] = [t for t in usage["calls"] if t > one_hour_ago]
    
    # Check limit
    if len(usage["calls"]) >= rate_limit:
        usage["rate_limit_hits"] += 1
        return False
    
    # Record call
    usage["calls"].append(now)
    usage["total_calls"] += 1
    usage["last_used"] = now
    
    return True

# Admin Endpoints
@app.post("/admin/init")
def initialize_admin():
    """Initialize admin access (call this once)"""
    admin_token = secrets.token_urlsafe(32)
    vault_storage["api_tokens"][admin_token] = {
        "role": "admin",
        "created_at": time.time()
    }
    return {
        "admin_token": admin_token,
        "message": "Save this token securely! You'll need it for all admin operations."
    }

@app.post("/admin/keys", dependencies=[Depends(verify_admin_token)])
def create_key(request: CreateKeyRequest):
    """Create and store encrypted API key"""
    
    # Generate unique ID
    key_id = generate_key_id(request.service_name)
    
    # Encrypt the API key
    encrypted_key = encrypt_key(request.api_key)
    
    # Store key data
    vault_storage["keys"][key_id] = {
        "key_id": key_id,
        "service_name": request.service_name,
        "encrypted_key": encrypted_key,
        "description": request.description,
        "allowed_contracts": request.allowed_contracts,
        "rate_limit": request.rate_limit,
        "created_at": time.time(),
        "active": True
    }
    
    # Initialize usage tracking
    vault_storage["usage"][key_id] = {
        "calls": [],
        "total_calls": 0,
        "last_used": 0,
        "rate_limit_hits": 0
    }
    
    return {
        "key_id": key_id,
        "service_name": request.service_name,
        "message": "API key stored securely"
    }

@app.get("/admin/keys", dependencies=[Depends(verify_admin_token)])
def list_keys():
    """List all stored keys (without revealing actual keys)"""
    keys = []
    for key_id, data in vault_storage["keys"].items():
        usage = vault_storage["usage"].get(key_id, {})
        keys.append({
            "key_id": key_id,
            "service_name": data["service_name"],
            "description": data["description"],
            "allowed_contracts": data["allowed_contracts"],
            "rate_limit": data["rate_limit"],
            "active": data["active"],
            "created_at": data["created_at"],
            "total_calls": usage.get("total_calls", 0),
            "last_used": usage.get("last_used", 0)
        })
    return {"keys": keys}

@app.put("/admin/keys/{key_id}", dependencies=[Depends(verify_admin_token)])
def update_key(key_id: str, request: UpdateKeyRequest):
    """Update key configuration"""
    if key_id not in vault_storage["keys"]:
        raise HTTPException(status_code=404, detail="Key not found")
    
    key_data = vault_storage["keys"][key_id]
    
    # Update fields
    if request.api_key is not None:
        key_data["encrypted_key"] = encrypt_key(request.api_key)
    
    if request.allowed_contracts is not None:
        key_data["allowed_contracts"] = request.allowed_contracts
    
    if request.rate_limit is not None:
        key_data["rate_limit"] = request.rate_limit
    
    if request.active is not None:
        key_data["active"] = request.active
    
    key_data["updated_at"] = time.time()
    
    return {
        "key_id": key_id,
        "message": "Key updated successfully"
    }

@app.delete("/admin/keys/{key_id}", dependencies=[Depends(verify_admin_token)])
def delete_key(key_id: str):
    """Delete a key"""
    if key_id not in vault_storage["keys"]:
        raise HTTPException(status_code=404, detail="Key not found")
    
    del vault_storage["keys"][key_id]
    if key_id in vault_storage["usage"]:
        del vault_storage["usage"][key_id]
    
    return {"message": "Key deleted successfully"}

@app.post("/admin/keys/{key_id}/rotate", dependencies=[Depends(verify_admin_token)])
def rotate_key(key_id: str, new_api_key: str):
    """Rotate API key"""
    if key_id not in vault_storage["keys"]:
        raise HTTPException(status_code=404, detail="Key not found")
    
    key_data = vault_storage["keys"][key_id]
    old_key = decrypt_key(key_data["encrypted_key"])
    
    # Update to new key
    key_data["encrypted_key"] = encrypt_key(new_api_key)
    key_data["rotated_at"] = time.time()
    
    return {
        "key_id": key_id,
        "message": "Key rotated successfully",
        "old_key_preview": old_key[:8] + "..." if len(old_key) > 8 else "***"
    }

@app.get("/admin/usage/{key_id}", dependencies=[Depends(verify_admin_token)])
def get_usage_stats(key_id: str):
    """Get detailed usage statistics for a key"""
    if key_id not in vault_storage["keys"]:
        raise HTTPException(status_code=404, detail="Key not found")
    
    usage = vault_storage["usage"].get(key_id, {
        "calls": [],
        "total_calls": 0,
        "last_used": 0,
        "rate_limit_hits": 0
    })
    
    # Calculate hourly stats
    now = time.time()
    one_hour_ago = now - 3600
    recent_calls = [t for t in usage.get("calls", []) if t > one_hour_ago]
    
    return {
        "key_id": key_id,
        "total_calls": usage.get("total_calls", 0),
        "calls_last_hour": len(recent_calls),
        "last_used": usage.get("last_used", 0),
        "rate_limit_hits": usage.get("rate_limit_hits", 0),
        "active": vault_storage["keys"][key_id]["active"]
    }

# Contract Endpoints (used by GenLayer contracts)
@app.post("/contract/get-key")
def get_key_for_contract(
    request: ContractKeyRequest,
    contract_address: str = Depends(verify_contract_signature)
):
    """Get decrypted API key for authorized contract"""
    
    # Find key by service name
    matching_keys = [
        (key_id, data) for key_id, data in vault_storage["keys"].items()
        if data["service_name"] == request.service_name and data["active"]
    ]
    
    if not matching_keys:
        raise HTTPException(status_code=404, detail="No active key found for this service")
    
    key_id, key_data = matching_keys[0]
    
    # Check permissions
    if key_data["allowed_contracts"]:
        if contract_address not in key_data["allowed_contracts"]:
            raise HTTPException(
                status_code=403, 
                detail="Contract not authorized to use this key"
            )
    
    # Check rate limit
    if not check_rate_limit(key_id, key_data["rate_limit"]):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({key_data['rate_limit']} requests/hour)"
        )
    
    # Decrypt and return key
    api_key = decrypt_key(key_data["encrypted_key"])
    
    return {
        "api_key": api_key,
        "service_name": request.service_name,
        "rate_limit": key_data["rate_limit"],
        "calls_remaining": key_data["rate_limit"] - len(vault_storage["usage"][key_id]["calls"])
    }

# Health check
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "total_keys": len(vault_storage["keys"]),
        "active_keys": len([k for k in vault_storage["keys"].values() if k["active"]])
    }

# Export vault state (for backups)
@app.get("/admin/export", dependencies=[Depends(verify_admin_token)])
def export_vault():
    """Export encrypted vault state"""
    return {
        "keys": vault_storage["keys"],
        "usage": vault_storage["usage"],
        "exported_at": time.time()
    }

# Import vault state (for restores)
@app.post("/admin/import", dependencies=[Depends(verify_admin_token)])
def import_vault(data: dict):
    """Import vault state from backup"""
    vault_storage["keys"] = data.get("keys", {})
    vault_storage["usage"] = data.get("usage", {})
    
    return {
        "message": "Vault imported successfully",
        "keys_imported": len(vault_storage["keys"])
    }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("GenLayer API Key Vault")
    print("=" * 50)
    print("\nStarting server...")
    print("API Docs: http://localhost:8000/docs")
    print("\n⚠️  First, initialize admin access:")
    print("   POST http://localhost:8000/admin/init")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)