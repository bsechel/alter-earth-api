#!/bin/bash

# Create Alter Earth API project structure
echo "🏗  Creating Alter Earth API project structure..."

# Create main app directories
mkdir -p app/{api,core,models,services,workers}
mkdir -p app/api/{endpoints,deps}

# Create __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/endpoints/__init__.py
touch app/api/deps/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
touch app/workers/__init__.py

echo "✅ Created project structure:"
echo ""

# Show the actual structure
if command -v tree &> /dev/null; then
    tree app/
else
    echo "app/"
    find app -type d | sed 's|[^/]*/|- |g'
    echo ""
    echo "Python files:"
    find app -name "*.py" | sort
fi

echo ""
echo "🎉 Structure created successfully!"