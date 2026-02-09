"""Shared test fixtures for the AWS Exam Simulator test suite."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


# --- Sample question data (both formats) ---

SAMPLE_QUESTIONS_SAA = [
    {
        "question": "A company needs a storage solution for frequently accessed data with the lowest cost. Which S3 storage class should they use?",
        "options": [
            "A. S3 Standard",
            "B. S3 Intelligent-Tiering",
            "C. S3 Standard-IA",
            "D. S3 Glacier",
        ],
        "correct": "A. S3 Standard",
        "explanation": "S3 Standard is designed for frequently accessed data and provides low latency and high throughput.",
        "references": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html",
    },
    {
        "question": "Which AWS service provides a managed Kubernetes control plane?",
        "options": [
            "A. Amazon ECS",
            "B. Amazon EKS",
            "C. AWS Fargate",
            "D. AWS Lambda",
        ],
        "correct": "B. Amazon EKS",
        "explanation": "Amazon EKS (Elastic Kubernetes Service) provides a managed Kubernetes control plane.",
        "references": "https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html",
    },
    {
        "question": "A Solutions Architect needs to encrypt data at rest in an RDS database. Which service manages the encryption keys?",
        "options": [
            "A. AWS CloudHSM",
            "B. AWS KMS",
            "C. AWS Secrets Manager",
            "D. AWS Certificate Manager",
        ],
        "correct": "B. AWS KMS",
        "explanation": "AWS KMS (Key Management Service) manages encryption keys for RDS encryption at rest.",
        "references": "https://docs.aws.amazon.com/kms/latest/developerguide/overview.html",
    },
    {
        "question": "Which service provides DDoS protection for AWS resources?",
        "options": [
            "A. AWS WAF",
            "B. AWS Shield",
            "C. Amazon GuardDuty",
            "D. AWS Inspector",
        ],
        "correct": "B. AWS Shield",
        "explanation": "AWS Shield provides DDoS protection. Shield Standard is automatic, Shield Advanced provides enhanced protection.",
        "references": "",
    },
    {
        "question": "A company uses CloudWatch to monitor EC2 instances. What is the default metric collection interval?",
        "options": [
            "A. 1 minute",
            "B. 5 minutes",
            "C. 10 minutes",
            "D. 15 minutes",
        ],
        "correct": "B. 5 minutes",
        "explanation": "CloudWatch basic monitoring collects metrics every 5 minutes. Detailed monitoring provides 1-minute intervals.",
        "references": "",
    },
]

SAMPLE_QUESTIONS_CLF = [
    {
        "question": "Which AWS service allows users to manage resources through a web interface?",
        "options": [
            "AWS CLI",
            "AWS API",
            "AWS SDK",
            "AWS Management Console",
        ],
        "correct": "AWS Management Console",
    },
    {
        "question": "What is an example of horizontal scaling in AWS?",
        "options": [
            "Replacing an EC2 instance with a larger one",
            "Adding more RAM to an EC2 instance",
            "Adding more EC2 instances to handle traffic",
            "Upgrading to a faster EBS volume",
        ],
        "correct": "Adding more EC2 instances to handle traffic",
    },
    {
        "question": "Which service helps determine who terminated EC2 instances?",
        "options": [
            "Amazon Inspector",
            "AWS CloudTrail",
            "AWS Trusted Advisor",
            "EC2 Instance Usage Report",
        ],
        "correct": "AWS CloudTrail",
    },
]


@pytest.fixture
def question_dir(tmp_path: Path) -> Path:
    """Create a temporary question directory with sample data."""
    qdir = tmp_path / "questions"
    qdir.mkdir()

    # Write SAA-style questions
    (qdir / "SAA-C03-test.json").write_text(
        json.dumps(SAMPLE_QUESTIONS_SAA), encoding="utf-8"
    )

    # Write CLF-style questions
    (qdir / "CLF-C02-test.json").write_text(
        json.dumps(SAMPLE_QUESTIONS_CLF), encoding="utf-8"
    )

    return qdir


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Create a temporary database path."""
    return tmp_path / "state" / "test.sqlite"
