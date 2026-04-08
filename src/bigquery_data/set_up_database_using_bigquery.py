import os

from src.bigquery_data.fetch_from_bigquery import fetch_purchase_rows
from src.database.database_setup import DatabaseSetup


def import_data_and_enter_into_database(project_id=None, limit=None, clear_existing=True):
    db_setup = DatabaseSetup()

    if clear_existing:
        db_setup.clear_database()
    db_setup.create_constraints()

    rows = fetch_purchase_rows(project_id=project_id, limit=limit)

    with db_setup.driver.session(database=db_setup.database) as session:
        for row in rows:
            session.run(
                """
                MERGE (u:User {id: $user_id})
                SET u.firstname = $first_name,
                    u.lastname = $last_name,
                    u.name = trim($first_name + ' ' + $last_name),
                    u.display_name = trim($first_name + ' ' + $last_name)

                MERGE (p:Product {id: $product_id})
                SET p.title = $product_name,
                    p.name = $product_name

                MERGE (c:Category {name: $category_name})
                SET c.display_name = $category_name

                MERGE (u)-[:PURCHASED]->(p)
                MERGE (p)-[:BELONGS_TO]->(c)
                """,
                user_id=row["user_id"],
                first_name=row["first_name"] or "",
                last_name=row["last_name"] or "",
                product_id=row["product_id"],
                product_name=row["product_name"],
                category_name=row["category_name"],
            )

    db_setup.close()


if __name__ == "__main__":
    import_data_and_enter_into_database(
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCLOUD_PROJECT"),
        limit=os.getenv("BIGQUERY_IMPORT_LIMIT"),
    )
