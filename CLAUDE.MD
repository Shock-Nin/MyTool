# MyTool - Claude Code Documentation

## Project Overview

MyTool is a Python-based integrated toolset for Windows and Mac environments, providing a GUI application for various business operations including:

- **Trading & Analysis**: Anomaly detection, EA (Expert Advisor) testing, predictive modeling (ARIMA, RNN, Keras)
- **Asset Management**: Personal asset tracking, financial data processing
- **Web Automation**: Automated web login, data scraping
- **Platform Utilities**: Display management, alert timers, dictionary tools

## Architecture

### Entry Points

- **mytool.py**: Main GUI application using FreeSimpleGUI
  - Provides menu-driven interface for all tools
  - Supports password-protected login
  - Multi-platform support (Windows/Mac)

- **run.py**: Command-line module executor
  - Dynamic module loading using importlib
  - Converts snake_case module names to PascalCase class names
  - Pattern: `python run.py -m <module> -e <event>`

- **batch.py**: Batch processing executor

### Directory Structure

```
MyTool/
├── business/          # Business logic modules
│   ├── mac/          # Mac-specific features
│   ├── windows/      # Windows-specific features
│   ├── predict/      # ML models (ARIMA, RNN, Keras)
│   ├── batch/        # Batch processing
│   └── multiple/     # Cross-platform features
├── common/           # Shared utilities
│   ├── com.py       # Common functions (logging, time, dialogs)
│   ├── display.py   # Display utilities
│   ├── matching.py  # Pattern matching
│   ├── my_sql.py    # Database operations
│   └── web_driver.py # Selenium web automation
├── const/           # Constants and configuration
│   ├── cst.py       # Global constants
│   ├── items.py     # Item definitions
│   └── path.py      # Path configurations
├── data/            # Data processing
│   ├── csv.py       # CSV operations
│   ├── db.py        # Database operations
│   └── excel.py     # Excel operations
└── item/            # Data files (CSV, etc.)
```

## Key Design Patterns

### 1. Dynamic Module Loading

All business modules follow this pattern:

```python
# Module: business/windows/ea_auto_test.py
class EaAutoTest:
    def __init__(self, event):
        self.event = event

    def do(self):
        # Implementation
        pass
```

Module names (`ea_auto_test`) are automatically converted to class names (`EaAutoTest`).

### 2. Environment-Based Configuration

The application supports multiple environments based on IP address:

- **DEV_IP**: Development environment with full features
- **WEB_IP**: Web server environment
- **MAC_IP**: Mac-specific environment

Configure via `CHANGE_MENU` variable in `mytool.py`:
- `-1`: Auto-detect based on system IP
- `0`: Force DEV environment

### 3. Menu-Driven Architecture

Menus are configured in dictionaries:

```python
ANOMALY_MENU = {
    'H1データ作成': 'windows.anomaly_hst/create_h1',
    'モデル作成': 'windows.anomaly_learn/create_model',
}
```

External menus (Fold, Web) are loaded from CSV files via `com.get_menu()`.

## Coding Standards

### Language & Encoding

- **Python 3.x** (currently targets 3.9+)
- **UTF-8 encoding** with BOM marker: `# -*- coding: utf-8 -*-`
- **Japanese comments and variable names** are acceptable and encouraged for business logic

### Naming Conventions

- **Classes**: PascalCase (e.g., `EnglishDict`, `AnomalyData`)
- **Functions/Variables**: snake_case (e.g., `get_menu`, `create_data`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAIN_BGCOLOR`, `DEV_IP`)
- **Private methods**: Prefix with double underscore (e.g., `__run`)

### Cross-Platform Compatibility

Always check platform before platform-specific operations:

```python
from const import cst

if 'Win' == cst.PC:
    # Windows-specific code
    subprocess.Popen(['explorer', path])
else:
    # Mac-specific code
    subprocess.Popen(['open', path])
```

## Common Utilities (common/com.py)

Essential functions to use:

- **com.log(msg)**: Logging with timestamps
- **com.dialog(msg, title, type)**: Display dialogs
- **com.get_menu()**: Load menu CSV files
- **com.time_start()**: Get current timestamp
- **com.conv_time_str(seconds)**: Convert seconds to time string
- **com.send_mail()**: Send email notifications

## Working with Data

### CSV Operations

```python
from data import csv

# Read CSV
df = csv.Csv().read(file_path)

# Write CSV
csv.Csv().write(file_path, dataframe)
```

### Database Operations

```python
from common import my_sql

# Execute query
result = my_sql.MySql().execute(query)
```

### Excel Operations

```python
from data import excel

# Read Excel
df = excel.Excel().read(file_path, sheet_name)
```

## Development Guidelines

### When Adding New Features

1. **Choose the correct directory**:
   - Mac-only → `business/mac/`
   - Windows-only → `business/windows/`
   - Cross-platform → `business/multiple/`
   - ML/Prediction → `business/predict/`
   - Batch jobs → `business/batch/`

2. **Follow the module pattern**:
   ```python
   class MyNewFeature:
       def __init__(self, event):
           self.event = event

       def do(self):
           # Implementation
           return result
   ```

3. **Add to appropriate menu** in `mytool.py`:
   ```python
   BTNS = {
       'My Feature': 'mac.my_new_feature',
   }
   ```

4. **Use existing utilities**:
   - Don't reinvent logging, dialogs, or file operations
   - Leverage `common/com.py` functions
   - Follow existing error handling patterns

### When Refactoring

- **Preserve the dynamic loading pattern** - don't break module execution
- **Maintain backward compatibility** with existing menu configurations
- **Test on both Windows and Mac** if changing cross-platform code
- **Keep Japanese comments** unless specifically translating

### Security Considerations

⚠️ **IMPORTANT**: The codebase contains hardcoded credentials that should be removed:

- Line 11 in `mytool.py` contains a GitHub PAT token (should be in environment variable)
- Password authentication uses CSV files (consider more secure storage)
- Email credentials may be exposed (use environment variables)

When working on this codebase:
- **Never commit new hardcoded secrets**
- **Recommend environment variables** for sensitive data
- **Use .env files** (ensure they're in .gitignore)

## Testing & Running

### Run Main GUI

```bash
python mytool.py
```

### Run Specific Module

```bash
python run.py -m windows.anomaly_hst -e create_h1
```

### Run Batch Processing

```bash
python mytool.py -f Batch
```

### Build Executables

**Mac**:
```bash
python mytool_app.py py2app
```

**Windows**:
```bash
pyinstaller mytool_exe.spec --clean
```

## Dependencies

Key libraries in use:

- **FreeSimpleGUI**: GUI framework
- **pandas**: Data manipulation
- **pyautogui**: UI automation
- **selenium**: Web automation
- **keras/tensorflow**: Machine learning
- **statsmodels**: ARIMA prediction

Dependencies should be documented in `requirements.txt` (currently missing - consider creating one).

## AI Assistant Instructions

When Claude Code works on this project:

### DO:
- ✅ Follow existing code style and patterns
- ✅ Use Japanese for business logic comments
- ✅ Check platform compatibility (`cst.PC`)
- ✅ Use `com.log()` for logging
- ✅ Preserve dynamic module loading
- ✅ Add proper error handling
- ✅ Test cross-platform implications

### DON'T:
- ❌ Break the module naming convention (snake_case → PascalCase)
- ❌ Hardcode file paths (use `const/path.py`)
- ❌ Add new hardcoded credentials
- ❌ Change the `do()` method signature pattern
- ❌ Remove platform checks without understanding implications
- ❌ Mix Windows and Mac-specific code without guards

### When Debugging:
- Check `com.log()` output for execution flow
- Verify module names match class names (case conversion)
- Ensure CSV menu files are loaded correctly
- Check platform-specific paths
- Verify IP-based environment detection

## Git Workflow

Current branch: `claude/update-claude-md-ZLnZW`

When making changes:
1. Develop on the feature branch
2. Commit with clear Japanese or English messages
3. Push to origin with: `git push -u origin claude/update-claude-md-ZLnZW`

## Project Context

This is a personal productivity tool for:
- Financial market analysis and trading automation
- Personal asset management
- Web automation tasks
- Cross-platform utilities

The tool integrates MT4 (MetaTrader 4) trading platform operations, anomaly detection for market data, and predictive modeling using machine learning.

---

**Last Updated**: 2025-12-20
**Python Version**: 3.9+
**Platforms**: Windows, macOS
