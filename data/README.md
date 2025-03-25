# Requirenments

1. Download the [public jira dataset](https://zenodo.org/records/5901804) from Zendo. Make sure it's v5, which is the latest one
2. Extract it in this folder.
3. enter `ThePublicJiraDataset/3.\ DataDump/` and verify integrity of dump, using the command below
4. use the commands provided in the folders' README to restore the dump
5. start the mongoDB server with `mongod --config /path/to/mongod.conf
`

### Integrity 
Check the integrity of the mongoDB dump using: 
```bash
gzip -t mongodump-JiraRepos.archive
 ```

- a silent return means success

### Restore dump
Use the following command
```bash
mongorestore --gzip --archive=mongodump-JiraRepos.archive --nsFrom "JiraRepos.*" --nsTo "JiraRepos.*"
```


### Check if DB is running
The mongo shell command has been changed, and is now accessed through `mongosh`
- optionally `mongosh --ping <PORT>`

Run the command `db.runCommand({ ping:1 })` --> this should return an ok