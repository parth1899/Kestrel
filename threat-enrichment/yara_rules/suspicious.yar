rule PowerShell_ScriptPolicyTest {
    meta:
        description = "Detects PowerShell Script Policy Test files"
        author = "NXTGEN"
    strings:
        $ps1 = /__PSScriptPolicyTest_.*\.ps1/
        $psm1 = /__PSScriptPolicyTest_.*\.psm1/
    condition:
        $ps1 or $psm1
}

rule Suspicious_Hash_Prefix {
    meta:
        description = "Detects fake hash prefix used in testing"
    strings:
        $hash = /hash___PSScriptPolicyTest_/
    condition:
        $hash
}