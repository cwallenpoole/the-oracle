# Pyromancy AJAX Implementation

This document outlines the changes made to implement AJAX-based fire image handling for the pyromancy feature.

## Overview

Previously, fire images were captured and submitted inline with the form. Now, images are captured, sent to the server via AJAX, stored on the server, and the server-provided URL is used for display and processing.

## Changes Made

### 1. Frontend JavaScript Changes (`templates/pyromancy.html`)

#### Modified Functions:
- **`captureFireImage()`**: Now sends captured images to the server via AJAX instead of storing them locally
- **`displayCapturedImageFromServer()`**: New function to display images using server-provided URLs
- **Form submission handler**: Updated to use server-stored filenames instead of re-capturing images

#### Key Features:
- Sends cropped fire images to `/api/save-fire-image` endpoint
- Receives server response with image URL and filename
- Updates preview with server-hosted image
- Stores filename in form field for submission

### 2. Backend API Changes (`routes/api.py`)

#### Enhanced `/api/save-fire-image` Endpoint:
- Accepts base64 image data via JSON POST
- Saves images to `static/fire-captures/` directory
- Generates unique filenames with timestamp and username
- Returns structured response with:
  - `image_url`: Server URL for the saved image
  - `filename`: Generated filename for reference
  - `filepath`: Server-side file path
  - `success`: Boolean status flag

### 3. Pyromancy Reading Handler (`routes/readings.py`)

#### Refactored `pyromancy_reading()` Function:
- **Helper Functions**: Split complex logic into focused helper functions:
  - `_load_fire_image()`: Handles loading from server storage or base64
  - `_save_fire_image_for_reading()`: Manages final image naming and storage
- **Dual Support**: Handles both server-stored filenames and base64 data (fallback)
- **Improved Error Handling**: Better error messages and logging
- **Code Quality**: Reduced cognitive complexity and eliminated duplicate constants

## Workflow

### 1. Image Capture
```javascript
// User clicks fire canvas or capture button
captureFireImage() →
  AJAX POST to /api/save-fire-image →
  Server saves image and returns URL →
  Update preview with server URL
```

### 2. Form Submission
```javascript
// User submits form
Form submission →
  Check for server-stored filename →
  Submit form with filename reference
```

### 3. Reading Generation
```python
# Server processes reading
pyromancy_reading() →
  Load image from server storage →
  Analyze with AI →
  Generate reading →
  Rename image to final reading ID
```

## Benefits

1. **Performance**: Images are only uploaded once via AJAX
2. **Reliability**: Server-stored images prevent data loss during form submission
3. **User Experience**: Immediate feedback when images are captured
4. **Maintainability**: Cleaner separation of concerns between frontend and backend
5. **Debugging**: Better logging and error handling throughout the process

## File Structure

```
static/fire-captures/
├── fire_username_20250123_143022_123.png  # Temporary captured images
└── fire_reading_id.png                    # Final reading images
```

## Testing

Use the provided test script to verify the API:
```bash
python test_fire_api.py
```

## Error Handling

- **Missing Images**: Clear error messages when server-stored images are not found
- **Network Issues**: Graceful fallback to base64 submission
- **File System**: Proper directory creation and permissions handling
- **User Feedback**: Status messages for successful captures and errors

## Security Considerations

- **File Types**: Only PNG and JPG files are accepted
- **User Authentication**: Images are associated with logged-in users
- **File Naming**: Unique timestamps prevent filename collisions
- **Directory Isolation**: Images stored in designated directory

## Future Enhancements

- Image compression for bandwidth optimization
- Thumbnail generation for faster loading
- Automatic cleanup of old temporary images
- Support for multiple image formats
- Progressive image upload with progress indicators
