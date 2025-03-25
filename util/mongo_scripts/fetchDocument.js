// use JiraRepos
// load("fetchDocument.js");
// Use above 2 in the mongosh shell

// this returns a single random issue matching the $or restrictions and containing the defined fields.
// change collectionName to existing collection name

db.collectionName.findOne({
  $or: [
    { "fields.components": { $exists: true, $ne: [] } },
    { "fields.labels": { $exists: true, $ne: [] } },
    { "fields.issuelinks": { $exists: true, $ne: [] } }
  ]
}, {
  "fields.summary": 1,
  "fields.description": 1,
  "fields.project": 1,
  "fields.components": 1,
  "fields.labels": 1,
  "fields.issuelinks": 1,
  "fields.status": 1,
  _id: 0
});