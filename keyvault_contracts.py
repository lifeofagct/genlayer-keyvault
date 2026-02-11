# { "Depends": "py-genlayer:test" }
"""
GenLayer Key Vault Integration Example
========================================

Shows how contracts use the Key Vault to access API keys securely.
"""

from genlayer import *


class KeyVaultClient(gl.Contract):
    """
    Example contract showing Key Vault integration.
    
    This contract fetches API keys from the vault and uses them
    to make authenticated API calls.
    """
    
    def __init__(self, vault_url: str):
        self.vault_url = vault_url  # e.g., "https://keyvault.example.com"
        self.contract_address = ""  # Set after deployment
        self.last_response = ""
    
    def _get_api_key(self, service_name: str) -> str:
        """
        Fetch API key from vault.
        
        In production, this would make an HTTP request to the vault.
        For demo, we'll use AI to simulate the vault response.
        """
        
        # Generate contract signature (simplified for demo)
        # In production: use proper cryptographic signature
        signature = f"contract_sig_{self.contract_address}"
        
        # Request key from vault
        vault_request = f"""Make a POST request to {self.vault_url}/contract/get-key

Headers:
- X-Contract-Address: {self.contract_address}
- X-Signature: {signature}

Body:
{{
  "contract_address": "{self.contract_address}",
  "service_name": "{service_name}"
}}

Return only the API key from the response (the "api_key" field).
If the request fails, return "ERROR: [reason]"."""
        
        def fetch_key():
            return gl.exec_prompt(vault_request).strip()
        
        api_key = gl.eq_principle_leader_mode(fetch_key)
        
        if api_key.startswith("ERROR:"):
            raise Exception(f"Failed to get API key: {api_key}")
        
        return api_key
    
    @gl.public.write
    def fetch_weather_secure(self, city: str) -> str:
        """
        Fetch weather data using API key from vault.
        
        This demonstrates secure API usage:
        1. Get API key from vault (encrypted, permission-checked)
        2. Use key to make API call
        3. Key never exposed in contract code
        """
        
        # Get OpenWeatherMap API key from vault
        try:
            api_key = self._get_api_key("openweathermap")
        except Exception as e:
            return f"Failed to access API key: {str(e)}"
        
        # Use the key to fetch weather
        weather_prompt = f"""Fetch current weather for {city} from OpenWeatherMap API.

Use this API key: {api_key}

Return format:
Temperature: [temp]°C
Conditions: [description]
Humidity: [percent]%

If the API call fails, return "ERROR: [reason]"."""
        
        def fetch_weather():
            return gl.exec_prompt(weather_prompt).strip()
        
        weather_data = gl.eq_principle_strict_eq(fetch_weather)
        
        self.last_response = weather_data
        return weather_data
    
    @gl.public.write
    def fetch_crypto_price_secure(self, token: str) -> str:
        """
        Fetch cryptocurrency price using API key from vault.
        
        Demonstrates using different API keys for different services.
        """
        
        # Get CoinGecko API key from vault
        try:
            api_key = self._get_api_key("coingecko")
        except Exception as e:
            return f"Failed to access API key: {str(e)}"
        
        # Use the key to fetch price
        price_prompt = f"""Fetch current {token} price from CoinGecko API.

Use this API key: {api_key}

Return format:
Token: {token}
Price (USD): $[price]
24h Change: [percentage]%

If the API call fails, return "ERROR: [reason]"."""
        
        def fetch_price():
            return gl.exec_prompt(price_prompt).strip()
        
        price_data = gl.eq_principle_strict_eq(fetch_price)
        
        self.last_response = price_data
        return price_data
    
    @gl.public.view
    def get_last_response(self) -> str:
        """Get the last API response"""
        return self.last_response if self.last_response else "No API calls made yet"


# ============================================================================
# EXAMPLE: Weather Insurance with Key Vault
# ============================================================================

class WeatherInsuranceWithVault(gl.Contract):
    """
    Weather insurance that uses Key Vault for secure API access.
    
    This shows a real-world use case: insurance contract that needs
    to fetch weather data without exposing API keys.
    """
    
    def __init__(self, vault_url: str):
        self.vault_url = vault_url
        self.contract_address = ""
        self.policies = {}
        self.policy_counter = 0
    
    def _get_weather_api_key(self) -> str:
        """Get weather API key from vault"""
        vault_request = f"""Request API key from vault at {self.vault_url}

Service: openweathermap
Contract: {self.contract_address}

Return only the API key."""
        
        def fetch():
            return gl.exec_prompt(vault_request).strip()
        
        return gl.eq_principle_leader_mode(fetch)
    
    @gl.public.write
    def create_policy(self, location: str, coverage: int, trigger: str) -> str:
        """Create weather insurance policy"""
        self.policy_counter += 1
        policy_id = f"POL-{self.policy_counter}"
        
        self.policies[policy_id] = {
            "owner": gl.message_sender_address,
            "location": location,
            "coverage": coverage,
            "trigger": trigger,  # e.g., "rain", "snow", "temperature below 10C"
            "active": True,
            "claimed": False
        }
        
        return policy_id
    
    @gl.public.write
    def check_weather_and_process_claim(self, policy_id: str) -> str:
        """
        Check weather conditions and process insurance claim.
        
        Uses Key Vault to securely access weather API.
        """
        
        if policy_id not in self.policies:
            return "ERROR: Policy not found"
        
        policy = self.policies[policy_id]
        
        if not policy["active"]:
            return "ERROR: Policy not active"
        
        if policy["claimed"]:
            return "ERROR: Claim already processed"
        
        # Get API key from vault
        try:
            api_key = self._get_weather_api_key()
        except Exception as e:
            return f"ERROR: Could not access weather API key - {str(e)}"
        
        # Fetch current weather
        weather_prompt = f"""Fetch current weather for {policy['location']} using API key {api_key}.

Check if conditions match: {policy['trigger']}

Return format:
WEATHER: [current conditions]
MATCH: YES or NO
REASON: [why it matches or doesn't]"""
        
        def check():
            return gl.exec_prompt(weather_prompt).strip()
        
        weather_check = gl.eq_principle_strict_eq(check)
        
        # Process claim
        if "MATCH: YES" in weather_check:
            policy["claimed"] = True
            policy["active"] = False
            policy["payout"] = policy["coverage"]
            
            return f"""✅ CLAIM APPROVED

Policy: {policy_id}
Location: {policy['location']}
Trigger: {policy['trigger']}
Payout: {policy['coverage']} tokens

Weather Check:
{weather_check}

Insurance has been paid out."""
        else:
            return f"""❌ CLAIM DENIED

Policy: {policy_id}
Location: {policy['location']}
Trigger: {policy['trigger']}

Weather Check:
{weather_check}

Conditions do not match policy trigger."""
    
    @gl.public.view
    def get_policy(self, policy_id: str) -> str:
        """View policy details"""
        if policy_id not in self.policies:
            return "Policy not found"
        
        policy = self.policies[policy_id]
        
        return f"""
Policy: {policy_id}
Owner: {policy['owner']}
Location: {policy['location']}
Coverage: {policy['coverage']} tokens
Trigger: {policy['trigger']}
Status: {'Claimed' if policy['claimed'] else 'Active' if policy['active'] else 'Inactive'}
Payout: {policy.get('payout', 0)} tokens
"""


# ============================================================================
# EXAMPLE: Simple Demo Contract
# ============================================================================

class SimpleKeyVaultDemo(gl.Contract):
    """
    Simplest possible example of using Key Vault.
    
    Perfect for learning and testing.
    """
    
    def __init__(self):
        self.vault_url = "https://keyvault.example.com"
        self.last_key_used = ""
    
    @gl.public.write
    def test_get_key(self, service_name: str) -> str:
        """
        Test fetching a key from the vault.
        
        Args:
            service_name: Name of service (e.g., "openweathermap")
            
        Returns:
            Success message or error
        """
        
        # In a real implementation, this would make an HTTP request
        # For demo, we simulate the vault response
        
        request = f"""Simulate getting API key for service: {service_name}

Vault URL: {self.vault_url}
Contract: {gl.message_sender_address}

Return a demo API key in format: sk_demo_[random]"""
        
        def get_key():
            return gl.exec_prompt(request).strip()
        
        api_key = gl.eq_principle_leader_mode(get_key)
        
        # Store for verification (in real app, don't store keys!)
        self.last_key_used = f"{service_name[:10]}..."
        
        return f"""✅ Successfully retrieved API key!

Service: {service_name}
Key Preview: {api_key[:15]}...
Vault: {self.vault_url}

The full key would be used to make API calls.
(In this demo, we don't expose the full key for security)"""
    
    @gl.public.view
    def get_vault_info(self) -> str:
        """Get info about the vault connection"""
        return f"""
GenLayer Key Vault Integration

Vault URL: {self.vault_url}
Last Service Used: {self.last_key_used if self.last_key_used else 'None'}

How it works:
1. Contract requests API key from vault
2. Vault checks permissions and rate limits
3. Vault returns decrypted key
4. Contract uses key for API call
5. Key never stored in contract

Security benefits:
✓ Keys encrypted at rest
✓ Permission-based access
✓ Rate limiting
✓ Key rotation support
✓ Usage tracking
✓ No keys in contract code
"""