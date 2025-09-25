# Complete Bedrock Account Fix - TorWAR Application

## Issue Description
The TorWAR application was using the wrong AWS account (466171249965) when invoking Bedrock models, instead of the correct account (445567094096). This caused AccessDeniedException errors when trying to use AI Analysis features.

## Root Cause Analysis
The issue was in multiple locations where the AWS profile was hardcoded to `beyon-money-payer`:

1. **aws_helper.py** - Default profile fallback
2. **app.py** - Flask session initialization 
3. **aws_auth_routes.py** - Profile selection logic
4. **app.py** - HTML form default value

## Complete Fix Applied

### 1. Updated aws_helper.py
**File**: `aws_helper.py` (Line 28)
```python
# OLD:
profile = 'beyon-money-payer'
print(f"DEBUG: Using beyon-money-payer profile for AWS session")

# NEW:
profile = 'tau-dev'
print(f"DEBUG: Using tau-dev profile for AWS session (account 445567094096)")
```

### 2. Updated app.py - Session Initialization
**File**: `app.py` (Lines 2579-2580)
```python
# OLD:
session['aws_profile'] = 'beyon-money-payer'
session['aws_account_id'] = '466171249965'

# NEW:
session['aws_profile'] = 'tau-dev'
session['aws_account_id'] = '445567094096'
```

### 3. Updated app.py - HTML Form Default
**File**: `app.py` (Line 1406)
```html
<!-- OLD: -->
<input type="text" class="form-control" name="profile_name" value="beyon-money-payer" readonly>

<!-- NEW: -->
<input type="text" class="form-control" name="profile_name" value="tau-dev" readonly>
```

### 4. Updated aws_auth_routes.py - Profile Logic
**File**: `aws_auth_routes.py` (Lines 75-77)
```python
# OLD:
# Use beyon-money-payer as default if default is selected
if profile_name == 'default':
    profile_name = 'beyon-money-payer'

# NEW:
# Use tau-dev as default if default is selected
if profile_name == 'default':
    profile_name = 'tau-dev'
```

## Verification Steps Completed

### ✅ Profile Access Test
```bash
aws sts get-caller-identity --profile tau-dev
# Result: Account 445567094096 ✅
```

### ✅ Bedrock Model Access Test
```bash
aws bedrock-runtime invoke-model --profile tau-dev --region us-east-1 \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":50,"messages":[{"role":"user","content":"Hello"}]}'
# Result: Successful invocation ✅
```

### ✅ Flask Session Test
```bash
python3 test_session_fix.py
# Result: SUCCESS - Using correct account 445567094096 ✅
```

### ✅ Cache Clearing
```bash
python3 clear_sessions.py
# Result: All caches cleared ✅
```

## Files Modified
1. `aws_helper.py` - Profile fallback logic
2. `app.py` - Session initialization and HTML form
3. `aws_auth_routes.py` - Profile selection logic
4. `clear_sessions.py` - Cache clearing utility (new)
5. `test_session_fix.py` - Verification script (new)
6. `COMPLETE_BEDROCK_FIX.md` - This documentation

## Expected Behavior After Fix

### Before Fix:
```
DEBUG: Error invoking Bedrock model: An error occurred (AccessDeniedException) when calling the InvokeModel operation: User: arn:aws:sts::466171249965:assumed-role/AssumeReadOnlyRoleFromBeyonMaster/botocore-session-1756729459 is not authorized to perform: bedrock:InvokeModel
```

### After Fix:
```
DEBUG: Using tau-dev profile for AWS session (account 445567094096)
DEBUG: Bedrock invocation successful
```

## Restart Instructions

1. **Stop your TorWAR application** if it's currently running
2. **Clear any browser sessions** (logout and login again)
3. **Start the TorWAR application**
4. **Test AI Analysis** on any recommendation

## Verification Commands

### Check Current Account:
```bash
cd /home/toraif/TorWAR
python3 test_simple_bedrock.py
```

### Check Session Configuration:
```bash
cd /home/toraif/TorWAR  
python3 test_session_fix.py
```

## Troubleshooting

If you still see the old account (466171249965):

1. **Clear browser cache** and cookies
2. **Restart the Flask application** completely
3. **Check application logs** for the debug message showing tau-dev profile
4. **Verify no other processes** are using cached sessions

## Account Mapping Reference
- ❌ **Old Account**: 466171249965 (beyon-money-payer profile)
- ✅ **New Account**: 445567094096 (tau-dev profile)

## Status
- ✅ All code changes applied
- ✅ All tests passing
- ✅ Caches cleared
- ✅ Ready for application restart

**Fix completed**: September 2, 2025  
**Status**: Complete - Ready for production use  
**Next step**: Restart TorWAR application
