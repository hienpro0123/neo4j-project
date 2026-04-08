import unittest
from unittest.mock import MagicMock

from src.recommendations.collaborative_filtering import ProductRecommender


class TestRecommendations(unittest.TestCase):

    def setUp(self):
        self.driver = MagicMock()
        self.session = MagicMock()
        self.driver.session.return_value.__enter__.return_value = self.session
        self.recommender = ProductRecommender(self.driver, "neo4j")

    def test_user_based_recommendations(self):
        self.session.run.return_value = [
            {"Product": "Phone"},
            {"Product": "Laptop"},
        ]

        result = self.recommender.get_user_based_recommendations("1")

        self.assertEqual(result, ["Phone", "Laptop"])

    def test_user_based_recommendations_falls_back_when_sparse(self):
        self.session.run.side_effect = [
            [{"Product": "Phone"}],
            [{"Product": "Phone"}, {"Product": "Keyboard"}, {"Product": "Mouse"}],
        ]

        result = self.recommender.get_user_based_recommendations("1", top_n=3)

        self.assertEqual(result, ["Phone", "Keyboard", "Mouse"])

    def test_category_based_recommendations(self):
        self.session.run.return_value = [
            {"Recommendation": "Keyboard"},
        ]

        result = self.recommender.get_category_based_recommendations("1")

        self.assertEqual(result, ["Keyboard"])


if __name__ == "__main__":
    unittest.main()
