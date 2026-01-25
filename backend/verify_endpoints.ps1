$ErrorActionPreference = "Stop"

function Test-Endpoint {
    param (
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    Write-Host "Testing $Method $Url ..." -NoNewline
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            UseBasicParsing = $true
        }
        if ($Body) { $params.Body = $Body; $params.ContentType = "application/x-www-form-urlencoded" }
        
        $response = Invoke-WebRequest @params
        Write-Host " OK ($($response.StatusCode))" -ForegroundColor Green
        return $response
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader $_.Exception.Response.GetResponseStream()
            Write-Host $reader.ReadToEnd() -ForegroundColor Yellow
        }
        return $null
    }
}

# 1. Login
$baseUrl = "http://localhost:8000/api/v1"
$loginRes = Test-Endpoint -Url "$baseUrl/auth/login" -Method "POST" -Body "username=admin@example.com&password=admin"

if (-not $loginRes) { exit }

$tokenObj = $loginRes.Content | ConvertFrom-Json
$token = $tokenObj.access_token
$headers = @{ Authorization = "Bearer $token" }

Write-Host "`nLogged in successfully. Token obtained.`n"

# 2. Check Me
Test-Endpoint -Url "$baseUrl/auth/me" -Headers $headers

# 3. Check Admin Endpoints
Test-Endpoint -Url "$baseUrl/admin/vendors" -Headers $headers
Test-Endpoint -Url "$baseUrl/admin/categories" -Headers $headers
Test-Endpoint -Url "$baseUrl/admin/regions" -Headers $headers
Test-Endpoint -Url "$baseUrl/admin/admins" -Headers $headers

Write-Host "`nVerification Complete."
