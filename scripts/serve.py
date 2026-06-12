#!/usr/bin/env python3
""""Start the fu7ur3pr00f API server"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "fu7ur3pr00f.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )