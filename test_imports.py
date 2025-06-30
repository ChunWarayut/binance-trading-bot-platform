#!/usr/bin/env python3

print("Testing imports...")

try:
    import telegram
    print("✅ telegram imported successfully")
except ImportError as e:
    print(f"❌ telegram import failed: {e}")

try:
    import fastapi
    print("✅ fastapi imported successfully")
except ImportError as e:
    print(f"❌ fastapi import failed: {e}")

try:
    import streamlit
    print("✅ streamlit imported successfully")
except ImportError as e:
    print(f"❌ streamlit import failed: {e}")

try:
    import binance
    print("✅ binance imported successfully")
except ImportError as e:
    print(f"❌ binance import failed: {e}")

try:
    import pandas
    print("✅ pandas imported successfully")
except ImportError as e:
    print(f"❌ pandas import failed: {e}")

print("Import test completed!")

# Save results to file
import json
results = {
    "telegram": False,
    "fastapi": False,
    "streamlit": False,
    "binance": False,
    "pandas": False
}

try:
    import telegram
    results["telegram"] = True
except:
    pass

try:
    import fastapi
    results["fastapi"] = True
except:
    pass

try:
    import streamlit
    results["streamlit"] = True
except:
    pass

try:
    import binance
    results["binance"] = True
except:
    pass

try:
    import pandas
    results["pandas"] = True
except:
    pass

with open("import_test.json", "w") as f:
    json.dump(results, f, indent=2) 