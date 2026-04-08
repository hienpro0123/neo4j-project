import unittest
from unittest.mock import MagicMock, patch

from src.database.database_setup import DatabaseSetup


class TestDatabaseSetup(unittest.TestCase):

    @patch("src.database.database_setup.GraphDatabase.driver")
    def test_create_constraints_runs_expected_queries(self, mock_driver_factory):
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_factory.return_value = mock_driver

        db_setup = DatabaseSetup()
        db_setup.create_constraints()

        self.assertEqual(mock_session.run.call_count, 3)
        db_setup.close()


if __name__ == "__main__":
    unittest.main()
