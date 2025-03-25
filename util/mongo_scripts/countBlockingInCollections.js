// use JiraRepos
// load("countBlockingInCollections.js");
// Use above 2 in the mongosh shell

var collections = ["Apache", "Hyperledger", "IntelDAOS", "JFrog", "Jira", "JiraEcosystem", "MariaDB", "Mindville", "Mojang", "MongoDB", "Qt", "RedHat", "Sakai", "SecondLife", "Sonatype", "Spring"];

collections.forEach(function(col) {
  var count = db.getCollection(col).countDocuments({
    "fields.issuelinks.type.name": { $in: ["Block", "Depend"] }
  });
  print(col + " : " + count);
});