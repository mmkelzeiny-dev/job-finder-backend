import os
import sys
import subprocess

def run(cmd):
    print(f"\n> {cmd}")
    subprocess.run(cmd, shell=True, check=False)

def main():
    print("🔧 Fixing httpx/httpcore compatibility for Python", sys.version)
    
    # Step 1: Uninstall old versions
    print("\n📦 Uninstalling existing versions...")
    run(f'"{sys.executable}" -m pip uninstall -y httpx httpcore h11')

    # Step 2: Install compatible versions
    print("\n📦 Installing stable versions (for Python 3.13+ / 3.14)...")
    run(f'"{sys.executable}" -m pip install "httpx==0.27.2" "httpcore==1.0.5" "h11==0.14.0"')

    # Step 3: Verify
    print("\n🔍 Verifying installation...")
    try:
        import httpx
        print(f"✅ httpx successfully installed: {httpx.__version__}")
    except Exception as e:
        print("❌ Import failed after reinstall:", e)

if __name__ == "__main__":
    main()
