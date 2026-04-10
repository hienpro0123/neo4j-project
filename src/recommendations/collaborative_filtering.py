class ProductRecommender:

    def __init__(self, driver, database=None):
        self.driver = driver
        self.database = database

    def _run_product_query(self, query, **params):
        with self.driver.session(database=self.database) as session:
            result = session.run(query, **params)
            return [record["Product"] for record in result]

    def _run_records_query(self, query, **params):
        with self.driver.session(database=self.database) as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]

    def get_user_based_recommendation_details(self, target_user_id, top_n=5):
        collaborative_query = """
        MATCH (target:User {id: $user_id})-[:PURCHASED]->(p:Product)
        MATCH (similar:User)-[:PURCHASED]->(p)
        WHERE similar <> target
        WITH target, similar, COUNT(DISTINCT p) AS shared_products
        ORDER BY shared_products DESC
        LIMIT 25

        MATCH (similar)-[:PURCHASED]->(recommended:Product)-[:BELONGS_TO]->(recommended_category:Category)
        WHERE NOT (target)-[:PURCHASED]->(recommended)

        OPTIONAL MATCH (target)-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(target_category:Category)
        WITH recommended,
             recommended_category,
             shared_products,
             collect(DISTINCT target_category.name) AS target_categories

        WITH recommended.title AS Product,
             SUM(shared_products) AS SharedSignal,
             SUM(CASE WHEN recommended_category.name IN target_categories THEN 1 ELSE 0 END) AS CategorySignal,
             COUNT(*) AS Supporters
        WITH Product,
             SharedSignal,
             CategorySignal,
             Supporters,
             ((SharedSignal * 3) + (CategorySignal * 2) + Supporters) AS Score
        RETURN Product, SharedSignal, CategorySignal, Supporters, Score
        ORDER BY Score DESC, Product ASC
        LIMIT $top_n
        """
        fallback_query = """
        MATCH (target:User {id: $user_id})-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(category:Category)
        WITH target, category, COUNT(*) AS category_weight
        ORDER BY category_weight DESC, category.name ASC
        LIMIT 3

        MATCH (candidate:Product)-[:BELONGS_TO]->(category)
        WHERE NOT (target)-[:PURCHASED]->(candidate)

        OPTIONAL MATCH (:User)-[:PURCHASED]->(candidate)
        WITH candidate.title AS Product,
             category.name AS Category,
             category_weight AS CategoryWeight,
             COUNT(*) AS Popularity
        WITH Product,
             Category,
             CategoryWeight,
             Popularity,
             ((CategoryWeight * 3) + Popularity) AS Score
        RETURN Product, Category, CategoryWeight, Popularity, Score
        ORDER BY Score DESC, Product ASC
        LIMIT $top_n
        """

        collaborative_rows = self._run_records_query(
            collaborative_query,
            user_id=target_user_id,
            top_n=top_n,
        )

        details = []
        seen_products = set()

        for row in collaborative_rows:
            product = row["Product"]
            seen_products.add(product)
            details.append(
                {
                    "product": product,
                    "score": row["Score"],
                    "strategy": "user_based",
                    "reason": (
                        f"Shared purchases: {row['SharedSignal']}, "
                        f"category matches: {row['CategorySignal']}, "
                        f"supporters: {row['Supporters']}"
                    ),
                }
            )

        if len(details) >= top_n:
            return details

        fallback_rows = self._run_records_query(
            fallback_query,
            user_id=target_user_id,
            top_n=top_n,
        )

        for row in fallback_rows:
            product = row["Product"]
            if product in seen_products:
                continue
            seen_products.add(product)
            details.append(
                {
                    "product": product,
                    "score": row["Score"],
                    "strategy": "fallback_category",
                    "reason": (
                        f"Top category: {row['Category']}, "
                        f"category weight: {row['CategoryWeight']}, "
                        f"popularity: {row['Popularity']}"
                    ),
                }
            )
            if len(details) == top_n:
                break

        return details

    def get_user_based_recommendations(self, target_user_id, top_n=5):
        details = self.get_user_based_recommendation_details(target_user_id, top_n=top_n)
        return [item["product"] for item in details]

    def get_category_based_recommendation_details(self, target_user_id, top_n=5):
        query = """
        MATCH (u:User {id: $user_id})-[:PURCHASED]->(:Product)-[:BELONGS_TO]->(c:Category)
        WITH u, c.name AS category, COUNT(*) AS cnt
        ORDER BY cnt DESC
        LIMIT 1
        MATCH (q:Product)-[:BELONGS_TO]->(:Category {name: category})
        WHERE NOT (u)-[:PURCHASED]->(q)
        OPTIONAL MATCH (:User)-[:PURCHASED]->(q)
        WITH category, cnt, q.title AS Product, COUNT(*) AS Popularity
        WITH category, cnt, Product, Popularity, ((cnt * 3) + Popularity) AS Score
        RETURN Product, category AS Category, cnt AS CategoryWeight, Popularity, Score
        ORDER BY Score DESC, Product ASC
        LIMIT $top_n
        """
        rows = self._run_records_query(query, user_id=target_user_id, top_n=top_n)
        return [
            {
                "product": row["Product"],
                "score": row["Score"],
                "strategy": "category_based",
                "reason": (
                    f"Top category: {row['Category']}, "
                    f"category weight: {row['CategoryWeight']}, "
                    f"popularity: {row['Popularity']}"
                ),
            }
            for row in rows
        ]

    def get_category_based_recommendations(self, target_user_id, top_n=5):
        details = self.get_category_based_recommendation_details(target_user_id, top_n=top_n)
        return [item["product"] for item in details]
