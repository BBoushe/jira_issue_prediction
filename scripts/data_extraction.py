import pymongo


class JiraMongoExtractor:
    def __init__(self, uri='mongodb://localhost:27017/', db_name="JiraRepos"):
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]

    def fetch_issues(self, collection_name, query=None, projection=None):
        """
        Fetch issues from a given MongoDB collection.

        :param collection_name: string of collection we want to fetch issues from.
        :param query: dict to filter documents
        :param projection: dict specifying fields to include/exclude
        :return list of dicts containing issue data
        """
        if query is None:
            query = {}
        if projection is None:
            projection = {}

        cursor = self.db[collection_name].find(query, projection)
        return list(cursor)

    def close(self):
        self.client.close()