# DefectDojo Fork – Operations Notes

Fork: `https://github.com/BlueRain94/django-DefectDojo` (`origin`)
Upstream: `https://github.com/DefectDojo/django-DefectDojo` (`upstream`)

> Shell commands below use Git Bash syntax unless marked **PowerShell**.

## Table of Contents

1. [Development](#1-development)
2. [Sync master and create a new version branch](#2-sync-master-and-create-a-new-version-branch)
3. [Upgrade a deployment](#3-upgrade-a-deployment)
4. [Backup and restore Postgres](#4-backup-and-restore-postgres)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Development

Run the dev stack (hot reload):

```bash
docker compose -f docker-compose.yml -f docker-compose.override.dev.yml up -d
```

Build and run the normal stack:

```bash
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
```

Follow the application log (debug output):

```bash
docker compose logs -f uwsgi
```

Where the custom code lives (since 3.x the modules were reorganized):

| What | File |
| --- | --- |
| Finding forms (`AddFindingForm`, `FindingForm`) | `dojo/finding/ui/forms.py` |
| Edit / View Finding views | `dojo/finding/ui/views.py` |
| Add Finding / Add from template views | `dojo/test/ui/views.py` |
| Request/response helper | `dojo/finding/helper.py` (`save_request_response_pairs`) |
| Templates | `dojo/templates/dojo/add_findings.html`, `edit_finding.html` |

> `dojo/forms.py`, `dojo/finding/views.py` and `dojo/test/views.py` are only
> backward-compat re-exports now. Do not put code there.

---

## 2. Sync master and create a new version branch

Goal: keep `master` identical to upstream, and put our commits on a branch
named `release/merge-from-<version>` on top of it.

Branch convention:

- `master` – mirror of `upstream/master`, **never commit here**.
- `release/merge-from-<version>` – upstream `<version>` + our commits.

### 2.1 Add the upstream remote (once)

```bash
git remote add upstream https://github.com/DefectDojo/django-DefectDojo.git
git remote -v
```

### 2.2 Remember the current base, then sync master

```bash
git switch master
OLD_BASE=$(git rev-parse master)      # base of the current release branch
git fetch upstream --tags
git merge --ff-only upstream/master
git push origin master
```

- `--ff-only` fails if `master` has local commits. In that case, check what they are
  (`git log upstream/master..master`). Only if nothing needs to be kept:

  ```bash
  git reset --hard upstream/master
  git push --force-with-lease origin master
  ```

Check the new version:

```bash
grep __version__ dojo/__init__.py
```

### 2.3 Read the upgrade notes

Read every note between the old and the new version **before** porting:

```text
docs/content/releases/os_upgrading/<version>.md
```

Look for module moves, renamed fields, removed features and hash-code changes.

### 2.4 Create the new branch and re-apply our commits

```bash
NEW=3.5.100                                    # new upstream version
OLD_BRANCH=release/merge-from-2.58.1           # previous release branch

git switch -c release/merge-from-$NEW master
git log --oneline $OLD_BASE..$OLD_BRANCH       # our commits, check the list
git cherry-pick $OLD_BASE..$OLD_BRANCH
```

If a commit conflicts:

```bash
git status                       # see the conflicted files
# fix the files, then:
git add <file>
git cherry-pick --continue
# or skip this commit / abort everything:
git cherry-pick --skip
git cherry-pick --abort
```

When upstream moved the code (the file is only a re-export, as in 3.x), do not
resolve the conflict in the old file. Abort, then port each commit by hand into
the new file and keep the original message and author:

```bash
git cherry-pick --abort
# ...edit the new files for commit <sha>...
git add <files>
git commit -C <sha>
```

### 2.5 Verify the branch

```bash
git log --oneline master..HEAD                 # only our commits on top
python -m py_compile dojo/finding/ui/views.py dojo/finding/ui/forms.py dojo/test/ui/views.py
```

Then run the stack (section 1) and test manually:

- Add Finding with several request/response pairs.
- Add Finding from template.
- Edit Finding: change existing pairs and add new ones.
- View Finding shows all pairs.

### 2.6 Push

```bash
git push -u origin release/merge-from-$NEW
```

---

## 3. Upgrade a deployment

1. Back up the database first (section 4).
2. Check out the release branch and rebuild:

   ```bash
   git fetch origin
   git switch release/merge-from-<version>
   git pull
   docker compose down
   docker compose build
   docker compose up -d
   ```

3. Migrations run automatically in the `initializer` container. Check them:

   ```bash
   docker compose logs initializer
   ```

   If the initializer is disabled, run them by hand:

   ```bash
   docker compose exec uwsgi /bin/bash -c "python manage.py migrate"
   ```

4. Run any extra command required by the upgrade notes, for example:

   ```bash
   docker compose exec uwsgi /bin/bash -c "python manage.py migrate_endpoints_to_locations"
   docker compose exec uwsgi /bin/bash -c "python manage.py dedupe --parser '<Scan Type>' --hash_code_only"
   ```

---

## 4. Backup and restore Postgres

Backup:

```bash
docker compose exec -T postgres pg_dumpall -c -U defectdojo > "dump_$(date +%Y-%m-%d_%H_%M_%S).sql"
```

**PowerShell**:

```powershell
docker compose exec -T postgres pg_dumpall -c -U defectdojo | Out-File -Encoding utf8 "dump_$(Get-Date -Format yyyy-MM-dd_HH_mm_ss).sql"
```

Restore:

```bash
docker compose exec -T postgres psql -U defectdojo < your_dump.sql
```

**PowerShell**:

```powershell
Get-Content your_dump.sql | docker compose exec -T postgres psql -U defectdojo
```

> Use the `pg_dump` / `psql` inside the `postgres` container so the client
> version matches the server. `manage.py dbbackup` is deprecated since 3.2.

---

## 5. Troubleshooting

### `/usr/bin/env: 'bash\r': No such file or directory`

Happens on Windows when `.sh` files are checked out with CRLF line endings.

1. Convert every `.sh` file in `docker/` to LF line endings, or set this and check out again:

   ```bash
   git config core.autocrlf input
   git rm --cached -r -q . && git reset --hard
   ```

   The last command discards uncommitted changes, so commit or stash first.

2. Rebuild all images and start again:

   ```bash
   docker compose build
   docker compose up -d
   ```

### Recreate the admin user

```bash
docker compose exec uwsgi /bin/bash -c "python manage.py createsuperuser"
```
