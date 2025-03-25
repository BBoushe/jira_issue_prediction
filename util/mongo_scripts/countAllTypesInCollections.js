// use JiraRepos
// load("countAllTypesInCollections.js");
// Use above 2 in the mongosh shell

var collections = ["Apache", "Hyperledger", "IntelDAOS", "JFrog", "Jira", "JiraEcosystem", "MariaDB", "Mindville", "Mojang", "MongoDB", "Qt", "RedHat", "Sakai", "SecondLife", "Sonatype", "Spring"];

collections.forEach(function(col) {
  print("Collection: " + col);
  var result = db.getCollection(col).aggregate([
    { $match: { "fields.issuelinks": { $exists: true, $ne: [] } } },
    { $unwind: "$fields.issuelinks" },
    { $group: { _id: "$fields.issuelinks.type.name", count: { $sum: 1 } } }
  ]).toArray();

  result.forEach(function(doc) {
    print("   " + doc._id + " : " + doc.count);
  });
  print(""); // new line for separation
});