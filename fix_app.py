#!/usr/bin/env python3
"""
Script to fix app.py by removing duplicate routes and commenting out missing imports
"""

def fix_app_py():
    with open('app.py', 'r') as f:
        lines = f.readlines()
    
    # Fix the import
    for i, line in enumerate(lines):
        if 'from check_ta_route import register_check_ta_route' in line:
            lines[i] = '# from check_ta_route import register_check_ta_route  # Module not found\n'
            print(f"Fixed import on line {i+1}")
        elif 'register_check_ta_route(app)' in line and not line.strip().startswith('#'):
            lines[i] = '    # register_check_ta_route(app)  # Module not found\n'
            print(f"Fixed function call on line {i+1}")
    
    # Find duplicate route definitions
    route_lines = []
    for i, line in enumerate(lines):
        if "@app.route('/recommendations/report')" in line:
            route_lines.append(i)
    
    if len(route_lines) > 1:
        print(f"Found duplicate routes at lines: {[l+1 for l in route_lines]}")
        
        # Remove the first duplicate (keep the second one which should be complete)
        start_remove = route_lines[0]
        
        # Find the end of the first route (look for the next @app.route or end of file)
        end_remove = len(lines)
        for i in range(start_remove + 1, len(lines)):
            if lines[i].startswith('@app.route') or lines[i].startswith('if __name__'):
                end_remove = i
                break
        
        print(f"Removing lines {start_remove+1} to {end_remove}")
        
        # Remove the duplicate route
        lines = lines[:start_remove] + lines[end_remove:]
    
    # Write the fixed file
    with open('app.py', 'w') as f:
        f.writelines(lines)
    
    print("✅ app.py has been fixed")

if __name__ == "__main__":
    fix_app_py()
