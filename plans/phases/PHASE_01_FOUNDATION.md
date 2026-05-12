# Phase 1: Foundation - Scraping Infrastructure
> Duration: Week 1
> Priority: CRITICAL
> Dependencies: None
> Research Basis: Web scraping best practices 2025 (ProxyTee, Scrapeless, ByteTunnels)

---

## Objective
Build production-grade scraping infrastructure with anti-bot detection, proxy rotation, and stealth capabilities.

## Deliverables
1. `backend/collectors/scraping_utils.py` - Core scraping utilities
2. `backend/collectors/proxy_manager.py` - Proxy rotation management
3. `backend/collectors/stealth_session.py` - Stealth browser session
4. `backend/collectors/retry_handler.py` - Intelligent retry logic
5. Updated `backend/requirements.txt` with new dependencies
6. Updated `backend/compliance/tos_registry.py` with new sources

## Implementation

### 1.1 Scraping Utilities (`scraping_utils.py`)

```python
"""
scraping_utils.py - Core scraping utilities for LeadIQ
Based on 2025 anti-bot detection best practices
"""
import asyncio
import random
from typing import Optional, Dict, List
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class StealthConfig:
    """Configuration for stealth scraping"""
    browser: str = "playwright"
    headless: bool = True
    user_agent_rotation: bool = True
    proxy_type: str = "residential"
    proxy_rotation_interval: int = 20
    delay_min: float = 2.0
    delay_max: float = 5.0
    tls_bypass: str = "curl_cffi"
    fingerprint_spoofing: bool = True
    mouse_movement: bool = True
    scroll_simulation: bool = True

@dataclass
class ProxyConfig:
    """Proxy configuration"""
    provider: str = "brightdata"
    username: str = ""
    password: str = ""
    country: str = "IN"
    city: Optional[str] = None
    rotation_interval: int = 20

class ScrapingUtils:
    """Core scraping utilities with anti-detection"""
    
    def __init__(self, config: StealthConfig):
        self.config = config
        self.proxy_manager = ProxyManager(config.proxy_config)
        self.ua_rotator = UserAgentRotator()
        self.tls_manager = TLSFingerprintManager(config.tls_bypass)
        
    async def create_stealth_session(self) -> StealthSession:
        """Create a stealth browsing session"""
        
        # Get fresh proxy
        proxy = await self.proxy_manager.get_proxy()
        
        # Get rotated user agent
        user_agent = self.ua_rotator.get_random()
        
        # Create TLS context with bypass
        tls_context = self.tls_manager.create_context()
        
        session = StealthSession(
            proxy=proxy,
            user_agent=user_agent,
            tls_context=tls_context,
            config=self.config
        )
        
        logger.info("stealth_session_created", 
                   proxy=proxy['ip'],
                   ua=user_agent[:50])
        
        return session
    
    async def random_delay(self):
        """Human-like random delay"""
        delay = random.uniform(self.config.delay_min, self.config.delay_max)
        await asyncio.sleep(delay)
        
    def jitter_delay(self, base_delay: float, jitter_pct: float = 0.3) -> float:
        """Add jitter to delay to avoid patterns"""
        jitter = base_delay * jitter_pct * random.uniform(-1, 1)
        return max(0.5, base_delay + jitter)

class UserAgentRotator:
    """Rotate user agents from real browser signatures"""
    
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]
    
    def get_random(self) -> str:
        return random.choice(self.USER_AGENTS)
    
    def get_for_browser(self, browser: str) -> str:
        """Get UA for specific browser type"""
        browsers = {
            'chrome': [ua for ua in self.USER_AGENTS if 'Chrome' in ua and 'Edg' not in ua],
            'edge': [ua for ua in self.USER_AGENTS if 'Edg' in ua],
            'firefox': [ua for ua in self.USER_AGENTS if 'Firefox' in ua],
            'safari': [ua for ua in self.USER_AGENTS if 'Safari' in ua and 'Chrome' not in ua],
        }
        return random.choice(browsers.get(browser, self.USER_AGENTS))

class TLSFingerprintManager:
    """Manage TLS fingerprint to avoid detection"""
    
    def __init__(self, method: str = "curl_cffi"):
        self.method = method
        
    def create_context(self):
        """Create TLS context with browser-like fingerprint"""
        if self.method == "curl_cffi":
            from curl_cffi import requests
            return requests.Session(impersonate="chrome120")
        elif self.method == "tls_client":
            from tls_client import Session
            return Session(client_identifier="chrome_120")
        else:
            import httpx
            return httpx.AsyncClient()
```

### 1.2 Proxy Manager (`proxy_manager.py`)

```python
"""
proxy_manager.py - Intelligent proxy rotation and management
"""
import asyncio
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class Proxy:
    ip: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    country: str = "IN"
    city: Optional[str] = None
    type: str = "residential"
    last_used: Optional[float] = None
    use_count: int = 0
    success_rate: float = 1.0

class ProxyManager:
    """Manage proxy pool with intelligent rotation"""
    
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.proxy_pool: List[Proxy] = []
        self.current_index = 0
        self.failed_proxies: set = set()
        
    async def initialize_pool(self):
        """Load initial proxy pool"""
        # Load from provider API or file
        self.proxy_pool = await self.load_proxies_from_provider()
        logger.info("proxy_pool_initialized", count=len(self.proxy_pool))
        
    async def get_proxy(self) -> Dict:
        """Get next proxy with rotation logic"""
        
        # Filter out failed proxies
        available = [p for p in self.proxy_pool if p.ip not in self.failed_proxies]
        
        if not available:
            logger.warning("no_proxies_available")
            # Fallback to direct connection
            return None
            
        # Weighted random selection based on success rate
        weights = [p.success_rate for p in available]
        proxy = random.choices(available, weights=weights, k=1)[0]
        
        proxy.last_used = asyncio.get_event_loop().time()
        proxy.use_count += 1
        
        return {
            'ip': proxy.ip,
            'port': proxy.port,
            'username': proxy.username,
            'password': proxy.password,
            'url': f"http://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
        }
        
    async def report_success(self, proxy_ip: str):
        """Report successful use of proxy"""
        for p in self.proxy_pool:
            if p.ip == proxy_ip:
                p.success_rate = min(1.0, p.success_rate + 0.05)
                break
                
    async def report_failure(self, proxy_ip: str, error_type: str):
        """Report failed use of proxy"""
        for p in self.proxy_pool:
            if p.ip == proxy_ip:
                p.success_rate = max(0.1, p.success_rate - 0.2)
                if p.success_rate < 0.3:
                    self.failed_proxies.add(proxy_ip)
                    logger.warning("proxy_marked_failed", ip=proxy_ip, error=error_type)
                break
                
    async def load_proxies_from_provider(self) -> List[Proxy]:
        """Load proxies from provider (BrightData, ScrapingBee, etc.)"""
        # Implementation depends on provider
        # Example for BrightData:
        if self.config.provider == "brightdata":
            return await self.load_brightdata_proxies()
        elif self.config.provider == "scrapingbee":
            return await self.load_scrapingbee_proxies()
        else:
            # Load from environment or file
            return self.load_from_file()
            
    async def load_brightdata_proxies(self) -> List[Proxy]:
        """Load BrightData residential proxies"""
        # BrightData API integration
        proxies = []
        # Generate proxy list from credentials
        for i in range(100):  # Pool of 100 proxies
            proxy = Proxy(
                ip=f"brd.superproxy.io",
                port=22225,
                username=f"brd-customer-{self.config.username}-region-in",
                password=self.config.password,
                country="IN"
            )
            proxies.append(proxy)
        return proxies
```

### 1.3 Stealth Session (`stealth_session.py`)

```python
"""
stealth_session.py - Playwright-based stealth browser session
"""
import asyncio
from playwright.async_api import async_playwright, Page, Browser
from playwright_stealth import stealth_async
import structlog

logger = structlog.get_logger()

class StealthSession:
    """Stealth browsing session with anti-detection"""
    
    def __init__(self, proxy, user_agent, tls_context, config):
        self.proxy = proxy
        self.user_agent = user_agent
        self.tls_context = tls_context
        self.config = config
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def start(self):
        """Launch stealth browser"""
        self.playwright = await async_playwright().start()
        
        browser_args = {
            'headless': self.config.headless,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
            ]
        }
        
        if self.proxy:
            browser_args['proxy'] = {
                'server': self.proxy['url']
            }
            
        self.browser = await self.playwright.chromium.launch(**browser_args)
        
        context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='en-IN',
            timezone_id='Asia/Kolkata',
        )
        
        self.page = await context.new_page()
        
        # Apply stealth plugins
        await stealth_async(self.page)
        
        # Additional evasions
        await self._apply_evasions()
        
        logger.info("stealth_browser_launched", 
                   ua=self.user_agent[:50],
                   proxy=self.proxy['ip'] if self.proxy else "none")
        
    async def _apply_evasions(self):
        """Apply additional anti-detection evasions"""
        
        # Remove webdriver property
        await self.page.evaluate("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Override plugins
        await self.page.evaluate("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Override permissions
        await self.page.evaluate("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
    async def goto(self, url: str, wait_until: str = "networkidle"):
        """Navigate to URL with human-like behavior"""
        
        # Random initial delay
        await asyncio.sleep(random.uniform(1, 3))
        
        response = await self.page.goto(url, wait_until=wait_until)
        
        # Simulate human-like scrolling
        if self.config.scroll_simulation:
            await self._simulate_scrolling()
            
        return response
        
    async def _simulate_scrolling(self):
        """Simulate human-like scrolling"""
        scroll_height = await self.page.evaluate("document.body.scrollHeight")
        viewport_height = await self.page.evaluate("window.innerHeight")
        
        current_position = 0
        while current_position < scroll_height:
            # Random scroll amount
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            
            # Random pause (simulating reading)
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Occasionally scroll back up (like re-reading)
            if random.random() < 0.1:
                await self.page.evaluate(f"window.scrollBy(0, -{random.randint(50, 150)})")
                await asyncio.sleep(random.uniform(0.3, 1.0))
                
    async def intercept_api(self, pattern: str, handler):
        """Intercept API calls matching pattern"""
        
        async def route_handler(route):
            request = route.request
            if pattern in request.url:
                response = await route.fetch()
                body = await response.json()
                await handler(body)
                await route.fulfill(response=response)
            else:
                await route.continue_()
                
        await self.page.route(pattern, route_handler)
        
    async def close(self):
        """Close browser session"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
```

### 1.4 Retry Handler (`retry_handler.py`)

```python
"""
retry_handler.py - Intelligent retry logic with exponential backoff
"""
import asyncio
import random
from functools import wraps
from typing import Callable, TypeVar, Optional
import structlog

logger = structlog.get_logger()

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 5
    base_delay: float = 2.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (
        asyncio.TimeoutError,
        ConnectionError,
        # HTTP errors
    )

class RetryHandler:
    """Handle retries with exponential backoff and jitter"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic"""
        
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                if attempt > 1:
                    logger.info("retry_succeeded", 
                               attempt=attempt,
                               func=func.__name__)
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self._is_retryable(e):
                    raise
                    
                if attempt == self.config.max_attempts:
                    logger.error("max_retries_exceeded",
                                func=func.__name__,
                                error=str(e),
                                attempts=attempt)
                    raise last_exception
                    
                delay = self._calculate_delay(attempt)
                logger.warning("retry_attempt",
                            func=func.__name__,
                            attempt=attempt,
                            max_attempts=self.config.max_attempts,
                            delay=delay,
                            error=str(e))
                
                await asyncio.sleep(delay)
                
    def _is_retryable(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        return isinstance(exception, self.config.retryable_exceptions)
        
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        # Exponential backoff
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter (±30%)
        if self.config.jitter:
            jitter = delay * 0.3 * random.uniform(-1, 1)
            delay = max(0.5, delay + jitter)
            
        return delay

def with_retry(config: RetryConfig = None):
    """Decorator for adding retry logic"""
    handler = RetryHandler(config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await handler.execute(func, *args, **kwargs)
        return wrapper
    return decorator
```

---

## Verification Checkpoints

### Checkpoint 1.1: Proxy Rotation
- [ ] Load proxy pool (minimum 50 proxies)
- [ ] Rotate proxy every 20 requests
- [ ] Handle proxy failures gracefully
- [ ] Success rate > 90%

### Checkpoint 1.2: Stealth Browser
- [ ] Launch Playwright with stealth plugins
- [ ] Pass bot detection tests (bot.sannysoft.com)
- [ ] Navigate Naukri without immediate block
- [ ] Handle JavaScript rendering correctly

### Checkpoint 1.3: Retry Logic
- [ ] Exponential backoff works correctly
- [ ] Jitter prevents pattern detection
- [ ] Max attempts respected
- [ ] Non-retryable exceptions propagated

---

## Testing

```python
# tests/collectors/test_scraping_utils.py
import pytest
from backend.collectors.scraping_utils import ScrapingUtils, StealthConfig

@pytest.mark.asyncio
async def test_stealth_session_creation():
    config = StealthConfig()
    utils = ScrapingUtils(config)
    
    session = await utils.create_stealth_session()
    assert session is not None
    assert session.user_agent is not None
    
@pytest.mark.asyncio
async def test_proxy_rotation():
    # Mock proxy pool
    proxies = [
        {'ip': f'192.168.1.{i}', 'port': 8080}
        for i in range(10)
    ]
    
    manager = ProxyManager(config)
    manager.proxy_pool = proxies
    
    used_proxies = set()
    for _ in range(50):
        proxy = await manager.get_proxy()
        used_proxies.add(proxy['ip'])
    
    # Should have used multiple proxies
    assert len(used_proxies) > 1
    
@pytest.mark.asyncio
async def test_retry_with_backoff():
    call_count = 0
    
    @with_retry(RetryConfig(max_attempts=3, base_delay=0.1))
    async def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Simulated failure")
        return "success"
    
    result = await flaky_function()
    assert result == "success"
    assert call_count == 3
```

---

## Dependencies

```txt
# requirements additions
playwright>=1.40.0
playwright-stealth>=1.0.0
curl_cffi>=0.6.0
fake-useragent>=1.4.0
tenacity>=8.2.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Bot detection pass rate | > 95% | bot.sannysoft.com test |
| Proxy rotation success | > 90% | Proxy manager logs |
| Retry success rate | > 95% | Retry handler logs |
| Session launch time | < 5s | Timer measurement |
| Memory usage | < 500MB | Process monitor |

---

*Phase 1 - Foundation*
*Duration: Week 1*
*Research basis: Anti-bot detection 2025 best practices*
