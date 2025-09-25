# FINAL Bedrock Profile Fix - AI Dashboard Issue

## Issue
Even after previous fixes, the AI Dashboard was still using the wrong AWS account (466171249965) for Bedrock access, showing:
```
DEBUG: Same-account Bedrock client initialized successfully
DEBUG: Error invoking Bedrock model: AccessDeniedException... User: arn:aws:sts::466171249965:assumed-role/AssumeReadOnlyRoleFromBeyonMaster/...
```

## Root Cause
The `bedrock_helper.py` was falling back to "same-account" access when no cross-account configuration was provided, which used whatever profile the user was logged in with (beyon-money-payer) instead of forcing the tau-dev profile that has Bedrock access.

## Final Fix Applied

### Modified bedrock_helper.py
**Changed the fallback logic to FORCE tau-dev profile usage:**

```python
# OLD - Fallback to same-account access:
try:
    aws_session = get_aws_session()
    if aws_session:
        self.bedrock_client = aws_session.client('bedrock-runtime', region_name=self.bedrock_region)
        self.auth_method = 'same-account'
        print("DEBUG: Same-account Bedrock client initialized successfully")

# NEW - Force tau-dev profile for Bedrock:
try:
    print("DEBUG: Forcing tau-dev profile for Bedrock access...")
    tau_dev_session = boto3.Session(profile_name='tau-dev', region_name=self.bedrock_region)
    
    # Verify we're using the correct account
    sts_client = tau_dev_session.client('sts')
    identity = sts_client.get_caller_identity()
    account_id = identity.get('Account')
    
    if account_id == '445567094096':
        self.bedrock_client = tau_dev_session.client('bedrock-runtime', region_name=self.bedrock_region)
        self.auth_method = 'tau-dev-profile'
        print(f"DEBUG: tau-dev Bedrock client initialized successfully (account: {account_id})")
        return
```

### Updated Global Analyzer Management
**Added logic to ensure analyzer always uses tau-dev:**

```python
# OLD - Static global instance:
bedrock_analyzer = BedrockRecommendationAnalyzer()

# NEW - Dynamic instance with tau-dev verification:
bedrock_analyzer = None

def get_bedrock_analyzer():
    global bedrock_analyzer
    
    if bedrock_analyzer is None:
        print("DEBUG: Creating new Bedrock analyzer with tau-dev profile...")
        bedrock_analyzer = BedrockRecommendationAnalyzer()
    
    # Verify the analyzer is using the correct account
    if hasattr(bedrock_analyzer, 'auth_method') and bedrock_analyzer.auth_method != 'tau-dev-profile':
        print("DEBUG: Recreating Bedrock analyzer to ensure tau-dev profile usage...")
        bedrock_analyzer = BedrockRecommendationAnalyzer()
    
    return bedrock_analyzer
```

## Verification Results

### ✅ Test Results:
```bash
python3 test_forced_tau_dev.py
# Output:
DEBUG: Forcing tau-dev profile for Bedrock access...
DEBUG: tau-dev Bedrock client initialized successfully (account: 445567094096)
✅ SUCCESS: Bedrock access working with forced tau-dev profile!
```

## Expected Behavior After Fix

### Before Fix:
```
DEBUG: Same-account Bedrock client initialized successfully
DEBUG: Error invoking Bedrock model: AccessDeniedException... User: arn:aws:sts::466171249965:...
```

### After Fix:
```
DEBUG: Forcing tau-dev profile for Bedrock access...
DEBUG: tau-dev Bedrock client initialized successfully (account: 445567094096)
DEBUG: Bedrock invocation successful
```

## Restart Instructions

1. **Stop your TorWAR application** completely
2. **Restart the application**
3. **Test AI Dashboard** at http://172.23.40.210:5000/ai-dashboard
4. **Look for the new debug messages** showing tau-dev profile usage

## Key Changes Summary

- ✅ **Forced tau-dev profile** for ALL Bedrock operations
- ✅ **Account verification** ensures 445567094096 is used
- ✅ **Dynamic analyzer creation** prevents cached wrong sessions
- ✅ **Fallback logic updated** to prioritize tau-dev over same-account
- ✅ **All caches cleared** to ensure changes take effect

## Files Modified
1. `bedrock_helper.py` - Force tau-dev profile logic
2. `test_forced_tau_dev.py` - Verification script
3. `FINAL_BEDROCK_FIX.md` - This documentation

## Status
✅ **COMPLETE** - Bedrock will now ALWAYS use tau-dev profile (account 445567094096) regardless of which profile the user is logged in with.

**The AI Dashboard should now work correctly even when logged in with beyon-money-payer!**
