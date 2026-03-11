# Local Image Storage Setup Plan (Hybrid Approach)

This document outlines the finalized plan for migrating room images from Google Drive to a high-performance local storage solution.

## Architecture: The "Gold Standard"
**Cloudflare -> Nginx (Proxy) -> FastAPI -> Local Disk**

1.  **Storage**: Images are stored on the Droplet's SSD in `/var/www/tatoh/images/`.
2.  **Delivery**: Nginx serves the images directly from disk (fast).
3.  **Caching**: Cloudflare automatically caches these images globally ($0 cost).
4.  **Application**: AI Agent tools return direct URLs (e.g., `https://tatohseaview.com/images/room1.jpg`).

## Technical Trade-offs
- **Cost**: $0 extra (uses existing Droplet resources).
- **Security**: Directory listing will be disabled; access is via direct URL only.
- **Performance**: Cloudflare "Edge" caching ensures fast global loading.
- **Isolation**: Nginx handles image traffic, so the FastAPI AI Agent doesn't slow down.

## Implementation Steps

### 1. FastAPI Setup
Mount the static directory in `api/main.py`:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/images", StaticFiles(directory="/var/www/tatoh/images"), name="images")
```

### 2. Tool Update
Update `get_room_gallery.py` to return local URLs instead of Google Drive links.

### 3. Server Configuration (Production)
Set up Nginx to handle `/images` requests:
```nginx
location /images/ {
    alias /var/www/tatoh/images/;
    expires 30d;
    add_header Cache-Control "public, no-transform";
}
```

## Conclusion
This Hybrid approach provides S3-level performance and reliability without the monthly subscription costs, utilizing the infrastructure you already have in place.
