# Run this in PowerShell as Administrator
# Right-click PowerShell and select "Run as administrator"
netsh advfirewall firewall add rule name="WSL Backend 8000" dir=in action=allow protocol=TCP localport=8000 profile=private,domain
Write-Host "Done! Firewall rule added for port 8000."
