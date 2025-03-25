// use JiraRepos
// load("findOneBlockingDoc.js");
// Use above 2 in the mongosh shell

// this returns a random db object such that the issuelinks type name is either Block or Depend.
// Will return *null* if it cannot find one.

db.Apache.findOne({
  "fields.issuelinks.type.name": { $in: ["Block", "Depend"] }
}, {
  "fields.summary": 1,
  "fields.description":1,
  "fields.issuelinks": 1,
  "fields.project":1,
  "fields.status":1,
  _id: 0
});