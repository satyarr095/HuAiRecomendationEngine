#!/usr/bin/env python3
"""
Setup script for AI Recommendation Engine
Installs and configures Ollama with required models
"""

import subprocess
import sys
import time
import requests
import platform

def run_command(command, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_ollama_installed():
    """Check if Ollama is installed"""
    success, stdout, stderr = run_command("ollama --version")
    return success

def install_ollama():
    """Install Ollama based on the operating system"""
    system = platform.system().lower()
    
    print("🦙 Installing Ollama...")
    
    if system == "darwin":  # macOS
        print("📦 Installing Ollama on macOS...")
        success, stdout, stderr = run_command("curl -fsSL https://ollama.ai/install.sh | sh")
        if not success:
            print("❌ Failed to install Ollama via script. Trying with brew...")
            success, stdout, stderr = run_command("brew install ollama")
            
    elif system == "linux":
        print("📦 Installing Ollama on Linux...")
        success, stdout, stderr = run_command("curl -fsSL https://ollama.ai/install.sh | sh")
        
    else:
        print("❌ Unsupported operating system. Please install Ollama manually from https://ollama.ai")
        return False
    
    if success:
        print("✅ Ollama installed successfully!")
        return True
    else:
        print(f"❌ Failed to install Ollama: {stderr}")
        return False

def start_ollama_service():
    """Start Ollama service"""
    print("🚀 Starting Ollama service...")
    
    # Try to start Ollama service
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait a bit for service to start
    time.sleep(3)
    
    # Check if service is running
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running!")
            return True
    except:
        pass
    
    print("⚠️  Ollama service might not be running. Please start it manually with: ollama serve")
    return False

def pull_models():
    """Pull required Ollama models"""
    models_to_try = [
        "mistral:7b",
        "llama2:7b", 
        "tinyllama"
    ]
    
    successful_model = None
    
    for model in models_to_try:
        print(f"📥 Attempting to pull {model}...")
        success, stdout, stderr = run_command(f"ollama pull {model}")
        
        if success:
            print(f"✅ Successfully pulled {model}")
            successful_model = model
            break
        else:
            print(f"❌ Failed to pull {model}: {stderr}")
            continue
    
    if successful_model:
        print(f"🎉 AI model ready: {successful_model}")
        return successful_model
    else:
        print("❌ Failed to pull any models. Please check your internet connection.")
        return None

def install_python_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    success, stdout, stderr = run_command(f"{sys.executable} -m pip install -r requirements.txt")
    
    if success:
        print("✅ Python dependencies installed successfully!")
        return True
    else:
        print(f"❌ Failed to install dependencies: {stderr}")
        return False

def test_setup():
    """Test if everything is set up correctly"""
    print("🧪 Testing setup...")
    
    try:
        import ollama
        from duckduckgo_search import DDGS
        from bs4 import BeautifulSoup
        
        print("✅ All Python packages imported successfully!")
        
        # Test Ollama connection
        try:
            models = ollama.list()
            if models and models.get('models'):
                print(f"✅ Ollama is working with {len(models['models'])} model(s)!")
                return True
            else:
                print("⚠️  Ollama is connected but no models found.")
                return False
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up AI Recommendation Engine")
    print("=" * 50)
    
    # Step 1: Install Python dependencies
    if not install_python_dependencies():
        print("❌ Setup failed at Python dependencies step")
        return False
    
    # Step 2: Check/Install Ollama
    if not check_ollama_installed():
        if not install_ollama():
            print("❌ Setup failed at Ollama installation step")
            return False
    else:
        print("✅ Ollama is already installed!")
    
    # Step 3: Start Ollama service
    start_ollama_service()
    
    # Step 4: Pull AI models
    model = pull_models()
    if not model:
        print("❌ Setup failed at model downloading step")
        return False
    
    # Step 5: Test everything
    if test_setup():
        print("\n🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Make sure Ollama service is running: ollama serve")
        print("2. Start the AI engine: python app.py")
        print("3. Test with your frontend!")
        return True
    else:
        print("❌ Setup completed but tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 