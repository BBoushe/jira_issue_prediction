// use JiraRepos
// load("countBlockingInCollections.js");
// Use above 2 in the mongosh shell

// this query gets back the numbers of Block or Depend issuelinks in the collections and returns a number
// returns true if it executes at least once
const collections = ["Apache", "Hyperledger", "IntelDAOS", "JFrog", "Jira", "JiraEcosystem", "MariaDB", "Mindville", "Mojang", "MongoDB", "Qt", "RedHat", "Sakai", "SecondLife", "Sonatype", "Spring"];
const keywords = ["Block", "Depend", "Blocked", "Dependent", "Blocker", "Required", "Dependency", "Blocks", "Gantt End to Start", "Gantt End to End", "Gantt Start to Start", "Depends", "Follows", "Relate", "Cause", "Gantt Dependency", "Relates", "Gantt start-finish", "Gantt finish-finish", "finish-start [GANTT]", "finish-finish [GANTT]", "Gantt: finish-start", "Gantt: start-start", "start-finish [GANTT]", "dependent", ];

let totalCount = 0;
collections.forEach(col => {
  let count = db.getCollection(col).countDocuments({
    "fields.issuelinks.type.name": { $in: keywords }
  });
  totalCount += count;
  print(col + " : " + count);
});

print(`Total count: ${totalCount}`);