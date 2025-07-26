# Utilities Folder

This folder contains debugging, testing, and maintenance scripts for the Spooky Football Engine.

## 📋 Scripts Overview

### 🔍 Testing & Debugging

#### `postgresql_compatibility_check.py`
- **Purpose**: Tests all API endpoints for PostgreSQL compatibility
- **Usage**: `python3 postgresql_compatibility_check.py`
- **Tests**: All 7 API endpoints to ensure they work with PostgreSQL

#### `database_health_check.py`
- **Purpose**: Comprehensive database health monitoring
- **Usage**: `python3 database_health_check.py`
- **Checks**:
  - Database connectivity
  - Table record counts
  - Data integrity issues
  - Last update timestamps

#### `api_stress_test.py`
- **Purpose**: Stress tests API endpoints under concurrent load
- **Usage**: `python3 api_stress_test.py`
- **Configuration**: 20 requests total, 5 concurrent

#### `debug_main.py`
- **Purpose**: Debug version of main strength calculation
- **Usage**: `python3 debug_main.py`
- **Features**: Detailed output with all calculation steps

### 🛠️ Migration & Setup

#### `migrate_to_postgresql.py`
- **Purpose**: Migrates SQLite database to PostgreSQL
- **Usage**: `DATABASE_URL="postgresql://..." python3 migrate_to_postgresql.py`
- **Note**: Requires PostgreSQL connection string

### 🧪 Feature Testing

#### `test_demo.py`
- **Purpose**: Tests the demo Flask application locally
- **Usage**: `python3 test_demo.py`
- **Tests**: Basic functionality of demo_app.py

#### `test_new_features.py`
- **Purpose**: Tests newly added features
- **Usage**: `python3 test_new_features.py`
- **Focus**: European competitions, form display, etc.

#### `check_dual_scores.py`
- **Purpose**: Verifies dual scoring system (local vs European)
- **Usage**: `python3 check_dual_scores.py`
- **Checks**: Proper score normalization

#### `simple_test.py`
- **Purpose**: Basic smoke test for core functionality
- **Usage**: `python3 simple_test.py`
- **Quick**: Minimal test for rapid verification

## 🚀 Quick Commands

### Production Health Check
```bash
# Check if production app is healthy
python3 postgresql_compatibility_check.py

# Check database health
python3 database_health_check.py
```

### Local Development
```bash
# Debug calculations
python3 debug_main.py

# Test Flask app locally
python3 test_demo.py
```

### Performance Testing
```bash
# Stress test the API
python3 api_stress_test.py
```

### Database Migration
```bash
# Migrate to PostgreSQL (requires DATABASE_URL)
DATABASE_URL="your_postgres_url" python3 migrate_to_postgresql.py
```

## 📝 Notes

- Most scripts assume the project structure with imports from parent directory
- Production scripts target the Railway deployment URL
- Always activate virtual environment before running: `source ../venv/bin/activate`
- Some scripts require environment variables (like DATABASE_URL)

### Environment Requirements

**Scripts that need virtual environment activated:**
- `simple_test.py` - requires Flask
- `test_demo.py` - requires Flask and other dependencies

**Scripts that work with system Python:**
- `postgresql_compatibility_check.py` - uses requests (installed system-wide)
- `database_health_check.py` - uses standard library + psycopg2
- `api_stress_test.py` - uses requests
- Other scripts use mainly standard library

**For production database checks:**
```bash
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"
python3 database_health_check.py
```

## 🔧 Adding New Utilities

When adding new utility scripts:
1. Follow the naming convention: `purpose_action.py`
2. Include a docstring explaining the script's purpose
3. Add error handling and clear output messages
4. Update this README with the new script's information