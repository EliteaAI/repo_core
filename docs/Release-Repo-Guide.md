# EliteA Repo: how the Release machine works

*A plain-language guide to `repo_core` and `repo_target`, the "Release Tasks" page, and the EliteaUI build.*

> Prepared on 9 Nov 2026 from the code in `EliteaLocal/repo_core`, `EliteaLocal/repo_target` and `EliteaLocal/EliteaUI/.github/workflows`, plus the real run history on GitHub. Updated on 10 Nov 2026 when the fix in section 11 was merged (repo_target v0.1.5 + two new EliteaUI workflows).

---

## Contents

1. [The short version](#1-the-short-version)
2. [The big picture: what is "EliteA Repo"?](#2-the-big-picture-what-is-elitea-repo)
3. [The two repositories and what each one does](#3-the-two-repositories-and-what-each-one-does)
4. [The screens (menu map)](#4-the-screens-menu-map)
5. [Settings: the one place everything is configured](#5-settings-the-one-place-everything-is-configured)
6. [Every task on the Release Tasks page](#6-every-task-on-the-release-tasks-page)
7. [Where the files go and who can download them](#7-where-the-files-go-and-who-can-download-them)
8. [What really happens in each of your procedures](#8-what-really-happens-in-each-of-your-procedures)
9. [The EliteaUI GitHub workflows](#9-the-eliteaui-github-workflows)
10. [**The problem:** why "Wait for the EliteaUI build" no longer happens automatically](#10-the-problem-why-wait-for-the-eliteaui-build-no-longer-happens-automatically)
11. [**The fix:** two separate workflows](#11-the-fix-two-separate-workflows)
12. [Other things worth knowing (risks and gotchas)](#12-other-things-worth-knowing-risks-and-gotchas)
13. [Troubleshooting](#13-troubleshooting)
14. [Glossary](#14-glossary)
15. [Appendix: file-by-file reference](#15-appendix-file-by-file-reference)

---

## 1. The short version

- **EliteA Repo** is a private "app store" for EliteA. For each release version (for example `2.0.6`) it keeps copies of every EliteA plugin, the EliteaUI website bundle, and every Python package those plugins need. EliteA servers ("Pylons") and customers install a release from this store.
- **`repo_core`** is the shell of that store: the website, login, the Settings page, the task runner on the Release Tasks page, and the remote-control pages for Pylons.
- **`repo_target`** holds the 16 tasks you see in the drop-down. It also runs the "shelves" (download addresses) that serve the collected files.
- **The bug.** Since mid-September 2026, every release branch ends with a bot commit whose message contains `[skip ci]`. `tag_release` puts the release tag on exactly that commit. GitHub sees `[skip ci]` and does not start "Build and release from tag". So the EliteaUI bundle is never built, and you have to start the workflow by hand.
- **The fix (merged, switched on by a setting).** `tag_release` and `tag_release_from_main` each send their **own signal** to EliteaUI, which starts exactly one new workflow:
  - `tag_release` → `release_tag_build.yml`
  - `tag_release_from_main` → `release_branch_build.yml`

  That workflow creates the tag itself, using GitHub's built-in token. GitHub never starts other workflows from actions done with that token, so `tag_build_release.yml` and `build_and_release.yml` stay untouched and silent. See [section 11](#11-the-fix-two-separate-workflows).

---

## 2. The big picture: what is "EliteA Repo"?

Think of it as a **warehouse with labelled shelves**, one shelf set per release:

```
                    GitHub (EliteaAI organisation)
        ┌──────────────────────────────────────────────────┐
        │  EliteaUI   admin   auth   artifacts   ...  (repos)│
        │     │ release/2.0.6 branch  →  tag "2.0.6"         │
        │     │ GitHub Release "2.0.6" → EliteAUI.zip        │
        └─────┼────────────────────────────────────────────┘
              │  (1) Release Tasks create branches/tags on GitHub
              │  (2) Release Tasks download code + bundles from GitHub
              ▼
   ┌────────────────────────── EliteA Repo ───────────────────────────┐
   │  repo_core   = the building: website, login, settings, task runner │
   │  repo_target = the workers (tasks) + the shelves (download URLs)  │
   │                                                                   │
   │  Shelf "2.0.6":  plugins (code)  •  bundles (EliteAUI.zip)        │
   │                  python packages (wheels)                         │
   │  Public shelf "2.0.6": same idea, open to everyone               │
   │  Export shelf: one big .tar.gz per customer hand-over            │
   └───────────────────────────────────────────────────────────────────┘
              │  (3) Pylons / customers download a release from the shelves
              ▼
        EliteA environments (NEXT, customers' installations, ...)
```

The tasks on the Release Tasks page do one of three jobs:

| Job | Tasks |
|---|---|
| **Prepare GitHub**: create release branches and tags in all repos at once | `make_release_branch_from_main`, `tag_release`, `tag_release_from_main`, `tag_release_from_stage`, `delete_staging_branch` |
| **Fill the shelves**: download code, bundles and Python packages for a release | `collect_release_files`, `collect_release_requirements`, `collect_public_release_files`, `collect_public_release_requirements` |
| **Package / tidy / inspect** | `export_release`, `remove_export`, `purge_release`, `sync_registry`, `list_repos`, `diff_stage_migrations`, `diff_release_migrations` |

---

## 3. The two repositories and what each one does

Both are **Pylon plugins**. A plugin is a module that a Pylon server loads, much like an app on a phone. `repo_target` depends on `repo_core`, so `repo_core` always loads first.

### `repo_core`: "the building"

| What | In plain words | Where in code |
|---|---|---|
| Website shell | Draws the top menu (Core, Runtime, Release, User) and the pages. | `methods/init.py`, `templates/` |
| Login & permissions | Only users with the **admin** role can open the pages and run tasks. Each user can also be given access to specific releases (see [5.3](#53-giving-a-customer-access-to-a-release)). | `methods/auth.py` |
| Settings | Stores **one YAML text** (the settings) and hands it to every task. | `methods/settings.py`, `api/v1/settings.py` |
| Task runner | Runs a task in the background when you click **Start task** and keeps the list of runs (Invocations) for 24 hours. | `methods/tasks.py`, `api/v1/tasks.py` |
| Live logs | Streams a task's log lines to the "Logs" window while it runs (keeps the last 1,000 lines per task). | `methods/task_logs.py`, `sio/task_logs.py`, `utils/task_logs.py` |
| Pylon remote control | Shows the Pylons that report in, and lets you view or edit their config, restart them, and update, reload or delete plugins on them. | `api/v1/pylons.py`, `api/v1/remote.py`, `events/runtime_remote.py` |
| Users page | Create, rename or delete users and show their access token. | `api/v1/users.py` |

`repo_core` contains **no release logic**. It is an empty task runner until `repo_target` registers its tasks.

### `repo_target`: "the workers and the shelves"

| What | In plain words | Where in code |
|---|---|---|
| The 16 tasks | Everything in the drop-down. Registered with `repo_core` at start-up, in the order you see them. | `methods/init.py`, `tasks/*.py` |
| GitHub helper | Talks to the GitHub API: list repos, read branches, create tags/branches, download code and release files. | `tasks/common.py` (`GithubClient`) |
| EliteA helper | Asks a running EliteA (Stage) which commit each plugin is on. Used by the "from stage" tasks. | `tasks/common.py` (`EliteAClient`) |
| Shelves (download URLs) | Serve plugins, bundles and Python packages per release, both private (login needed) and public. | `routes/depot.py`, `routes/simple.py`, `routes/public_*.py` |
| Registry | An index of what is on each shelf, kept in the plugin's saved state. It is rebuilt from disk by `sync_registry`. | `methods/init.py`, `methods/collect_*.py` |
| pip options | Lets you pass extra options to `pip` globally, per release, or per plugin. | `methods/pip.py` |

---

## 4. The screens (menu map)

| Menu | Page | What you can do |
|---|---|---|
| **Core → Users** | Users | Add a user (a "repo" access token is created automatically), rename, delete, view the token. |
| **Core → Settings** | Settings | Edit the YAML settings (see section 5). **Load settings** / **Save settings**. |
| **Runtime → Pylons** | Pylons | Lists Pylons that reported in during the last 60 s. View the config (merged or raw), save it, **Restart**. |
| **Runtime → Remote** | Remote | Lists every plugin on every reporting Pylon with its version and commit. **Update selected**, **Update selected (purge requirements)**, **Purge selected requirements**, **Reload selected**, **Delete selected**, **Export selected configs** / **Import configs**. |
| **Release → Tasks** | Release Tasks | Pick a task, type the **Task parameter**, click **Start task**. The Invocations table shows each run. Open its **Logs** to see what happened. |
| **User → Logout** | — | Log out. |

> **Tip:** a task's **Status** only says whether the task *crashed*. Most tasks catch per-repo errors, log them, and carry on. A run can show *success* while some repos failed, so always open **Logs** and look for `Failed to ...` or `warning` lines.

---

## 5. Settings: the one place everything is configured

The settings are a YAML text saved inside `repo_core` (**Core → Settings**). They are **not** in the code repositories. Every task reads them when it starts, so changes apply to the next task run without a restart.

### 5.1 Keys the code uses

| Key | Used by | What it means |
|---|---|---|
| `github_token` | all GitHub tasks | Token used to talk to GitHub. It needs rights to read repos, create branches and tags, and read releases. |
| `elitea_url`, `elitea_token` | `tag_release_from_stage`, `diff_stage_migrations` | Address and token of the EliteA environment (Stage) to read plugin commits from. |
| `target_orgs` | all GitHub tasks | GitHub organisations to work on, for example `[EliteaAI]`. |
| `known_repos.target.<org>` | almost every task | **The release list.** Only repos listed here get branches, tags and collection. This is the list you extend in step 1 of the Stage procedure. |
| `known_repos.ignore.<org>` | `list_repos` | Repos you deliberately leave out, so `list_repos` stops reporting them as new. |
| `known_repos.public_target.<org>` | `collect_public_release_*` | Repos that go on the **public** (no-login) shelf. |
| `base_path` | file tasks | Folder where everything is stored. Default `/data/repo`. |
| `pip_args.common` / `.per_release.<ver>` / `.per_plugin.<file>` | `collect_*_requirements` | Extra `pip` options. The per-plugin entry wins over per-release, which wins over common. |
| `log_room_cache_size`, `log_room_ttl`, `log_room_housekeeping_interval` | live logs | How many log lines to keep (1000), how long (86400 s = 24 h), and how often to clean up (3600 s). |

### 5.2 Skeleton (structure only, values are placeholders)

```yaml
github_token: "<github token>"
elitea_url: "https://<stage address>"
elitea_token: "<elitea token>"
base_path: /data/repo

target_orgs:
  - EliteaAI

known_repos:
  target:            # included in releases
    EliteaAI:
      - EliteaUI
      - admin
      - admin_ui
      - artifacts
      - auth
      # ...
  ignore:            # known, but deliberately NOT released
    EliteaAI:
      - some_tool_repo
  public_target:     # put on the public shelf
    EliteaAI:
      - ...

pip_args:
  common: []
  per_release: {}
  per_plugin: {}
```

> **Careful:** every organisation in `target_orgs` must also appear under `known_repos.target` **and** `known_repos.ignore` (an empty list is fine). Otherwise `list_repos` and other tasks stop with an error.

### 5.3 Giving a customer access to a release

The private shelves only open for a user who has the **admin** role, or whose user **name** is a small JSON text listing their releases, for example:

```json
{"releases": ["2.0.6"]}
```

That user's token can then download only release `2.0.6`. The **public** shelves need no login at all.

---

## 6. Every task on the Release Tasks page

### 6.1 How the "Task parameter" works

Most tasks take a release version. Many also accept a **limit to specific repos**:

| You type | Meaning |
|---|---|
| `2.0.6` | Release 2.0.6, all repos in the release list |
| `2.0.6:runtime_engine_wam` | Release 2.0.6, only that repo |
| `2.0.6:auth,auth_core` | Release 2.0.6, only these two (comma, no spaces) |

### 6.2 The tasks, in drop-down order

| # | Task | What it does, in plain words | Parameter | Changes GitHub? |
|---|---|---|---|---|
| 1 | **list_repos** | Lists repos that exist on GitHub but are in neither the release list nor the ignore list, i.e. new repos you may need to add. | *(none)* | No |
| 2 | **tag_release_from_stage** | Tags every repo at **the exact commit currently running on Stage** (taken from `elitea_url`). EliteaUI is tagged at the commit in Stage's `head.txt`. Repos not on Stage are tagged from `main`. | `2.0.6[:repos]` | **Yes** (tags) |
| 3 | **tag_release_from_main** | Tags every repo at the newest commit of its default branch (`main`). | `2.0.6[:repos]` | **Yes** (tags) |
| 4 | **sync_registry** | Re-reads the storage folders and rebuilds the shelf index. Use it if the shelves look out of date. It also runs on the very first start. | *(none)* | No |
| 5 | **collect_release_files** | For each repo in the release list, downloads the code **at the tag** (only repos that have a `metadata.json`, i.e. real plugins), plus **every file attached to the GitHub Release with that name**. For EliteaUI that file is `EliteAUI.zip`. Puts them on the private shelf. | `2.0.6[:repos]` | No |
| 6 | **collect_release_requirements** | Opens each collected plugin, reads its `requirements.txt`, and runs `pip wheel` to download every Python package it needs onto the private shelf. | `2.0.6[:plugins]` | No |
| 7 | **collect_public_release_files** | Same as #5, but for the `public_target` list, onto the **public** shelf. For non-plugin repos it takes the **first** file of the GitHub Release. | `2.0.6[:repos]` | No |
| 8 | **collect_public_release_requirements** | Same as #6, for the public shelf. | `2.0.6[:plugins]` | No |
| 9 | **export_release** | Packs **everything** for that release (private and public, plugins and packages) into one `.tar.gz` with a random 30-character name and puts it on the public *export* shelf. The log ends with `Result: <file name>`. That file is what you hand to a customer. | `2.0.6` | No |
| 10 | **remove_export** | Deletes one export file from the export shelf. | the file name from `Result:` | No |
| 11 | **purge_release** | **Deletes** everything stored for a release, on all shelves (files and index). This cannot be undone. | `2.0.6` | No |
| 12 | **diff_stage_migrations** | Compares each plugin's `db_migrations.txt` between what runs on Stage and the `staging` branch, and prints the differences. | *(none)* | No |
| 13 | **diff_release_migrations** | Same comparison between two releases. | `2.0.5,2.0.6[:repos]` | No |
| 14 | **delete_staging_branch** | Deletes the `staging` branch in every repo (or only the listed ones). | *(empty)* or `repo1,repo2` | **Yes** (deletes) |
| 15 | **make_release_branch_from_main** | Creates `release/2.0.6` from `main` in every repo. If the branch already exists it is **left alone** (warning in the log). | `2.0.6[:repos]` | **Yes** (branches) |
| 16 | **tag_release** | Puts tag `2.0.6` on the newest commit of `release/2.0.6` in every repo. Repos without that branch are skipped (warning). **If the tag already exists it is moved** to the new commit. | `2.0.6[:repos]` | **Yes** (tags) |

---

## 7. Where the files go and who can download them

All under `base_path` (default `/data/repo`):

```
/data/repo/
├── depot/2.0.6/plugins/<repo>.tar.gz      ← collect_release_files     (private)
├── depot/2.0.6/bundles/EliteAUI.zip       ← collect_release_files     (private)
├── simple/2.0.6/*.whl                     ← collect_release_requirements (private)
├── public/depot/2.0.6/...                 ← collect_public_release_files (public)
├── public/simple/2.0.6/*.whl              ← collect_public_release_requirements (public)
├── public/depot/export/bundles/<random>.tar.gz  ← export_release (public!)
├── cache/   (pip download cache)
└── tmp/     (temporary files)
```

The matching download addresses, under the Repo's address:

| Address | Login? | What it serves |
|---|---|---|
| `/target/depot/<release>/…` | Yes (admin, or user with that release) | Plugin code, metadata, requirements, bundles |
| `/target/simple/<release>/…` | Yes | Python packages, in the standard pip "simple index" format |
| `/target/public/depot/<release>/…` | **No** | Public plugins and bundles |
| `/target/public/simple/<release>/…` | **No** | Public Python packages |
| `/target/public/depot/export/bundles/<file>/data` | **No** | The export archive |

> **Security note:** export archives sit on the **public** shelf. Anyone who knows the random file name can download one. Run `remove_export` once the customer has their copy.

---

## 8. What really happens in each of your procedures

### 8.1 Stage Deployment (new release branch → Stage)

| Your step | What the code actually does |
|---|---|
| `list_repos` | Lists GitHub repos missing from both the release list and the ignore list. **Nothing is changed.** |
| Add repos in Core Settings | Edits `known_repos.target.EliteaAI`. The next task run uses the new list. |
| `make_release_branch_from_main 2.0.6` | In every listed repo, creates `release/2.0.6` from the newest `main` commit (skipped if it already exists). |
| Verify branches / Actions | Creating a branch does **not** start any EliteaUI build by itself. |
| `tag_release 2.0.6` | In every repo with `release/2.0.6`, creates the tag `2.0.6` on that branch's newest commit. |
| Verify tags through GitHub Actions | ⚠️ For EliteaUI the tag **should** start "Build and release from tag", but currently does not. See [section 10](#10-the-problem-why-wait-for-the-eliteaui-build-no-longer-happens-automatically). |
| Point Argo CD Stage to `release/2.0.6`, verify sync | Happens outside the Repo tool. |

### 8.2 Next / Hotfix / Final release (filling the shelves)

The order matters because each step uses the result of the one before it:

```
tag_release 2.0.6
      │   GitHub: tag "2.0.6" placed on release/2.0.6 in every repo
      ▼
[EliteaUI build]  ← GitHub Action builds the website and attaches EliteAUI.zip
      │             to the GitHub Release "2.0.6"   (THIS is the "wait" step)
      ▼
collect_release_files 2.0.6         downloads plugin code at tag 2.0.6
      │                             + EliteAUI.zip from the GitHub Release "2.0.6"
      ▼
collect_release_requirements 2.0.6  downloads Python packages for those plugins
      ▼
collect_public_release_files / _requirements 2.0.6   (same, public shelf)
      ▼
export_release 2.0.6                one .tar.gz for the customer  (Final release only)
```

**Why you must wait for the EliteaUI build:** `collect_release_files` takes whatever is attached to the GitHub Release `2.0.6` **at that moment**. If the build has not finished, you collect **nothing** (first time) or the **previous, outdated** `EliteAUI.zip` (hotfix). The task reports success either way, so the mistake stays hidden.

**Hotfix limited to plugins (`2.0.2:runtime_engine_wam`).** If EliteaUI is **not** in the list, nothing in EliteaUI changes and there is no build to wait for. You only wait when EliteaUI is part of the hotfix.

**Updating NEXT Pylons.** Updating plugins on Pylons (Runtime → Remote → *Update selected*) makes the Pylons fetch the newly collected plugin versions. That is why collection must finish first.

---

## 9. The EliteaUI GitHub workflows

| File | Name in GitHub | Starts when | What it does |
|---|---|---|---|
| `build_and_release.yml` | Build + Release + Deploy | Every push to `main`, or manually | Bumps the version (`0.4.2570` → `0.4.2571`), commits it **with `[skip ci]`**, builds, and attaches `EliteAUI.zip` to the release `latest`. Tells `elitea_core` the new UI version. |
| `tag_build_release.yml` | **Build and release from tag** | A tag is pushed, **or** it is started manually / by the hotfix workflow | **Two jobs in one file:** **(a) on a release branch:** bumps a hotfix version (`…-hotfix.53`), commits it **with `[skip ci]`**, builds, attaches the zip to release `2.0.x`; **(b) on a tag:** builds the tag as-is and attaches the zip to that release. |
| `cherry_pick_to_main.yml` | Cherry-pick hotfix to main | A PR into `release/**` is merged | Opens a PR copying a `hotfix/…` change to `main`, **and** starts "Build and release from tag" on the release branch (case (a) above). |
| `trigger_deploy.yml` | Trigger deploy | Any GitHub Release is published/updated | **Always fails on purpose** (`exit 1`). The real deploy is commented out. Its red ❌ runs can be ignored. |
| `delete_stale.yml` | Delete stale branches | Daily at midnight | Removes branches inactive for 40 days. |

---

## 10. The problem: why "Wait for the EliteaUI build" no longer happens automatically

### 10.1 What you see

After `tag_release`, the **Build and release from tag** workflow does not start, so you start it by hand from the Actions tab.

### 10.2 The cause, in one sentence

**`tag_release` tags a commit whose message contains `[skip ci]`, and GitHub is built never to start a tag-push workflow for such a commit.**

### 10.3 Step by step

1. Since **10–14 Sep 2026** (PRs #978 and #1004, "notify-version" / "ui-version-notify"), every run of the workflow on a release branch bumps the hotfix version and pushes a commit like:
   `build: [EL-1000] Increment version to 0.4.2509-hotfix.53 [skip ci]`
2. `[skip ci]` is there on purpose: it stops that commit from starting yet another build (an endless loop).
3. So the **newest commit of every release branch is always that bot commit.** The same applies to `main` (bumped by "Build + Release + Deploy").
4. `tag_release` (in `repo_target/tasks/repo_tasks.py`) tags **the newest commit of `release/<version>`**, which is that `[skip ci]` commit.
5. GitHub sees a tag push for a `[skip ci]` commit and **ignores** every workflow that listens to "push", including `on: push: tags`.

### 10.4 Evidence (checked on GitHub, 9 Nov 2026)

| Tag | Points to commit | Message |
|---|---|---|
| `2.0.8` | `427749c` | `build: [EL-1000] Increment version to 0.4.2509-hotfix.50 [skip ci]` |
| `2.0.7` | `3e27218` | `build: [EL-1000] Increment version to 0.4.2342-hotfix.38 [skip ci]` |
| `2.0.6` | `591d7b9` | `build: [EL-1000] Increment version to 0.4.2219-hotfix.16 [skip ci]` |

Run history of "Build and release from tag":

- **36** runs were started automatically by a tag push. The **last one was 16 Sep 2026** (tag `2.0.5`, which still pointed to a normal commit).
- Every run since then, including all of 2.0.7 and 2.0.8, was started **manually or by the hotfix workflow** (`workflow_dispatch`).

The timing matches the date the version bump was added exactly.

### 10.5 A second, smaller problem in the same file

When the workflow runs on a release branch and the GitHub Release (and tag) **doesn't exist yet**, the release step creates the tag on **`main`** instead of the release branch, because no `commit:` is given. A later `tag_release` moves it to the right place, but until then the tag is wrong. A manual run on a release branch also defaults the release name to **`latest`**, which can overwrite the `latest` release by mistake.

---

## 11. The fix: two separate workflows

> Status: **merged.** It is active only after `ui_build_dispatch: true` is set in Core → Settings (see 11.4).
> Files: EliteaUI [`release_tag_build.yml`](https://github.com/EliteaAI/EliteaUI/blob/main/.github/workflows/release_tag_build.yml) and [`release_branch_build.yml`](https://github.com/EliteaAI/EliteaUI/blob/main/.github/workflows/release_branch_build.yml). repo_target [`tasks/repo_tasks.py`](https://github.com/EliteaAI/repo_target/blob/main/tasks/repo_tasks.py) and [`tasks/common.py`](https://github.com/EliteaAI/repo_target/blob/main/tasks/common.py) (v0.1.5).

### 11.1 The rules this design guarantees

| Workflow | Starts automatically **only** when | Never starts because of these tasks |
|---|---|---|
| **`release_tag_build.yml`** *(new)* | you run **`tag_release`** | — |
| **`release_branch_build.yml`** *(new)* | you run **`tag_release_from_main`** | — |
| `tag_build_release.yml` *(unchanged)* | as today: a tag push you make by hand, or a hotfix PR merged into `release/**` | `tag_release`, `tag_release_from_main` |
| `build_and_release.yml` *(unchanged)* | as today: a push to `main`, or a manual run | `tag_release`, `tag_release_from_main` |

`tag_build_release.yml`, `build_and_release.yml` and `cherry_pick_to_main.yml` stay **exactly as they are**.

### 11.2 Why a plain "tag" trigger can't give that guarantee

- `tag_release` and `tag_release_from_main` create **identical** tags (`2.0.9`) through the **same** GitHub call. Right after `make_release_branch_from_main`, they even tag the **same commit**. A workflow reacting to "a tag appeared" can't tell which task created it.
- Any tag created with your Repo's GitHub token is a tag push. That push starts **`tag_build_release.yml`** (`on: push: tags: '*'`) whenever the commit lacks `[skip ci]`. Today you're only "protected" by `[skip ci]`, and only by luck of timing. For example, right after a PR merge the newest commit is the merge commit, not the bot's `[skip ci]` commit.

So the task itself has to say which workflow it wants, and the tag must be created in a way that starts nothing else.

### 11.3 How it works

```
tag_release 2.0.9                          tag_release_from_main 2.0.9
   │ all other repos: tagged as today         │ all other repos: tagged as today
   │ EliteaUI: NOT tagged by the Repo.        │ EliteaUI: NOT tagged by the Repo.
   │ Sends signal "repo-tag-release"          │ Sends signal "repo-tag-release-from-main"
   │ {tag 2.0.9, commit of release/2.0.9}     │ {tag 2.0.9, commit of main}
   ▼                                          ▼
release_tag_build.yml                      release_branch_build.yml
   1. checks the request (version format, commit id)
   2. creates/moves tag 2.0.9 with GitHub's built-in workflow token
        → GitHub rule: actions done with that token start NO other workflow,
          so tag_build_release.yml cannot fire
   3. builds the tagged commit, attaches EliteAUI.zip to Release "2.0.9"
        → pushes no commits, so build_and_release.yml cannot fire
   4. checks the zip is attached → "Bundle ready" notice
   5. notifies elitea_core of the UI version (same as the old tag build)
```

Why each guarantee holds:

| Guarantee | Based on |
|---|---|
| Only `tag_release` starts `release_tag_build.yml` | It listens **only** to the signal type `repo-tag-release` (a `repository_dispatch`), which only that task sends. |
| Only `tag_release_from_main` starts `release_branch_build.yml` | It listens **only** to `repo-tag-release-from-main`. |
| `tag_build_release.yml` isn't started | The tag is created with the workflow's built-in `GITHUB_TOKEN`. GitHub documents that events caused by this token start no new workflow runs. This holds with or without `[skip ci]`. |
| `build_and_release.yml` isn't started | The new workflows never push commits. They don't bump the version either; a tag is built as-is. |
| `trigger_deploy.yml` isn't started by the new release | The Release is created with the same built-in token. |

The signal (`repository_dispatch`) always runs the workflow file from **`main`**. The new files only need to be on `main`, not on every release branch.

Both workflows can also be **run by hand** from the Actions tab (input: an existing tag) to rebuild a bundle. A manual run builds only; it never creates or moves tags.

### 11.4 The `repo_target` change (v0.1.5)

repo_target v0.1.5 changes 2 files:

- `tasks/common.py`: a new `repository_dispatch()` call (sends the signal to GitHub).
- `tasks/repo_tasks.py`: a new helper `tag_or_dispatch()`, used by `tag_release` and `tag_release_from_main` only. For **EliteaUI**, and only when the new setting is on, it sends the signal instead of tagging. Every other repo is tagged exactly as before.

It is **switched off by default**. Add this line in **Core → Settings** to switch it on:

```yaml
ui_build_dispatch: true
```

With the setting absent or `false`, the Repo behaves exactly as today. That makes the rollout order safe.

Tested with a simulated GitHub. Setting off: identical to today. Setting on: EliteaUI receives the right signal for each task, and other repos are still tagged normally.

### 11.5 Rollout, in this order

1. **EliteaUI:** `release_tag_build.yml` and `release_branch_build.yml` are on **`main`** (done). Nothing else was changed.
2. **repo_target:** deploy v0.1.5 to the Repo (update the plugin, then restart). Nothing changes yet.
3. **Core → Settings:** add `ui_build_dispatch: true`, save.
4. Run `tag_release 2.0.x` (or `tag_release_from_main`). In EliteaUI → Actions, exactly one run should appear: "Release tag build (tag_release)" (or "Release branch build (tag_release_from_main)"). "Build and release from tag" and "Build + Release + Deploy" should show nothing new.
5. Wait for the **Bundle ready** notice, then continue with `collect_release_files`.

**To undo:** set `ui_build_dispatch: false`. You're back to today's behaviour immediately, with no redeploy.

### 11.6 What this does *not* change (on purpose)

- `tag_release_from_stage` still tags EliteaUI directly, as today. It wasn't in scope, so it can still start `tag_build_release.yml`.
- Tags pushed by hand, and the hotfix flow (`cherry_pick_to_main.yml` → `tag_build_release.yml`), work exactly as today.
- Other repos' own workflows (if any react to tags) behave as today. Only EliteaUI's tagging moves into its workflow.
- In the Repo task log, EliteaUI now shows `Requesting UI tag + build (...)` instead of a tagging line. The EliteaUI tag appears a few seconds later, when the workflow runs.

### 11.7 Re-tagging an existing release (for example 2.0.8)

Running `tag_release 2.0.8` again when tag `2.0.8` already exists:

1. Other repos: the tag is **moved** to the newest commit of their `release/2.0.8`, as before.
2. EliteaUI: the Repo sends `repo-tag-release`. "Release tag build (tag_release)" **moves** tag `2.0.8` to the commit the Repo sent. The run shows a *Tag moved* notice: `2.0.8 -> <commit>`. It then rebuilds, and **replaces** `EliteAUI.zip` on the existing Release `2.0.8`.
3. "Build and release from tag" and "Build + Release + Deploy" show **no new run**.

To re-tag **only EliteaUI** and leave the other repos alone, use `2.0.8:EliteaUI`.

What to check:

| Where | Expected |
|---|---|
| Repo task log | `Requesting UI tag + build (repo-tag-release): EliteaAI - EliteaUI @ <commit>`, no `Failed to …` |
| EliteaUI → Actions | Exactly one new run: **Release tag build (tag_release)**, green, with notices *Tag moved* and *Bundle ready* |
| EliteaUI → tag `2.0.8` | Points to the commit from the log (the newest commit of `release/2.0.8`) |
| EliteaUI → Release `2.0.8` | `EliteAUI.zip` freshly updated (asset date = now) |
| EliteaUI → Actions, other workflows | No new runs of *Build and release from tag* or *Build + Release + Deploy* caused by the re-tag |

---

## 12. Other things worth knowing (risks and gotchas)

| # | Finding | Why it matters | Where |
|---|---|---|---|
| 1 | Tasks report **success** even when some repos failed (errors are caught per repo and logged). | Always check **Logs** for `Failed to …`. | `tasks/repo_tasks.py` |
| 2 | `collect_release_files` stays silent when a Release or its zip is missing. | You can collect a release without the UI bundle and not notice. Check `Getting bundle data: EliteAUI.zip` in the log. | `tasks/release_tasks.py` |
| 3 | `collect_release_files` has **no** per-repo error handling. | One broken repo stops the whole task, and the repos after it are not collected. | `tasks/release_tasks.py` |
| 4 | `collect_public_release_files` uses the **first** file of a Release and crashes if a Release has no files. | A Release without its build output breaks the task. | `tasks/public_release_tasks.py` |
| 5 | `tag_release` silently **moves** an existing tag. | Running it with the wrong version re-points that tag. Double-check the parameter. | `tasks/common.py` |
| 6 | `make_release_branch_from_main` always uses the branch literally called `main`. | A repo whose main branch has another name fails (logged). | `tasks/repo_tasks.py` |
| 7 | `purge_release` deletes files permanently. | There is no undo. | `tasks/registry_tasks.py` |
| 8 | Export archives are on the **public** shelf. | Remove them after hand-over (`remove_export`). | `tasks/export_tasks.py` |
| 9 | The Invocations list lives in memory only (24 h). | After a restart of the Repo, the history and logs are gone. | `repo_core/methods/init.py` |
| 10 | `trigger_deploy.yml` always fails. | Red ❌ after every Release update; it is noise, not a real problem. | EliteaUI workflows |
| 11 | Node version differs: `main` builds with 24.0.0, release builds with 23.11.0. | A UI built on `main` and on a release branch may behave differently. | EliteaUI workflows |

---

## 13. Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| No EliteaUI build after `tag_release` | Section 10 (`[skip ci]`) | Today: start "Build and release from tag" manually on the tag. After the fix: check that `ui_build_dispatch: true` is in Settings and that the task log shows `Requesting UI tag + build`. |
| `collect_release_files` finished but the UI is old or missing on NEXT | Collected before the EliteaUI build finished | Wait for the build ("Bundle ready" notice after the fix), then run `collect_release_files 2.0.x:EliteaUI` again. |
| `tag_release` log says `Release branch does not exist` | `make_release_branch_from_main` wasn't run for that repo, or the repo was added to settings later | Run `make_release_branch_from_main 2.0.x:<repo>`, then `tag_release 2.0.x:<repo>`. |
| A new repo isn't released | Not in `known_repos.target` | Run `list_repos`, add it in Core → Settings, save. |
| A task fails immediately with an error about a missing key | Settings YAML incomplete or invalid (e.g. org missing from `ignore`) | Fix it in Core → Settings. The Repo log shows `Failed to load settings` if the YAML itself is broken. |
| Shelves show stale content | Index out of date | Run `sync_registry`. |
| A customer token gets "403" | User name lacks `{"releases": ["2.0.x"]}` | Edit the user in Core → Users. |

---

## 14. Glossary

| Term | Meaning |
|---|---|
| **Pylon** | The EliteA server program that loads plugins. The Repo itself is a Pylon. |
| **Plugin** | A module loaded by a Pylon. In GitHub, any repo with a `metadata.json`. |
| **Release branch** | `release/2.0.6`: a copy of `main` taken at release time, receives only hotfixes. |
| **Tag** | A permanent label on one exact commit, e.g. `2.0.6`. Used to say "this is exactly what we ship". |
| **GitHub Release** | A page on GitHub tied to a tag, with downloadable files attached (here: `EliteAUI.zip`). |
| **Bundle** | A ready-built file, here the compiled EliteaUI website zip. |
| **Wheel (`.whl`)** | A ready-to-install Python package. |
| **Workflow / GitHub Action** | An automatic script GitHub runs on certain events (push, tag, manual click). |
| **`[skip ci]`** | Text in a commit message telling GitHub: "don't start push-triggered workflows for this commit". |
| **workflow_dispatch** | Starting a workflow manually (or from another workflow or the API). |
| **create event** | GitHub's "a new branch or tag was created" signal. Not affected by `[skip ci]`. |
| **Stage / NEXT** | EliteA environments: Stage for testing a release branch, NEXT the next production-like environment. |

---

## 15. Appendix: file-by-file reference

### `repo_core` (plugin "EliteA repository core", v0.1, depends on `auth`)

| File | Role |
|---|---|
| `module.py`, `metadata.json` | Plugin entry point and description |
| `methods/init.py` | Start-up: menus, task runner (background threads, 24 h retention), log streaming, Pylon registry |
| `methods/auth.py` | `user_has_role`, `user_has_release` (reads `{"releases": [...]}` from the user name), access-denied page |
| `methods/settings.py` | `get_settings()`: parses the saved YAML (logs `Failed to load settings` if it's invalid) |
| `methods/tasks.py` | `register_task`, `task_list`, `execute_task` (adds Starting / Exiting log lines and duration) |
| `methods/task_logs.py`, `sio/task_logs.py`, `utils/task_logs.py` | Live log rooms, 1,000-line cache, 24 h clean-up |
| `api/v1/tasks.py` | List runs / start a task / stop a task |
| `api/v1/settings.py` | Load and save settings |
| `api/v1/users.py` | User and token management |
| `api/v1/pylons.py`, `api/v1/remote.py` | Pylon config / restart; plugin update, reload, delete, purge requirements, config export/import |
| `events/runtime_remote.py` | Receives "I'm alive" reports from Pylons (dropped after 60 s of silence) |
| `templates/`, `static/` | Web pages (Bootstrap + Vue + CodeMirror YAML editor) |

### `repo_target` (plugin "EliteA repository target", v0.1.4, depends on `repo_core`)

| File | Role |
|---|---|
| `module.py` | Mounts everything under `/target` |
| `methods/init.py` | Creates folders, opens `/target/public/*` (or all of `/target/*` if `internal_repo: true`), loads the registry, **registers the 16 tasks** |
| `methods/auth.py` | Release-level access check |
| `methods/collect_depot.py`, `methods/collect_simple.py` | Build the shelf index from folders (reads each plugin's `metadata.json` and `requirements.txt`, each wheel's metadata and hash) |
| `methods/pip.py` | Chooses pip options (per plugin > per release > common) |
| `routes/depot.py`, `routes/simple.py` | Private shelves |
| `routes/public_depot.py`, `routes/public_simple.py` | Public shelves |
| `tasks/common.py` | `GithubClient` (repos, branches, tags, contents, tarballs, releases) and `EliteAClient` (Stage plugin heads, UI `head.txt`) |
| `tasks/repo_tasks.py` | `list_repos`, `tag_release_from_main`, `tag_release_from_stage`, `delete_staging_branch`, `make_release_branch_from_main`, `tag_release` |
| `tasks/release_tasks.py` | `collect_release_files`, `collect_release_requirements` |
| `tasks/public_release_tasks.py` | `collect_public_release_files`, `collect_public_release_requirements` |
| `tasks/export_tasks.py` | `export_release`, `remove_export` |
| `tasks/registry_tasks.py` | `sync_registry`, `purge_release` |
| `tasks/diff_tasks.py` | `diff_stage_migrations`, `diff_release_migrations` |
