# Sentinel

Sentinel is an AWS account auditor. It scans your AWS account on a schedule or on demand. It checks each resource against a set of rules and reports anything that looks wrong. Findings go to Slack and into GitHub Issues so you actually do something about them.

The kind of things it checks for:

- S3 buckets that are public when they shouldn't be
- S3 buckets without encryption
- IAM users without MFA
- Security groups with `0.0.0.0/0` open on sensitive ports (22, 3389, 3306, 5432)
- Root account access keys
- EBS volumes nobody is using
- EC2 instances that have been stopped for more than 30 days
- Resources missing the tags the team agreed on

This is the kind of tool that already exists at the enterprise level (AWS Config, AWS Security Hub, Wiz, Steampipe, Cloud Custodian). Sentinel is the small self-hosted version.

## Status

Just scaffolded. Branch protection on `main`, CI on every PR, Issues open with the work to do. No scanning logic yet.

## Why I'm building this

I'm moving into DevOps and cloud engineering, and small projects help me practice and have some fun.

My previous repo (`server-health-monitor`) is where I practiced some bash and played around with GitHub and git workflows I'd used before. I shipped it without tests or CI, which wasn't great. That's not how real teams ship code. So I decided to jump to a more complete project, not just bash scripting. Sentinel starts with the proper foundation in commit zero so I don't repeat that.

## Stack

- Python 3.12 and FastAPI for the service and REST API
- boto3 for AWS SDK
- PostgreSQL for storing scan results
- Redis for the scan queue (later phase)
- LocalStack and moto for AWS mocking in tests
- pytest for tests
- Docker for packaging
- Terraform for infrastructure
- GitHub Actions for CI

## Getting started

Will be added once there is something to run.

## Architecture

See `docs/ARCHITECTURE.md` once it lands.

## License

MIT. See `LICENSE`.