# TorWAR Versioning & Archiving System

## 🎯 Problem Solved
- **Duplicate Prevention**: No more duplicate recommendations during sync
- **Data Preservation**: Previous recommendations archived instead of deleted
- **Version Tracking**: Each sync creates a new version with audit trail
- **Historical Analysis**: View and compare recommendations across time

## 🏗️ Architecture

### Database Collections
1. **`recommendations`** - Current active recommendations
2. **`recommendations_archive`** - All previous versions with timestamps

### Version Flow
```
Sync Request → Archive Current Data → Clear Active → Sync New → Version++
```

## 🔧 Implementation Details

### 1. Archive System
```python
@classmethod
def archive_and_clear(cls, user_id):
    # Move current recommendations to archive with timestamp
    current_recs = list(cls.collection.find({'user_id': user_id}))
    if current_recs:
        archive_timestamp = datetime.utcnow()
        for rec in current_recs:
            rec['archived_at'] = archive_timestamp
            rec['is_archived'] = True
        cls.archive_collection.insert_many(current_recs)
    
    # Clear current collection
    cls.collection.delete_many({'user_id': user_id})
```

### 2. Version Management
- Auto-increment version numbers per user
- Each sync gets unique version (v1, v2, v3...)
- Version stored with each recommendation

### 3. New Routes Added
- `/archived-versions` - List all archived versions
- `/archived-recommendations/<version>` - View specific version

## 🎨 UI Features

### Dashboard Enhancements
- **History Button**: Quick access to archived versions
- **Version Info**: Sync notifications show version and archived count
- **Archive Count**: Shows how many recommendations were archived

### Archive Views
- **Version List**: Table showing version, count, and archive date
- **Archive Browser**: View recommendations from any previous version
- **Visual Distinction**: Archived cards have different styling (border-warning)

## 📊 Benefits

### For Users
- ✅ **No Data Loss**: All previous syncs preserved
- ✅ **Clean Current View**: No duplicates in active recommendations
- ✅ **Historical Tracking**: See how recommendations change over time
- ✅ **Audit Trail**: Know when each sync happened

### For System
- ✅ **Performance**: Active collection stays clean and fast
- ✅ **Scalability**: Archive grows but doesn't impact daily operations
- ✅ **Reliability**: No risk of losing historical data
- ✅ **Compliance**: Full audit trail for regulatory requirements

## 🔄 Sync Process (New)

### Before (Problematic)
```
Sync → Delete All → Insert New → Duplicates if interrupted
```

### After (Robust)
```
Sync → Archive Current → Clear Active → Insert New (versioned) → Success
```

### Sync Response Enhanced
```json
{
  "success": true,
  "synced_count": 45,
  "archived_count": 42,
  "version": 3,
  "total_checks": 50,
  "connections_processed": 2
}
```

## 🎯 Usage Examples

### View Current Recommendations
- Navigate to `/recommendations` - shows latest version only

### View Historical Data
1. Dashboard → "History" button → `/archived-versions`
2. Select version → `/archived-recommendations/2` → View v2 data

### Sync New Data
1. Click "Sync" → Archives current data → Creates new version
2. Notification: "✅ Sync completed! 45 recommendations synced (v3). 42 previous recommendations archived."

## 🔍 Data Structure

### Active Recommendation
```json
{
  "_id": "...",
  "user_id": "user123",
  "check_id": "check456",
  "name": "Security Group Rules",
  "version": 3,
  "created_at": "2025-10-19T13:00:00Z"
}
```

### Archived Recommendation
```json
{
  "_id": "...",
  "user_id": "user123", 
  "check_id": "check456",
  "name": "Security Group Rules",
  "version": 2,
  "created_at": "2025-10-18T10:00:00Z",
  "archived_at": "2025-10-19T13:00:00Z",
  "is_archived": true
}
```

## ✅ Testing Status
- ✅ Archive system working
- ✅ Version increment working  
- ✅ UI routes accessible (with auth)
- ✅ Templates rendering correctly
- ✅ No duplicates in active collection
- ✅ Historical data preserved
