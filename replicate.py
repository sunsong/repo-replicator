import os
import sqlite3
import subprocess

# This tool is crafted for replicating git repositories from online git services like github.
# It guarantees that all repositories can be updated if you run this script regularly.
# All repositories that are about to be synchronized stored in sqlite db.
# Repositories are stored in ~/repos by default.


class Repo(object):
    """
        Basic manipulation for a repository:
        clone, update the repository
        get attributes of the repository
    """
    def __init__(self, https_url, ssh_url, user_name, repo_name, base_path):
        self.https_url = https_url
        self.ssh_url = ssh_url
        self.user_name = user_name
        self.repo_name = repo_name
        self.base_path = os.path.expanduser(base_path)

    def get_repo_path(self):
        return os.path.join(self.base_path, self.user_name, self.repo_name)

    def clone(self, full_path=None):
        if not full_path:
            full_path = self.get_repo_path()
        subprocess.check_call(["mkdir", "-p", full_path])
        subprocess.check_call(["git", "clone", "--bare", self.https_url, full_path])

    def update(self, full_path=None):
        """
            update this repo given the full_path,
            if full_path is not given, use default instead.
        """
        if not full_path:
            full_path = self.get_repo_path()
        subprocess.Popen("cd {}; git remote update".format(full_path), shell=True).wait()

    def exists(self):
        if os.path.exists(self.get_repo_path()):
            return True
        return False


class GithubRepo(Repo):
    """
        A specific type of Repo
    """
    def __init__(self, user_name, repo_name, base_path):
        https_url = "https://github.com/{}/{}.git".format(user_name, repo_name)
        ssh_url = "git@github.com:{}/{}.git".format(user_name, repo_name)
        super(GithubRepo, self).__init__(
            https_url, ssh_url, user_name, repo_name, base_path
        )


class DB(object):
    """
        SQLite related: check if all tables are created,
        if not, then create tables.
    """
    def __init__(self):
        self.tables = ['repos']
        self.table_schema = {
            'repos': [
                ('id', 'INTEGER'),
                ('user_name', 'VARCHAR'),
                ('repo_name', 'VARCHAR'),
            ]
        }
        self.connection = sqlite3.connect('db.sqlite3')

    def create_table(self, table):
        if table not in self.tables:
            return False

        sql = "CREATE TABLE %s (" % table
        sql += ", ".join([
            "%s %s" % (column[0], column[1]) for column in self.table_schema[table]
        ])
        sql += ")"

        print sql
        c = self.connection.cursor()
        c.execute(sql)

    def check_create_tables(self):
        tables = []
        c = self.connection.cursor()
        result = c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        for item in result:
            if len(item) > 0:
                tables.append(item[0])

        for table in self.tables:
            if table not in tables:
                self.create_table(table)

    def get_repos_generator(self):
        """
            Retrieve info from all repositories.
        """

        sql = "SELECT * from repos;"
        c = self.connection.cursor()
        result = c.execute(sql)
        return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
            Commit and close the db at last.
        """
        print "Commiting and closing db finally..."
        self.connection.commit()
        self.connection.close()


def validate_db():
    with DB() as db:
        db.check_create_tables()


def sync_repos():
    base_path = "~/repos"
    with DB() as db:
        for repo_id, user_name, repo_name in db.get_repos_generator():
            repo = GithubRepo(user_name, repo_name, base_path)
            if repo.exists():
                repo.update()
            else:
                repo.clone()


if __name__ == '__main__':
    validate_db()
    print "Validation Finished."
    sync_repos()
    print "Repo Synchronization Finished."
