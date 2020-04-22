# MIT License
#
# Copyright (c) 2020 SCL team at Red Hat
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from logging import getLogger
from pathlib import Path
from subprocess import CalledProcessError

from frambo.git import Git as FramboGit
from frambo.utils import run_cmd


logger = getLogger(__name__)


class Git(FramboGit):
    @staticmethod
    def has_ssh_access(url, port):
        """
        Check if SSH keys are able to push changes into Pagure
        :param url: Pagure URL address
        :param port: port for checking SSH keys
        :return: False if SSH keys are not valid for Pagure
                 True if SSH Keys are valid for using with Pagure
        """
        cmd = f"ssh -T git@git.{url} -p {port}"
        if not port:
            cmd = f"ssh -T git@pkgs.fedoraproject.org"
        retval = run_cmd(cmd.split())
        return retval == 0

    @staticmethod
    def git_add_all(title: str, description_msg: str):
        """
        Add and push all files into the fork.
        :param title: ???
        :param description_msg:
        """
        FramboGit.call_git_cmd("add *", msg="Add all")
        try:
            # Commit message looks like:
            # <User defined commit Title>\n\n
            # UpstreamCommitID: {hash}\n
            # UpstreamCommitLink: {repo}/commit/{hash}\n
            # UpstreamRepository: {repo}
            FramboGit.call_git_cmd(
                f"commit -m {title!r} -m {description_msg!r}", msg="Commit into distgit"
            )
        except CalledProcessError:
            pass

        try:
            FramboGit.call_git_cmd("push -u origin", msg="Push changes into git")
        except CalledProcessError:
            pass

    @staticmethod
    def clone_repo(clone_url: str, tempdir: str) -> Path:
        """
        Clone git repository from url.
        :param clone_url: url to clone from, it can also be a local path (directory)
        :param tempdir: temporary directory, where the git is cloned
        :return: directory with cloned repo or None
        """
        # clone_url can be url as well as path to directory, try to get the last part (strip .git)
        reponame = FramboGit.strip_dot_git(clone_url.split("/")[-1])
        cloned_dir = Path(tempdir) / reponame
        clone_success = True
        try:
            FramboGit.call_git_cmd(
                f"clone --recurse-submodules {clone_url} {str(cloned_dir)}"
            )
        except CalledProcessError:
            # clone git repository w/o submodule. In case submodules does not exist
            clone_success = False
        if not clone_success:
            try:
                FramboGit.call_git_cmd(f"clone {clone_url} {str(cloned_dir)}")
            except CalledProcessError:
                raise
        return cloned_dir

    @staticmethod
    def fetch_pr_origin(number: str, msg: str):
        """
        Fetch specific Pull Request.
        :param number: PR number to fetch
        :param msg: message shown in log file
        """
        # Download Upstream repo to temporary directory
        # 'git fetch origin pull/ID/head:BRANCHNAME or git checkout origin/pr/ID'
        FramboGit.call_git_cmd(
            "fetch origin pull/{n}/head:PR{n}".format(n=number), msg=msg
        )

    @staticmethod
    def sync_fork_with_origin(url, branch):
        """
        Sync fork with the latest changes from downstream origin.
        * Add downstream origin and upstream
        * fetch upstream
        * Reset commit with the latest downstream origin
        * push changes back to origin
        :param branch: Str: Name of branch to sync
        :param url: Str: URL which is add upstream into origin
        """
        FramboGit.call_git_cmd(f"remote add upstream {url}")
        FramboGit.call_git_cmd(f"fetch upstream")
        FramboGit.call_git_cmd(f"reset --hard upstream/{branch}")
        FramboGit.call_git_cmd(f"push origin {branch} --force")