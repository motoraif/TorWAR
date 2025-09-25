# AWS Login Route Fix

## Overview

This update fixes the BuildError related to the 'aws_login' endpoint that was occurring when trying to redirect to this route. The error message was:

```
BuildError: Could not build url for endpoint 'aws_login'. Did you mean 'index' instead?
```

## Issue Identified

The issue was that the AWS authentication routes were defined in the `aws_auth_routes.py` file but were not being registered with the Flask application. This caused the `url_for('aws_login')` function to fail because the route wasn't registered.

## Changes Made

### 1. Added Import for AWS Auth Routes

Added the import for the register_auth_routes function from the aws_auth_routes.py file:

```python
from aws_auth_routes import register_auth_routes
```

### 2. Registered AWS Auth Routes with Flask App

Added the following line after creating the Flask app to register the AWS authentication routes:

```python
# Register AWS authentication routes
register_auth_routes(app)
```

### 3. Verified Route Definitions

Confirmed that the aws_auth_routes.py file contains the necessary route definitions:

```python
@app.route('/aws-login')
@app.route('/aws_login')  # Add alias for consistency
def aws_login():
    """AWS authentication page."""
    # Route implementation
```

## Benefits

- Fixed the BuildError that was occurring when trying to redirect to the aws_login route
- Ensured that all AWS authentication routes are properly registered with the Flask application
- Maintained the separation of concerns by keeping AWS authentication routes in a separate file

## Notes

- The aws_auth_routes.py file contains multiple AWS authentication-related routes, including:
  - aws_login: For logging in to AWS
  - aws_logout: For logging out from AWS
  - aws_profile_select: For selecting an AWS profile
  - aws_region_select: For selecting an AWS region

- All these routes are now properly registered with the Flask application and can be used with url_for()
- The fix maintains the modular structure of the application by keeping AWS authentication routes in a separate file
