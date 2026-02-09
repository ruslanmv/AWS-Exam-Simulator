"""Auto-tagging engine for AWS exam questions.

Tags questions based on keyword patterns. This enables:
- Adaptive question selection (focus on weak areas)
- Spaced repetition (revisit missed domains)
- Progress analytics per AWS domain
"""
from __future__ import annotations

import re

# (tag, patterns) - first match wins for each tag
TAG_RULES: list[tuple[str, list[str]]] = [
    # AWS Core Services
    ("iam", [
        r"\bIAM\b", r"\bpolicy\b", r"\brole\b", r"\bpermission\b",
        r"\bSTS\b", r"\bfederat", r"\bidentity\b", r"\baccess control\b",
        r"\bcredential\b", r"\bMFA\b", r"\bActive Directory\b",
    ]),
    ("vpc_networking", [
        r"\bVPC\b", r"\bsubnet\b", r"\brout(e|ing)\b", r"\bNACL\b",
        r"\bsecurity group\b", r"\bVPN\b", r"\bDirect Connect\b",
        r"\bTransit Gateway\b", r"\bENI\b", r"\bElastic IP\b",
        r"\bpeering\b", r"\bPrivateLink\b", r"\bNetwork Load\b",
    ]),
    ("s3_storage", [
        r"\bS3\b", r"\bbucket\b", r"\bobject storage\b", r"\blifecycle\b",
        r"\bGlacier\b", r"\bversioning\b", r"\bpre-signed\b",
        r"\bstorage class\b", r"\bcross-region replication\b",
    ]),
    ("ec2_compute", [
        r"\bEC2\b", r"\bAMI\b", r"\bAuto Scaling\b", r"\bELB\b",
        r"\bALB\b", r"\bNLB\b", r"\binstance\b", r"\bplacement group\b",
        r"\bspot\b", r"\breserved\b", r"\bdedicated\b", r"\bEBS\b",
    ]),
    ("serverless", [
        r"\bLambda\b", r"\bAPI Gateway\b", r"\bStep Functions\b",
        r"\bserverless\b", r"\bFargate\b", r"\bSAM\b",
    ]),
    ("containers", [
        r"\bECS\b", r"\bEKS\b", r"\bDocker\b", r"\bcontainer\b",
        r"\bKubernetes\b", r"\bECR\b",
    ]),
    ("databases", [
        r"\bRDS\b", r"\bDynamoDB\b", r"\bAurora\b", r"\bElastiCache\b",
        r"\bRedshift\b", r"\bNeptune\b", r"\bDocumentDB\b",
        r"\bdatabase\b", r"\bMySQL\b", r"\bPostgre\b",
    ]),
    ("monitoring_logging", [
        r"\bCloudWatch\b", r"\bCloudTrail\b", r"\bX-Ray\b",
        r"\blog(s|ging)\b", r"\bmetric\b", r"\balarm\b", r"\bSNS\b",
    ]),
    ("security_encryption", [
        r"\bencrypt\b", r"\bKMS\b", r"\bHSM\b", r"\bTLS\b",
        r"\bSSL\b", r"\bsecret\b", r"\bWAF\b", r"\bShield\b",
        r"\bGuardDuty\b", r"\bInspector\b", r"\bMacie\b",
    ]),
    ("high_availability", [
        r"\bhigh availability\b", r"\bfailover\b", r"\bmulti-AZ\b",
        r"\brecovery\b", r"\bRPO\b", r"\bRTO\b", r"\bresilien\b",
        r"\bbackup\b", r"\bdisaster\b",
    ]),
    ("cost_optimization", [
        r"\bbilling\b", r"\bcost\b", r"\bBudgets\b", r"\bSupport Plan\b",
        r"\bpricing\b", r"\bfree tier\b", r"\bCost Explorer\b",
        r"\bSavings Plan\b", r"\bReserved\b",
    ]),
    ("devops_cicd", [
        r"\bCodePipeline\b", r"\bCodeBuild\b", r"\bCodeDeploy\b",
        r"\bCodeCommit\b", r"\bCI/CD\b", r"\bCloudFormation\b",
        r"\bCDK\b", r"\bTerraform\b", r"\bElastic Beanstalk\b",
    ]),
    ("ml_ai", [
        r"\bSageMaker\b", r"\bmachine learning\b", r"\bML\b",
        r"\bdeep learning\b", r"\bRekognition\b", r"\bComprehend\b",
        r"\bPolly\b", r"\bLex\b", r"\bTranscribe\b", r"\bTranslate\b",
        r"\bPersonalize\b", r"\bForecast\b", r"\bTextract\b",
    ]),
    ("messaging_integration", [
        r"\bSQS\b", r"\bSNS\b", r"\bKinesis\b", r"\bEventBridge\b",
        r"\bqueue\b", r"\bstream\b", r"\bmessag\b",
    ]),
    ("content_delivery", [
        r"\bCloudFront\b", r"\bCDN\b", r"\bRoute\s*53\b",
        r"\bDNS\b", r"\bedge\b", r"\bglobal accelerator\b",
    ]),
    ("analytics", [
        r"\bAthena\b", r"\bGlue\b", r"\bEMR\b", r"\bQuickSight\b",
        r"\bdata lake\b", r"\banalytic\b", r"\bRedshift\b",
    ]),
    ("migration", [
        r"\bmigrat\b", r"\bSnowball\b", r"\bDMS\b", r"\bSMS\b",
        r"\bTransfer Family\b", r"\bDataSync\b",
    ]),
]


def infer_tags(text: str) -> list[str]:
    """Infer domain tags from question text using keyword patterns."""
    tags: list[str] = []

    for tag, patterns in TAG_RULES:
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                tags.append(tag)
                break  # one match per tag is enough

    if not tags:
        tags.append("general")

    return sorted(set(tags))
