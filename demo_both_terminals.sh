#!/bin/bash

echo "=== Cable Tester Frontend/Backend Demo ==="
echo ""
echo "This will show you how the system works with two terminals."
echo ""
echo "INSTRUCTIONS:"
echo "1. Open a NEW terminal window"
echo "2. Navigate to: $(pwd)"
echo "3. Run: source venv/bin/activate && python src/backend_demo.py"
echo ""
echo "4. Then in THIS terminal, run: source venv/bin/activate && python src/frontend_simple_fixed.py"
echo ""
echo "5. Try these commands in the frontend:"
echo "   - Press 1 to simulate SSH connection"
echo "   - Press 2 to simulate security test"
echo "   - Press 3 to simulate performance tests"
echo "   - Press 4 to get status"
echo "   - Press q to quit"
echo ""
echo "Press Enter when you have the backend running in another terminal..."
read

echo "Starting frontend..."
source venv/bin/activate && python src/frontend_simple_fixed.py