foreach ($h in @('C:\Users\x\AppData\Local\Temp\Temp1_VoiceTwin.zip\VoiceTwin', 'C:\Users\x\AppData\Local\Temp\Rar$EXa123\VoiceTwin', 'D:\Temp\VoiceTwin', 'D:\VoiceTwin', 'E:\x\Temp2_VoiceTwin-v0.1.6.zip', 'D:\7zip\VoiceTwin')) {
  $hit = ($h -match '\\AppData\\Local\\Temp\\' -or $h -match '\\Temp\d+_[^\\]*\.zip(\\|$)')
  Write-Host "$hit  $h"
}
