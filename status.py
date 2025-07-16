#!/usr/bin/env python3
"""
Status and validation script for the AI News App pipeline.
Checks configuration, dependencies, and system readiness.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        ('requests', '2.31.0'),
        ('feedparser', '6.0.10'),
        ('psycopg2', '2.9.7'),
        ('dotenv', '1.0.0')
    ]
    
    missing_modules = []
    
    for module_name, min_version in required_modules:
        try:
            if module_name == 'psycopg2':
                import psycopg2
                version = psycopg2.__version__
            elif module_name == 'dotenv':
                import dotenv
                # python-dotenv doesn't expose __version__ directly
                try:
                    import importlib.metadata
                    version = importlib.metadata.version('python-dotenv')
                except:
                    version = 'installed'
            else:
                module = __import__(module_name)
                version = getattr(module, '__version__', 'unknown')
            
            print(f"  ✓ {module_name}: {version}")
        except ImportError:
            missing_modules.append(module_name)
            print(f"  ❌ {module_name}: not installed")
    
    if missing_modules:
        print(f"\n❌ Missing dependencies: {', '.join(missing_modules)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies installed")
        return True

def check_configuration():
    """Check configuration and environment variables."""
    print("\n🔧 Checking configuration...")
    
    try:
        from src.config import Config
        
        # Check environment file
        env_file = '.env'
        if os.path.exists(env_file):
            print(f"  ✓ Found {env_file}")
        else:
            print(f"  ⚠️  {env_file} not found (optional)")
            print(f"     Copy .env.example to .env and configure")
        
        # Check critical environment variables
        critical_vars = ['NEWS_API_KEY', 'DB_PASSWORD']
        optional_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER']
        
        for var in critical_vars:
            value = os.getenv(var)
            if value:
                print(f"  ✓ {var}: configured")
            else:
                print(f"  ❌ {var}: not set (required)")
        
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                print(f"  ✓ {var}: {value}")
            else:
                default_val = getattr(Config, var, 'default')
                print(f"  ⚠️  {var}: using default ({default_val})")
        
        # Test RSS feeds configuration
        print(f"  ✓ RSS feeds configured: {len(Config.RSS_FEEDS)}")
        for source, url in Config.RSS_FEEDS.items():
            print(f"    - {source}: {url}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

def check_file_structure():
    """Check if all required files are present."""
    print("\n📁 Checking file structure...")
    
    required_files = [
        'requirements.txt',
        '.env.example',
        'README.md',
        'run_pipeline.py',
        'setup_db.py',
        'test_components.py',
        'src/__init__.py',
        'src/config.py',
        'src/database.py',
        'src/news_api.py',
        'src/rss_parser.py',
        'src/main.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file_path} ({size} bytes)")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path}: missing")
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required files present")
        return True

def run_component_tests():
    """Run basic component tests."""
    print("\n🧪 Running component tests...")
    
    try:
        # Import test module and run tests
        import test_components
        test_components.main()
        return True
    except Exception as e:
        print(f"❌ Component tests failed: {e}")
        return False

def show_usage_instructions():
    """Show usage instructions."""
    print("\n📖 Usage Instructions:")
    print("="*50)
    
    print("\n1. Setup (one-time):")
    print("   cp .env.example .env")
    print("   # Edit .env with your API keys and database credentials")
    print("   python setup_db.py")
    
    print("\n2. Run pipeline:")
    print("   python run_pipeline.py                    # Full pipeline")
    print("   python run_pipeline.py --no-newsapi      # RSS only")
    print("   python run_pipeline.py --no-rss          # NewsAPI only")
    print("   python run_pipeline.py --query 'tech'    # Search query")
    print("   python run_pipeline.py --verbose         # Debug mode")
    
    print("\n3. Test components:")
    print("   python test_components.py")
    
    print("\n4. Check status:")
    print("   python status.py")

def main():
    """Main status check function."""
    print("🔍 AI News App - System Status Check")
    print("="*40)
    
    checks = [
        check_dependencies(),
        check_file_structure(),
        check_configuration(),
    ]
    
    # Only run component tests if basic checks pass
    if all(checks):
        checks.append(run_component_tests())
    
    print("\n" + "="*40)
    
    if all(checks):
        print("✅ System ready! All checks passed.")
        print("\nYour news ingestion pipeline is ready to use.")
        show_usage_instructions()
    else:
        print("❌ System not ready. Please fix the issues above.")
        print("\nFor setup help, see README.md")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())