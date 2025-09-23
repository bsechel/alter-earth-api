#!/bin/bash

# Alter Earth API Setup Script
echo "🌱 Setting up Alter Earth API development environment..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Found Python $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install basic FastAPI dependencies
echo "📚 Installing FastAPI and dependencies..."
pip install fastapi uvicorn[standard]

# Create requirements.txt
echo "📝 Generating requirements.txt..."
pip freeze > requirements.txt

# Verify installation
echo "🧪 Verifying installation..."
python -c "import fastapi; print('✅ FastAPI version:', fastapi.__version__)"
python -c "import uvicorn; print('✅ Uvicorn installed successfully')"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "   source venv/bin/activate"
echo ""
echo "To start development, run:"
echo "   uvicorn main:app --reload"
echo ""