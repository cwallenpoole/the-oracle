# Vision Images Implementation

This document outlines the implementation of LLM-powered vision image generation for flame readings in The Oracle application.

## Overview

The vision images feature analyzes flame reading text to extract mystical visions (like "Luminous Butterfly", "Whispering Leaf", etc.) and generates artistic line drawings using OpenAI's DALL-E 3 to visualize what the mystic might have seen in the flames.

## Architecture

### 1. Database Schema Updates

**New Column: `vision_images`**
- Added to `history` table
- Stores JSON array of vision image metadata
- Format: `[{"vision": "Luminous Butterfly", "url": "/static/vision-images/username/file.png", "filename": "file.png"}]`

### 2. Backend Components

#### API Endpoints (`routes/api.py`)

**`POST /api/generate-vision-images`**
- Accepts: `reading_id`, `fire_image_filename`, `visions[]`
- Starts async vision generation process
- Returns: `generation_id` for status tracking

**`GET /api/vision-images-status/<generation_id>`**
- Checks generation progress
- Returns: completed images with URLs

#### Core Functions

**`_extract_visions_from_text(reading_text)`**
- Uses regex patterns to find vision descriptions
- Patterns include: "saw X", "vision of X", "X appears", etc.
- Returns up to 5 unique visions

**`_generate_vision_images_async()`**
- Runs in background thread
- Generates images using OpenAI DALL-E 3
- Saves images to `static/vision-images/{username}/`
- Updates database with vision image URLs

### 3. Model Updates (`models/history.py`)

**New Properties & Methods:**
- `vision_images_list`: Property to get vision images as list
- `set_vision_images()`: Store vision images JSON
- `add_vision_image()`: Add single vision image
- Updated constructor and database operations

### 4. Frontend Integration

**Template Updates (`flame_reading_detail.html`):**
- Vision Images section with generate button
- Displays existing stored images
- Loading states and progress indicators
- Responsive grid layout for vision images

**JavaScript Features:**
- Vision extraction from reading content
- AJAX requests for generation and status
- Async polling for completion status
- Dynamic UI updates and error handling

## Workflow

### 1. Vision Generation Process
```
User clicks "Generate Vision Images"
    ↓
Frontend extracts visions from reading text
    ↓
AJAX POST to /api/generate-vision-images
    ↓
Backend starts async thread with OpenAI DALL-E
    ↓
Frontend polls /api/vision-images-status
    ↓
Images appear as they're generated
    ↓
Database updated with vision image URLs
```

### 2. Image Storage Structure
```
static/vision-images/
├── username1/
│   ├── visions_reading123_20250123_143022_Luminous_Butterfly.png
│   ├── visions_reading123_20250123_143022_Whispering_Leaf.png
│   └── ...
└── username2/
    └── ...
```

### 3. Database Storage
```json
{
  "vision_images": [
    {
      "vision": "Luminous Butterfly",
      "url": "/static/vision-images/username/file.png",
      "filename": "visions_reading123_20250123_143022_Luminous_Butterfly.png"
    }
  ]
}
```

## Features

### 1. Vision Extraction
- **Regex Patterns**: Identifies common mystical vision descriptions
- **Intelligent Filtering**: Removes common words and duplicates
- **Limit Control**: Maximum 5 visions per reading
- **Case Sensitivity**: Looks for properly capitalized phrases

### 2. Image Generation
- **OpenAI DALL-E 3**: High-quality image generation
- **Consistent Style**: "Simple, elegant line drawing in black ink on white background"
- **Mystical Prompt**: "A mystic recently saw {vision} in mystical flames"
- **Error Handling**: Continues if individual images fail

### 3. Async Processing
- **Background Threads**: Non-blocking generation
- **Status Polling**: Real-time progress updates
- **Timeout Handling**: Graceful handling of long generation times
- **Concurrent Safety**: Thread-safe database updates

### 4. Persistent Storage
- **Database Integration**: Vision images stored with readings
- **File Management**: Organized directory structure
- **URL Generation**: Server-provided URLs for images
- **Regeneration Support**: Can regenerate existing vision images

## User Experience

### 1. Initial State
- Placeholder with description of feature
- Single "Generate Vision Images" button
- Clear explanation of what will happen

### 2. Generation Process
- Loading spinner with progress text
- Shows discovered visions: "Found 3 visions: Luminous Butterfly, Whispering Leaf, Twisting Serpent"
- Polls every 3 seconds for updates

### 3. Completed State
- Grid layout displaying all generated images
- Hover effects and smooth transitions
- "Regenerate Vision Images" button for new versions
- Images persist across page reloads

### 4. Error Handling
- Clear error messages for network issues
- Fallback for vision extraction failures
- Graceful degradation if OpenAI API unavailable

## Configuration Requirements

### 1. Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here
```

### 2. Dependencies
```python
openai>=1.0.0
threading  # Built-in
urllib.request  # Built-in
re  # Built-in
```

### 3. Directory Structure
```
static/
├── vision-images/     # Auto-created
├── fire-captures/     # Existing
└── ...
```

## Security Considerations

### 1. Authentication
- Requires user login for API access
- User-specific image directories
- Reading ownership validation

### 2. File Security
- Images stored in user-specific subdirectories
- Sanitized filenames (alphanumeric only)
- No direct file system access from frontend

### 3. API Rate Limiting
- OpenAI API has built-in rate limits
- Thread-based processing prevents blocking
- Error handling for quota exceeded

## Performance Optimizations

### 1. Async Processing
- Background thread generation
- Non-blocking user experience
- Status polling instead of long requests

### 2. Efficient Storage
- JSON metadata in database
- File-based image storage
- URL-based image serving

### 3. Frontend Optimizations
- Lazy loading for images
- Responsive image sizing
- Caching of generated content

## Testing

### Test Script: `test_vision_images.py`
- Vision extraction testing
- API endpoint validation
- Status polling verification
- Error scenario testing

### Manual Testing Checklist
- [ ] Generate vision images for new reading
- [ ] Verify images persist after page reload
- [ ] Test regeneration functionality
- [ ] Validate error handling
- [ ] Check responsive design

## Future Enhancements

### 1. Image Quality
- Support for different art styles
- Size/resolution options
- Custom prompts from users

### 2. Performance
- Image optimization/compression
- CDN integration for image serving
- Batch processing for multiple readings

### 3. User Experience
- Image gallery view
- Download/sharing options
- Social media integration

### 4. Advanced Features
- AI-powered vision enhancement
- Custom vision descriptions
- Integration with original fire images

## Troubleshooting

### Common Issues

**"No clear visions found"**
- Reading text may not contain recognizable vision patterns
- Add more descriptive mystical content to readings

**"Generation taking longer than expected"**
- OpenAI API can be slow during high usage
- Images generate one at a time, wait for completion

**Images not displaying**
- Check file permissions on `static/vision-images/`
- Verify database connection and vision_images column

**API errors**
- Ensure OpenAI API key is configured
- Check API quota and billing status
- Verify user authentication

## Implementation Notes

- Vision images are optional and don't affect core reading functionality
- System gracefully degrades if OpenAI API is unavailable
- All vision images are stored permanently unless manually deleted
- Regeneration replaces existing images but keeps the same visions
- Database migration automatically adds vision_images column to existing installations
