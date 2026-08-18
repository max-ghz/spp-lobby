import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    # proxy_headers=False: uvicorn otherwise trusts X-Forwarded-For from
    # 127.0.0.1 by default, letting a client spoof its registered IP
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, proxy_headers=False)
