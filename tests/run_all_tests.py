"""
ISKOM AI-OS COMPREHENSIVE TEST RUNNER
=====================================
Menjalankan seluruh rangkaian pengujian dari Day 8 hingga Day 13 secara berurutan.
"""

import sys
import os
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

TESTS = [
    ("Day 8: Router & Architecture", "tests/test_day8_router.py"),
    ("Day 9: Knowledge Base", "tests/test_day9_knowledge.py"),
    ("Day 10: Tool System & RBAC", "tests/test_day10_tools.py"),
    ("Day 11: Workflow Engine", "tests/test_day11_workflow.py"),
    ("Day 12: Logging & Monitoring", "tests/test_day12_logging.py"),
    ("Day 13: 20 Real-World Scenarios", "tests/test_day13_20_scenarios.py"),
]

def main():
    print("=" * 80)
    print("🚀 MENJALANKAN SELURUH TEST SUITE ISKOM AI-OS (DAY 8 - DAY 13)")
    print("=" * 80)

    all_passed = True
    for name, filepath in TESTS:
        full_path = os.path.join(ROOT_DIR, filepath)
        print(f"\n▶ Menjalankan: {name} ({filepath})...")
        res = subprocess.run([sys.executable, full_path], cwd=ROOT_DIR)
        if res.returncode != 0:
            print(f"❌ GAGAL: {name}")
            all_passed = False
            break
        else:
            print(f"✅ LULUS: {name}")

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 SELURUH TEST SUITE BERHASIL 100% LULUS TANPA KENDALA!")
    else:
        print("⚠️ TERDAPAT TEST YANG GAGAL. SILAKAN PERIKSA LOG DI ATAS.")
    print("=" * 80)

if __name__ == "__main__":
    main()
