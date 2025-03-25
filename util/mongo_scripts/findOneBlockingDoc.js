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