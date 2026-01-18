import subprocess
import sys

def uninstall_dependencies():
    """Uninstalls dependencies used by Zombi Tools"""
    packages = ['pymem', 'keyboard', 'psutil', 'pyautogui', 'pillow', 'pynput']
    
    print("=" * 50)
    print("ZOMBI TOOLS CLEANUP UTILITY")
    print("=" * 50)
    print("This will uninstall the following packages:")
    for p in packages:
        print(f" - {p}")
    print("-" * 50)
    
    confirm = input("Are you sure you want to proceed? (y/n): ").lower()
    
    if confirm == 'y':
        print("\nUninstalling...")
        for package in packages:
            try:
                print(f"Removing {package}...")
                # Run pip uninstall with -y to automatically confirm
                subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", package])
                print(f"✓ {package} removed.")
            except subprocess.CalledProcessError:
                print(f"⚠ Could not remove {package} (maybe it wasn't installed?)")
            except Exception as e:
                print(f"❌ Error removing {package}: {e}")
        
        print("\n" + "=" * 50)
        print("Cleanup Complete!")
        print("=" * 50)
    else:
        print("Operation cancelled.")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    uninstall_dependencies()