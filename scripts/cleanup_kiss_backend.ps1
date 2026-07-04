# Run from repository root after extracting this patch.
# Removes old layered backend folders and JWT debug files from the prototype.
$paths = @(
  "api\models",
  "api\repositories",
  "api\services",
  "api\shared",
  "api\tests",
  "debug_jwt_local.py"
)
foreach ($p in $paths) {
  if (Test-Path $p) { Remove-Item $p -Recurse -Force }
}
New-Item -ItemType Directory -Force -Path "api\tests" | Out-Null
@'
def test_function_app_imports():
    import function_app
    assert function_app.app is not None
'@ | Set-Content "api\tests\test_function_app_import.py"
Write-Host "KISS cleanup completed."
