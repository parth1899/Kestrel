rule PowerShell_Suspicious_Temp_File {
    meta:
        description = "Detects suspicious PowerShell files in temp directories"
        author = "NXTGEN EDR"
        threat_level = "medium"
    strings:
        $ps1_temp = /\\Temp\\.*\.ps1/i
        $psm1_temp = /\\Temp\\.*\.psm1/i
        $pss_prefix = "__PSScriptPolicyTest_"
    condition:
        $pss_prefix or $ps1_temp or $psm1_temp
}

rule Atomic_Red_Team_Artifact {
    meta:
        description = "Detects Atomic Red Team test files/artifacts"
        author = "NXTGEN EDR"
        threat_level = "high"
    strings:
        $art_ps1 = "atomic-red-team" nocase
        $art_exe = /T\d{4}\.exe/  // e.g., T1003.exe from ART
        $art_path = /\\atomic-red-team\\/i
    condition:
        $art_ps1 or $art_exe or $art_path
}

rule Suspicious_File_Extension {
    meta:
        description = "Detects ransomware-like or suspicious file extensions"
        author = "NXTGEN EDR"
        threat_level = "high"
    strings:
        $ransom_ext = /\.(locked|encrypted|wannacry|locky)$/i
        $mal_exe = /\\AppData\\.*\.exe/i  // Suspicious exe in user data
    condition:
        $ransom_ext or $mal_exe
}

rule Known_Malware_FileName {
    meta:
        description = "Detects known malware filenames"
        author = "NXTGEN EDR"
        threat_level = "critical"
    strings:
        $mal_names = / (ransom|malware|trojan|virus|backdoor|keylogger)\./i
    condition:
        $mal_names
}

rule PowerShell_Suspicious_Temp_Execution {
    meta:
        description = "Detects PowerShell scripts executed from Temp/User directories"
        author = "NXTGEN EDR"
        threat_level = "high"
    strings:
        $ps_temp = /\\(Temp|AppData\\Local\\Temp)\\.*\.ps1?$/i
        $ps_user = /\\Users\\.*\\AppData\\.*\.ps1?$/i
    condition:
        any of them
}

rule Suspicious_Executable_In_UserDir {
    meta:
        description = "Detects .exe in user-writable directories"
        author = "NXTGEN EDR"
        threat_level = "medium"
    strings:
        $exe_user = /\\(Users|Documents|Downloads|AppData)\\.*\.exe$/i
    condition:
        $exe_user
}

rule Obfuscated_PowerShell {
    meta:
        description = "Detects common PowerShell obfuscation patterns"
        author = "NXTGEN EDR"
        threat_level = "high"
    strings:
        $enc = "-enc" nocase
        $b64 = /[A-Za-z0-9+\/]{50,}=/  // Long base64
        $invoke = "IEX" nocase
        $download = "Net.WebClient" nocase
    condition:
        all of ($enc, $b64) or ($invoke and $download)
}

rule Ransomware_Extension {
    meta:
        description = "Detects known ransomware file extensions"
        author = "NXTGEN EDR"
        threat_level = "critical"
    strings:
        $ext = /\.(locky|crypt|locked|cerber|wannacry|ryuk)$/i
    condition:
        $ext
}