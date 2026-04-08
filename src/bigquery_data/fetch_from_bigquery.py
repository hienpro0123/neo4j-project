import os

from google.cloud import bigquery

DATASET = "bigquery-public-data.thelook_ecommerce"

PURCHASES_QUERY = f"""
SELECT DISTINCT
    CAST(o.user_id AS STRING) AS user_id,
    u.first_name AS first_name,
    u.last_name AS last_name,
    CAST(p.id AS STRING) AS product_id,
    p.name AS product_name,
    p.category AS category_name
FROM `{DATASET}.orders` AS o
JOIN `{DATASET}.order_items` AS oi
    ON oi.order_id = o.order_id
JOIN `{DATASET}.users` AS u
    ON u.id = o.user_id
JOIN `{DATASET}.products` AS p
    ON p.id = oi.product_id
WHERE o.user_id IS NOT NULL
  AND p.id IS NOT NULL
  AND p.name IS NOT NULL
  AND p.category IS NOT NULL
ORDER BY user_id, product_id
"""


def get_bigquery_client(project_id=None):
    resolved_project = (
        project_id
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCLOUD_PROJECT")
    )
    return bigquery.Client(project=resolved_project) if resolved_project else bigquery.Client()


def fetch_purchase_rows(project_id=None, limit=None):
    query = PURCHASES_QUERY
    if limit is not None:
        query = f"{query}\nLIMIT {int(limit)}"

    return get_bigquery_client(project_id=project_id).query(query).result()
