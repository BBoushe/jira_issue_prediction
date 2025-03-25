# Requirenments

### Integrity 
Check the integrity of the mongoDB dump using: `gzip -t mongodump-JiraRepos.archive `
- a silent return means success

### Check if DB is running
The mongo shell command has been changed, and is now accessed through `mongosh`
- optionally `mongosh --ping <PORT>`

Run the command `db.runCommand({ ping:1 })` --> this should return an ok