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


"""Test betka core class"""

import pytest

from flexmock import flexmock

from betka.gitlab import GitLabAPI
from betka.constants import SYNCHRONIZE_BRANCHES
from tests.conftest import (
    config_json,
    two_mrs_both_valid,
    two_mrs_not_valid,
    two_mrs_one_valid,
    branches_list_full,
    get_user_valid,
    get_missing_user_valid

)
from tests.spellbook import PROJECT_ID


class TestBetkaGitlab(object):
    def betka_config(self):
        return {
            SYNCHRONIZE_BRANCHES: ["f3", "master"],
            "version": "1",
            "dist_git_repos": {
                "s2i-core": ["https://github.com/sclorg/s2i-base-container"]
            },
            "pagure_user": "foo",
            "downstream_master_msg": "[betka-master-sync]",
        }

    def setup_method(self):
        self.ga = GitLabAPI(betka_config=self.betka_config(), config_json=config_json())
        self.ga.image = "foobar"
        self.ga.project_id = PROJECT_ID

    def test_get_branches(self):
        flexmock(self.ga).should_receive("gitlab_get_action").with_args(
            url=f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/repository/branches"
        ).and_return(200, branches_list_full())
        assert self.ga.get_branches() == ["rhel-8.6.0", "rhel-8.8.0"]

    @pytest.mark.parametrize(
        "json_file,branch,mr_id",
        [
            (two_mrs_both_valid(), "rhel-8.6.0", 2),
            (two_mrs_both_valid(), "rhel-8.8.0", 1),
            (two_mrs_both_valid(), "rhel-8.7.0", None),
        ],
    )
    def test_mrs_valid(self, json_file, branch, mr_id):
        flexmock(self.ga).should_receive("gitlab_get_action").with_args(
            url=f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/merge_requests?state=opened"
        ).and_return(200, json_file)
        self.ga.betka_config = self.betka_config()
        assert (
            self.ga.check_gitlab_merge_requests(branch=branch)
            == mr_id
        )

    @pytest.mark.parametrize(
        "json_file,branch,mr_id",
        [
            (two_mrs_not_valid(), "rhel-8.6.0", None),
            (two_mrs_not_valid(), "rhel-8.8.0", None),
            (two_mrs_not_valid(), "rhel-8.7.0", None),
        ],
    )
    def test_mrs_not_filed_by_betka(self, json_file, branch, mr_id):
        flexmock(self.ga).should_receive("gitlab_get_action").with_args(
            url=f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/merge_requests?state=opened"
        ).and_return(200, json_file)
        self.ga.betka_config = self.betka_config()
        assert (
            self.ga.check_gitlab_merge_requests(branch=branch)
            == mr_id
        )

    def test_mrs_one_valid(self):
        flexmock(self.ga).should_receive("gitlab_get_action").with_args(
            url=f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/merge_requests?state=opened"
        ).and_return(200, two_mrs_one_valid())
        self.ga.betka_config = self.betka_config()
        assert (
            self.ga.check_gitlab_merge_requests(branch="rhel-8.6.0")
            == 2
        )

    @pytest.mark.parametrize(
        "host,namespace,image,branch,file,result_url",
        [
            ("https://src.fedoraproject.org", "containers", "postgresql", "", "bot-cfg.yml",
             "https://src.fedoraproject.org/containers/postgresql/-/raw//bot-cfg.yml"),
            ("https://src.fedoraproject.org", "containers", "postgresql", "master", "foo-bar.yaml",
             "https://src.fedoraproject.org/containers/postgresql/-/raw/master/foo-bar.yaml"),
            ("https://src.fedoraproject.org",  "containers", "dummy-container", "f36", "foo-bar.yaml",
             "https://src.fedoraproject.org/containers/dummy-container/-/raw/f36/foo-bar.yaml"),
        ],
    )
    def test_cfg_url(self, host, namespace, image, branch, file, result_url):
        self.ga.config_json["gitlab_host_url"] = host
        self.ga.config_json["gitlab_namespace"] = namespace
        self.ga.image = image

        assert result_url == self.ga.cfg_url(branch=branch, file=file)

    def test_valid_user(self):
        flexmock(self.ga).should_receive("gitlab_get_action").with_args(
            url=f"https://gitlab.com/api/v4/user"
        ).and_return(200, get_user_valid())
        self.ga.betka_config = self.betka_config()
        assert self.ga.get_user_from_token() == "phracek"

    def test_missing_user(self):
        flexmock(self.ga).should_receive("gitlab_get_action").with_args(
            url=f"https://gitlab.com/api/v4/user"
        ).and_return(200, get_missing_user_valid())
        self.ga.betka_config = self.betka_config()
        assert self.ga.get_user_from_token() is None

    def test_wrong_resp_user(self):
        flexmock(self.ga).should_receive("gitlab_get_action").with_args(
            url=f"https://gitlab.com/api/v4/user"
        ).and_return(400, get_user_valid())
        self.ga.betka_config = self.betka_config()
        assert self.ga.get_user_from_token() is None