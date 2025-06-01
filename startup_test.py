
import sys
import traceback

def test_imports():
    """Test all imports to identify issues"""
    tests = []
    
    try:
        from database import DatabaseManager
        tests.append(("DatabaseManager", True, "OK"))
    except Exception as e:
        tests.append(("DatabaseManager", False, str(e)))
    
    try:
        from flask import Flask
        tests.append(("Flask", True, "OK"))
    except Exception as e:
        tests.append(("Flask", False, str(e)))
    
    try:
        import openai
        tests.append(("OpenAI", True, "OK"))
    except Exception as e:
        tests.append(("OpenAI", False, str(e)))
    
    try:
        from github import Github
        tests.append(("GitHub", True, "OK"))
    except Exception as e:
        tests.append(("GitHub", False, str(e)))
    
    try:
        from self_migration_manager import SelfMigrationManager
        tests.append(("SelfMigrationManager", True, "OK"))
    except Exception as e:
        tests.append(("SelfMigrationManager", False, str(e)))
    
    return tests

def test_database():
    """Test database initialization"""
    try:
        from database import DatabaseManager
        db = DatabaseManager()
        db.init_db()
        return True, "Database initialized successfully"
    except Exception as e:
        return False, f"Database error: {e}"

def main():
    print("=== ClaireDev Startup Test ===\n")
    
    print("Testing imports...")
    import_tests = test_imports()
    
    for name, success, message in import_tests:
        status = "✅" if success else "❌"
        print(f"{status} {name}: {message}")
    
    print("\nTesting database...")
    db_success, db_message = test_database()
    status = "✅" if db_success else "❌"
    print(f"{status} Database: {db_message}")
    
    print("\nTesting main app...")
    try:
        import main
        print("✅ Main app: Import successful")
        
        # Test if Flask app can be created
        if hasattr(main, 'app'):
            print("✅ Flask app: Created successfully")
        else:
            print("❌ Flask app: Not found")
            
    except Exception as e:
        print(f"❌ Main app: {e}")
        traceback.print_exc()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
