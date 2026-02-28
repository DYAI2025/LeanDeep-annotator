import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from api.engine import engine

def run_tests():
    fixtures_path = Path("eval/ctg_fixtures.json")
    if not fixtures_path.exists():
        print("Fixtures not found.")
        return

    with open(fixtures_path, "r", encoding="utf-8") as f:
        fixtures = json.load(f)

    engine.load()
    
    print(f"{'ID':<40} | {'Health':<6} | {'Grade':<8} | {'Instab':<6}")
    print("-" * 75)

    for fix in fixtures:
        res = engine.analyze_conversation(fix["messages"])
        topo = res["topology"]
        health = topo["health"]["score"]
        grade = topo["health"]["grade"]
        instab = topo["gates"]["instability"]
        
        print(f"{fix['id']:<40} | {health:<6.2f} | {grade:<8} | {str(instab):<6}")
        
        # If instability matches or mismatch
        expected_instab = fix["expected_shadow"]["instability"]
        if instab != expected_instab:
            print(f"  [!] Instability mismatch: Expected {expected_instab}, got {instab}")
            for c in topo["constraints"]:
                if c["status"] != "pass":
                    print(f"      - {c['id']}: {c['status']} ({c['notes']})")

if __name__ == "__main__":
    run_tests()
