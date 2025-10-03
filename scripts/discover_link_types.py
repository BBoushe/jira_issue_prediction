from data_extraction import JiraMongoExtractor
from collections import Counter

extractor = JiraMongoExtractor(uri="mongodb://localhost:27017", db_name="JiraRepos")
issues = extractor.fetch_issues(
    collection_name="Jira",
    query={'fields.issuelinks': {'$exists': True, '$ne': []}},
    projection={'fields.issuelinks': 1, 'id': 1}
)
extractor.close()

link_types = Counter()
for issue in issues:
    links = issue.get('fields', {}).get('issuelinks', [])
    for link in links:
        link_type = link.get('type', {}).get('name')
        if link_type:
            link_types[link_type] += 1

print(f"\nFound {len(issues)} issues with links")
print(f"\nAll link types (sorted by frequency):")
for link_type, count in link_types.most_common():
    print(f"  {link_type}: {count}")