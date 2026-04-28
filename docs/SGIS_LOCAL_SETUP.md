# SGIS Local Setup

Use this flow to test SGIS locally without exposing the SGIS secret in browser code.

## 1. Fill the local env file

Edit:

- [sgis-local-env.ps1](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/apps/school-neighborhood-gis/scripts/sgis-local-env.ps1)

Set the values:

```powershell
$env:SGIS_CONSUMER_KEY = "your_service_id"
$env:SGIS_CONSUMER_SECRET = "your_secret_key"
```

## 2. Verify SGIS access

Run:

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\apps\school-neighborhood-gis"
powershell -ExecutionPolicy Bypass -File .\scripts\check-sgis-local.ps1
```

If the setup is correct, the script should print:

- `year`
- `admCd`
- `lowSearch`
- `boundaries`
- `statsRows`

## 3. Start the local app

Run:

```powershell
cd "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\apps\school-neighborhood-gis"
powershell -ExecutionPolicy Bypass -File .\scripts\start-local-server.ps1
```

Important:

- The script now auto-selects the next free port if `8787` is already in use.
- Always use the exact URL printed by the script.

Example:

- `http://127.0.0.1:8787/`
- or `http://127.0.0.1:8792/`

## 4. How the local proxy works

- The browser calls `/api/sgis/population`
- The local proxy requests an SGIS access token
- The local proxy calls SGIS boundary and population endpoints
- The proxy returns a merged layer payload to the browser

## 5. Security rule

- Never put `SGIS_CONSUMER_SECRET` into frontend files such as `runtime-config.js`
- Keep the secret in the local env script or server environment variables only
