#!/usr/bin/env python3
""""Start the fu7ur3pr00f API server"""

from fu7ur3pr00f.api.config import settings
import uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "fu7ur3pr00f.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )