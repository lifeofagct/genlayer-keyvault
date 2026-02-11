/**
 * GenLayer Key Vault SDK
 * ======================
 * 
 * JavaScript SDK for interacting with GenLayer Key Vault.
 * 
 * Installation:
 *   npm install genlayer-keyvault
 * 
 * Usage:
 *   import { KeyVaultClient } from 'genlayer-keyvault';
 *   const vault = new KeyVaultClient('https://vault.example.com', 'your-api-token');
 */

class KeyVaultClient {
  /**
   * Initialize Key Vault client
   * 
   * @param {string} vaultUrl - Base URL of the vault service
   * @param {string} apiToken - Admin API token (for admin operations)
   */
  constructor(vaultUrl, apiToken = null) {
    this.vaultUrl = vaultUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiToken = apiToken;
  }

  /**
   * Make authenticated request to vault
   */
  async _request(method, endpoint, data = null, adminOnly = false) {
    const url = `${this.vaultUrl}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json'
    };

    if (adminOnly && this.apiToken) {
      headers['X-Api-Token'] = this.apiToken;
    }

    const options = {
      method,
      headers
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    return await response.json();
  }

  // ========================================
  // Admin Methods
  // ========================================

  /**
   * Initialize admin access (call this once to get API token)
   */
  async initializeAdmin() {
    const result = await this._request('POST', '/admin/init');
    this.apiToken = result.admin_token;
    return result;
  }

  /**
   * Create a new API key
   * 
   * @param {Object} keyData - Key configuration
   * @param {string} keyData.service_name - Service name (e.g., "openweathermap")
   * @param {string} keyData.api_key - The actual API key to store
   * @param {string} keyData.description - Optional description
   * @param {string[]} keyData.allowed_contracts - Contract addresses allowed to use this key
   * @param {number} keyData.rate_limit - Requests per hour (default: 100)
   * @returns {Promise<Object>} Created key info
   */
  async createKey({ service_name, api_key, description = '', allowed_contracts = [], rate_limit = 100 }) {
    return await this._request('POST', '/admin/keys', {
      service_name,
      api_key,
      description,
      allowed_contracts,
      rate_limit
    }, true);
  }

  /**
   * List all stored keys
   */
  async listKeys() {
    return await this._request('GET', '/admin/keys', null, true);
  }

  /**
   * Update key configuration
   * 
   * @param {string} keyId - Key ID to update
   * @param {Object} updates - Fields to update
   */
  async updateKey(keyId, updates) {
    return await this._request('PUT', `/admin/keys/${keyId}`, updates, true);
  }

  /**
   * Delete a key
   * 
   * @param {string} keyId - Key ID to delete
   */
  async deleteKey(keyId) {
    return await this._request('DELETE', `/admin/keys/${keyId}`, null, true);
  }

  /**
   * Rotate an API key
   * 
   * @param {string} keyId - Key ID to rotate
   * @param {string} newApiKey - New API key value
   */
  async rotateKey(keyId, newApiKey) {
    return await this._request('POST', `/admin/keys/${keyId}/rotate`, { new_api_key: newApiKey }, true);
  }

  /**
   * Get usage statistics for a key
   * 
   * @param {string} keyId - Key ID
   */
  async getUsageStats(keyId) {
    return await this._request('GET', `/admin/usage/${keyId}`, null, true);
  }

  /**
   * Export vault state (for backup)
   */
  async exportVault() {
    return await this._request('GET', '/admin/export', null, true);
  }

  /**
   * Import vault state (from backup)
   * 
   * @param {Object} vaultData - Exported vault data
   */
  async importVault(vaultData) {
    return await this._request('POST', '/admin/import', vaultData, true);
  }

  // ========================================
  // Contract Methods
  // ========================================

  /**
   * Get API key for a contract (used by contracts)
   * 
   * @param {string} contractAddress - Contract address
   * @param {string} signature - Contract signature
   * @param {string} serviceName - Service name
   */
  async getKeyForContract(contractAddress, signature, serviceName) {
    const headers = {
      'X-Contract-Address': contractAddress,
      'X-Signature': signature
    };

    const response = await fetch(`${this.vaultUrl}/contract/get-key`, {
      method: 'POST',
      headers: {
        ...headers,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        contract_address: contractAddress,
        service_name: serviceName
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    return await response.json();
  }

  // ========================================
  // Utility Methods
  // ========================================

  /**
   * Health check
   */
  async healthCheck() {
    return await this._request('GET', '/health');
  }
}

// ========================================
// Helper Functions
// ========================================

/**
 * Quick setup helper for admin
 */
async function setupVault(vaultUrl) {
  const client = new KeyVaultClient(vaultUrl);
  const result = await client.initializeAdmin();
  
  console.log('✅ Vault initialized!');
  console.log('🔑 Admin Token:', result.admin_token);
  console.log('⚠️  Save this token securely!');
  
  return client;
}

/**
 * Example: Create a key
 */
async function exampleCreateKey() {
  const vault = new KeyVaultClient('http://localhost:8000', 'your-admin-token');
  
  const result = await vault.createKey({
    service_name: 'openweathermap',
    api_key: 'your-actual-api-key-here',
    description: 'Weather API key for insurance contracts',
    allowed_contracts: [
      '0x1234...', // Only these contracts can use this key
      '0x5678...'
    ],
    rate_limit: 100 // 100 requests per hour
  });
  
  console.log('Key created:', result.key_id);
}

/**
 * Example: List keys
 */
async function exampleListKeys() {
  const vault = new KeyVaultClient('http://localhost:8000', 'your-admin-token');
  
  const { keys } = await vault.listKeys();
  
  keys.forEach(key => {
    console.log(`📦 ${key.service_name} (${key.key_id})`);
    console.log(`   Calls: ${key.total_calls}`);
    console.log(`   Active: ${key.active}`);
    console.log(`   Rate Limit: ${key.rate_limit}/hour`);
  });
}

/**
 * Example: Get usage stats
 */
async function exampleUsageStats() {
  const vault = new KeyVaultClient('http://localhost:8000', 'your-admin-token');
  
  const stats = await vault.getUsageStats('key-id-here');
  
  console.log('Usage Statistics:');
  console.log(`Total calls: ${stats.total_calls}`);
  console.log(`Last hour: ${stats.calls_last_hour}`);
  console.log(`Rate limit hits: ${stats.rate_limit_hits}`);
}

/**
 * Example: Rotate key
 */
async function exampleRotateKey() {
  const vault = new KeyVaultClient('http://localhost:8000', 'your-admin-token');
  
  await vault.rotateKey('key-id-here', 'new-api-key-value');
  
  console.log('✅ Key rotated successfully');
  console.log('Old key is no longer valid');
  console.log('All future calls will use new key');
}

// ========================================
// Export
// ========================================

// For Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    KeyVaultClient,
    setupVault,
    exampleCreateKey,
    exampleListKeys,
    exampleUsageStats,
    exampleRotateKey
  };
}

// For browsers/ES modules
if (typeof window !== 'undefined') {
  window.KeyVaultClient = KeyVaultClient;
  window.setupVault = setupVault;
}