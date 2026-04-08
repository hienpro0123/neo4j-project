import unittest


@unittest.skip("Legacy InsertIntoDB flow was removed from the main BigQuery pipeline.")
class TestInsertIntoDB(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
