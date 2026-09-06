$folder = "d:\Develop\Projects\T004\Minifantasy"
$files = Get-ChildItem -Path $folder -Recurse -File | Where-Object { $_.Extension -match '\.(png|jpg|jpeg|gif|bmp)$' }
$count = 0
foreach ($file in $files) {
    $newName = $file.Name.ToLower() -replace ' ', '_' -replace '[^a-z0-9_.-]', ''
    
    # -cne is case-sensitive not-equal
    if ($file.Name -cne $newName) {
        $tempName = "$newName.tmp"
        $tempPath = Join-Path $file.Directory.FullName $tempName
        $finalPath = Join-Path $file.Directory.FullName $newName
        
        $conflict = $false
        # If the name change is more than just case, we must check if finalPath exists
        if ($file.Name.ToLower() -ne $newName.ToLower()) {
            if (Test-Path -LiteralPath $finalPath) {
                $conflict = $true
            }
        }
        
        if ($conflict) {
            Write-Host "Conflict for $($file.FullName), $newName already exists"
        } else {
            Rename-Item -LiteralPath $file.FullName -NewName $tempName
            Rename-Item -LiteralPath $tempPath -NewName $newName
            $count++
        }
    }
}
Write-Host "Done. Renamed $count files."
