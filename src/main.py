import argparse
import os

from src.bigquery_data.set_up_database_using_bigquery import import_data_and_enter_into_database
from src.database.database_setup import DatabaseSetup
from src.recommendations.collaborative_filtering import ProductRecommender


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-bigquery", action="store_true")
    parser.add_argument("--project-id", default=os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCLOUD_PROJECT"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--keep-existing-data", action="store_true")
    parser.add_argument("--user-id", default=None)
    return parser.parse_args()


def main():
    args = parse_args()

    if args.bootstrap_bigquery:
        import_data_and_enter_into_database(
            project_id=args.project_id,
            limit=args.limit,
            clear_existing=not args.keep_existing_data,
        )

    db_setup = DatabaseSetup()
    db_setup.create_constraints()

    collaborative_filter = ProductRecommender(db_setup.driver, db_setup.database)
    user_id = args.user_id or input("Enter User ID for recommendations: ")

    print("User-Based Collaborative Recommendations:")
    print(collaborative_filter.get_user_based_recommendations(user_id))

    print("Category-Based Collaborative Recommendations:")
    print(collaborative_filter.get_category_based_recommendations(user_id))

    db_setup.close()


if __name__ == "__main__":
    main()
