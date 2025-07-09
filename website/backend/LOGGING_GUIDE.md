# ELANORA Logging System Guide

## Quick Start

### Method 1: Auto-Detection (Recommended)
Just import and use - the logger will automatically detect your module name:

```python
from core.centralized_logging import get_logger

logger = get_logger()  # Auto-detects module name
logger.info("This works in any file!")
```

### Method 2: Directory-Wide Logging
Use one logger for all files in a directory:

```python
from core.centralized_logging import get_directory_logger

# All files in 'api' directory can use this same logger
api_logger = get_directory_logger("api")
api_logger.info("Shared logger for entire directory")
```

## How to Run Examples

### Option 1: Using the helper script (Easiest)
```powershell
cd C:\Users\Laffineur\Documents\GitHub\ELANORA\website\backend
python run_logging_examples.py
```

### Option 2: As a Python module
```powershell
cd C:\Users\Laffineur\Documents\GitHub\ELANORA\website\backend
python -m app.examples.logging_examples
```

### Option 3: Direct execution
```powershell
cd C:\Users\Laffineur\Documents\GitHub\ELANORA\website\backend
python app/examples/logging_examples.py
```

## Log File Organization

Your logs are automatically organized by module:

```
app/logs/
├── api/
│   └── api.log                  # Directory-wide API logs
├── core/
│   └── centralized_logging.log # Core module logs
├── examples/
│   └── custom.log              # Custom logger example
├── exceptions/
│   ├── validation.log          # Validation errors
│   ├── rate_limit.log          # Rate limit violations
│   └── general.log             # Unexpected errors
└── main.log                    # Main application logs
```

## Environment Configuration

Add these to your `.env` file:

```bash
# Logging Configuration
LOG_LEVEL=DEBUG                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
CONSOLE_LOG_LEVEL=INFO         # Separate level for console output
ROOT_LOG_LEVEL=WARNING         # Third-party library noise control
EXCEPTION_LOG_LEVEL=WARNING    # Exception handler log level
EXCEPTION_LOG_DIR=app/logs/exceptions
LOG_DIR=app/logs
APP_NAME=elanora
```

## Usage in Your FastAPI Files

### In any API file:
```python
# api/auth.py
from core.centralized_logging import get_logger

logger = get_logger()  # Becomes "elanora.api.auth"

async def login(user_data):
    logger.info("User login attempt", extra={
        "user_email": user_data.email,
        "ip_address": "192.168.1.100"
    })
    
    try:
        # Authentication logic
        logger.info("Login successful")
    except Exception as e:
        logger.error("Login failed", exc_info=True)
```

### In your main FastAPI app:
```python
# main.py
from core.centralized_logging import get_logger
from core.logging import setup_application_logging

# Setup logging FIRST
setup_application_logging()

logger = get_logger()  # Becomes "elanora.main"

app = FastAPI()

@app.on_event("startup")
async def startup():
    logger.info("Application starting up")
```

## Integration with Exception Handlers

The exception handlers are already configured to use structured logging:

```python
# In your main.py
from core.exception_handler import (
    validation_exception_handler,
    rate_limit_exception_handler,
    add_general_exception_handler
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(Exception, add_general_exception_handler())
```

## Structured Logging

Use the `extra` parameter for structured data:

```python
logger.info(
    "User action performed",
    extra={
        "user_id": "12345",
        "action": "login",
        "ip_address": "192.168.1.100",
        "success": True,
        "processing_time": 0.345
    }
)
```

## Log Output Format

Each log entry includes:
- Timestamp
- Logger name (auto-detected module)
- Log level
- Function and line number
- Message
- Extra structured data (when provided)

Example:
```
2025-07-08 17:39:15 | elanora.api.auth | INFO | auth.login:25 | User login successful
```

## Troubleshooting

### ModuleNotFoundError: No module named 'core'

**Solution**: Always run from the backend directory:
```powershell
cd C:\Users\Laffineur\Documents\GitHub\ELANORA\website\backend
```

### Logs not appearing

1. Check your LOG_LEVEL environment variable
2. Ensure you're calling `setup_application_logging()` once at startup
3. Verify the log directory exists and is writable

### Import issues

Use the helper script `run_logging_examples.py` which handles all path setup automatically.

## Best Practices

1. **Call `setup_application_logging()` once** at application startup
2. **Use auto-detection** - just import `get_logger()` and use it
3. **Use structured logging** with the `extra` parameter for important data
4. **Set appropriate log levels** per environment (DEBUG for dev, INFO/WARNING for prod)
5. **Use correlation IDs** for request tracing (automatic in exception handlers)

That's it! Your logging system is now production-ready with automatic organization, structured data, and minimal configuration required.
