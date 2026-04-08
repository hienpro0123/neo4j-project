class ProductRecommender:

    def __init__(self, driver, database=None):
        self.driver = driver
        self.database = database

    def _run_product_query(self, query, **params):
        with self.driver.session(database=self.database) as session:
            result = session.run(query, **params)
            return [record["Product"] for record in result]

    def get_user_based_recommendations(self, target_user_id, top_n=5):
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

        RETURN Product
        ORDER BY (SharedSignal * 3) + (CategorySignal * 2) + Supporters DESC, Product ASC
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
        WITH candidate.title AS Product, category_weight, COUNT(*) AS Popularity
        RETURN Product
        ORDER BY (category_weight * 3) + Popularity DESC, Product ASC
        LIMIT $top_n
        """

        recommendations = self._run_product_query(
            collaborative_query,
            user_id=target_user_id,
            top_n=top_n,
        )

        if len(recommendations) >= top_n:
            return recommendations

        fallback_recommendations = self._run_product_query(
            fallback_query,
            user_id=target_user_id,
            top_n=top_n,
        )

        merged = recommendations.copy()
        for product in fallback_recommendations:
            if product not in merged:
                merged.append(product)
            if len(merged) == top_n:
                break

        return merged

    def get_category_based_recommendations(self, target_user_id, top_n=5):
        query = """
        MATCH (u:User {id: $user_id})-[:PURCHASED]->(p:Product)-[:BELONGS_TO]->(c:Category)
        WITH u, c.name AS category, COUNT(*) AS cnt
        ORDER BY cnt DESC
        LIMIT 1
        MATCH (:Category {name: category})<-[:BELONGS_TO]-(q:Product)
        WHERE NOT (u)-[:PURCHASED]->(q)
        RETURN category, q.title AS Recommendation
        ORDER BY q.title LIMIT $top_n
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, user_id=target_user_id, top_n=top_n)
            return [record["Recommendation"] for record in result]
