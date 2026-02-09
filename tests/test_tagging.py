"""Tests for the auto-tagging engine."""
from __future__ import annotations

from mcp_server.src.aws_exam_tools.tagging import infer_tags


class TestTagging:
    """Test tag inference from question text."""

    def test_s3_question(self) -> None:
        tags = infer_tags("Which S3 storage class should you use for frequently accessed data in a bucket?")
        assert "s3_storage" in tags

    def test_iam_question(self) -> None:
        tags = infer_tags("A company needs to manage IAM roles and permissions for developers.")
        assert "iam" in tags

    def test_vpc_question(self) -> None:
        tags = infer_tags("Configure a VPC with public and private subnets and a NAT gateway.")
        assert "vpc_networking" in tags

    def test_ec2_question(self) -> None:
        tags = infer_tags("Launch an EC2 instance with an Auto Scaling group behind an ALB.")
        assert "ec2_compute" in tags

    def test_lambda_question(self) -> None:
        tags = infer_tags("Deploy a serverless application using AWS Lambda and API Gateway.")
        assert "serverless" in tags

    def test_rds_question(self) -> None:
        tags = infer_tags("Set up an RDS Aurora database with read replicas.")
        assert "databases" in tags

    def test_cloudwatch_question(self) -> None:
        tags = infer_tags("Set up CloudWatch alarms to monitor EC2 metrics and send SNS notifications.")
        assert "monitoring_logging" in tags

    def test_kms_question(self) -> None:
        tags = infer_tags("Use KMS to encrypt data at rest with customer managed keys.")
        assert "security_encryption" in tags

    def test_cost_question(self) -> None:
        tags = infer_tags("Use AWS Budgets to track billing costs and set up alerts.")
        assert "cost_optimization" in tags

    def test_ml_question(self) -> None:
        tags = infer_tags("Train a machine learning model using Amazon SageMaker.")
        assert "ml_ai" in tags

    def test_multiple_tags(self) -> None:
        tags = infer_tags("Configure IAM roles for Lambda functions accessing S3 buckets.")
        assert "iam" in tags
        assert "serverless" in tags
        assert "s3_storage" in tags

    def test_general_fallback(self) -> None:
        tags = infer_tags("What is the best practice for this scenario?")
        assert "general" in tags

    def test_empty_text(self) -> None:
        tags = infer_tags("")
        assert "general" in tags

    def test_tags_are_sorted(self) -> None:
        tags = infer_tags("Use IAM roles with S3 bucket policies for VPC endpoints.")
        assert tags == sorted(tags)

    def test_tags_are_unique(self) -> None:
        tags = infer_tags("S3 bucket in S3 with S3 lifecycle")
        assert len(tags) == len(set(tags))
