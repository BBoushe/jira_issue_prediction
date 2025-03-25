// use JiraRepos
// load("findOneBlockingDoc.js");
// Use above 2 in the mongosh shell

// this returns a random db object such that the issuelinks type name is either Block or Depend.
// Will return *null* if it cannot find one.

const keywords = ["Block", "Depend", "Blocked", "Dependent", "Blocker", "Required", "Dependency", "Blocks",
  "Gantt End to Start", "Gantt End to End", "Gantt Start to Start", "Depends", "Follows", "Relate", "Cause",
  "Gantt Dependency", "Relates", "Gantt start-finish", "Gantt finish-finish", "finish-start [GANTT]",
  "finish-finish [GANTT]", "Gantt: finish-start", "Gantt: start-start", "start-finish [GANTT]", "dependent", ];

const document = db.Apache.findOne({
  "fields.issuelinks.type.name": { $in: keywords }
}, {
  "fields.summary": 1,
  "fields.description":1,
  "fields.issuelinks": 1,
  "fields.project":1,
  "fields.status":1,
  _id: 0
});

print(document);