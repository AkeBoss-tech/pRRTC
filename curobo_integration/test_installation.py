import torch
import sys

def check_installation():
    print(f"Python: {sys.version}")
    
    # Check PyTorch
    try:
        print(f"PyTorch: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"CUDA Available: Yes ({torch.cuda.get_device_name(0)})")
        else:
            print("CUDA Available: NO")
    except ImportError:
        print("PyTorch not installed.")

    # Check cuRobo
    try:
        import curobo
        print(f"cuRobo: {curobo.__version__} (Installed at {curobo.__path__[0]})")
    except ImportError:
        print("cuRobo NOT installed or not found in PYTHONPATH.")
    except Exception as e:
        print(f"Error importing cuRobo: {e}")

    # Check Isaac Sim (omniverse)
    try:
        import omni.isaac.core
        print("Isaac Sim (omni.isaac.core): Found")
    except ImportError:
        print("Isaac Sim python bindings NOT found.")

if __name__ == "__main__":
    check_installation()
