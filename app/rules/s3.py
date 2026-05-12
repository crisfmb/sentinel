def find_public_s3_buckets(s3_client) -> list[str]:
    public_buckets = []
    response = s3_client.list_buckets()
    for bucket in response.get("Buckets", []):
        name = bucket.get("Name")
        creation_date = bucket.get("CreationDate")

    return public_buckets
