#!/bin/bash

# EQUITR Coder Installation Script
# This script installs and sets up EQUITR Coder on your system

set -e

echo "🚀 EQUITR Coder Installation"
echo "============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

python_version=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${python_version} found${NC}"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Virtual environment detected: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠️  No virtual environment detected${NC}"
    echo "It's recommended to install EQUITR Coder in a virtual environment"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv equitr-env
        source equitr-env/bin/activate
        echo -e "${GREEN}✅ Virtual environment created and activated${NC}"
    fi
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Install EQUITR Coder
echo -e "${BLUE}Installing EQUITR Coder...${NC}"
pip install -e .

# Create config directory
echo -e "${BLUE}Creating configuration directory...${NC}"
mkdir -p ~/.equitr

# Create default configuration if it doesn't exist
if [ ! -f ~/.equitr/config.yaml ]; then
    echo -e "${BLUE}Creating default configuration...${NC}"
    cat > ~/.equitr/config.yaml << 'EOF'
# EQUITR Coder Configuration
llm:
  model: "gpt-4o-mini"  # Default model - change as needed
  temperature: 0.3
  max_tokens: 4000
  budget: 25.0  # USD limit
  # api_key: "your-api-key-here"  # Set via environment variable instead

orchestrator:
  use_multi_agent: false
  max_iterations: 20

session:
  session_dir: "~/.equitr/sessions"
  max_context: 32000

repository:
  ignore_patterns:
    - "*.log"
    - "*.tmp"
    - "node_modules/"
    - "__pycache__/"
    - ".git/"
    - ".env"

git:
  auto_commit: true
  commit_message_prefix: "🤖 EQUITR:"
EOF
    echo -e "${GREEN}✅ Default configuration created at ~/.equitr/config.yaml${NC}"
else
    echo -e "${YELLOW}⚠️  Configuration already exists at ~/.equitr/config.yaml${NC}"
fi

# Create session directory
mkdir -p ~/.equitr/sessions

# Test installation
echo -e "${BLUE}Testing installation...${NC}"
if command -v equitrcoder &> /dev/null; then
    echo -e "${GREEN}✅ EQUITR Coder installed successfully!${NC}"
    echo -e "${GREEN}✅ Command 'equitrcoder' is available${NC}"
else
    echo -e "${RED}❌ Installation failed - command not found${NC}"
    exit 1
fi

# Show version
echo -e "${BLUE}Version check:${NC}"
equitrcoder --version

echo ""
echo -e "${GREEN}🎉 Installation Complete!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Set your API key:"
echo "   export OPENAI_API_KEY='your-api-key-here'"
echo ""
echo "2. Start using EQUITR Coder:"
echo "   equitrcoder"
echo ""
echo "3. For help:"
echo "   equitrcoder --help"
echo ""
echo -e "${BLUE}Configuration file: ~/.equitr/config.yaml${NC}"
echo -e "${BLUE}Session directory: ~/.equitr/sessions${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"