#!/usr/bin/env python3
"""
Quick start script for the Matching Engine API Gateway
"""
import sys
import os

# Setup paths
project_root = os.path.dirname(os.path.abspath(__file__))
matching_engine_path = os.path.join(project_root, 'core/matching-engine')

sys.path.insert(0, matching_engine_path)
sys.path.insert(0, project_root)

# Import and run gateway
if __name__ == "__main__":
    import uvicorn
    from services.order_gateway.gateway import app

    print("\n" + "="*70)
    print("MATCHING ENGINE - REST API GATEWAY")
    print("="*70)
    print(f"\n📡 Starting server...")
    print(f"   API URL: http://localhost:8000")
    print(f"   Docs:    http://localhost:8000/docs")
    print(f"   ReDoc:   http://localhost:8000/redoc")
    print(f"\n✅ Ready to accept orders\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
