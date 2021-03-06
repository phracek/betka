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

from betka.pagure import PagureAPI
from betka.constants import SYNCHRONIZE_BRANCHES
from tests.conftest import no_pullrequest, one_pullrequest, config_json


class TestBetkaPagure(object):
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
        self.pa = PagureAPI(betka_config=self.betka_config(), config_json=config_json())
        self.pa.image = "foobar"

    @pytest.mark.parametrize(
        "branches,status_code,expected",
        [
            (
                {"branches": ["f30", "master", "private"]},
                200,
                ["f30", "master", "private"],
            ),
            ({"branches": ["f30", "master", "private"]}, 400, []),
        ],
    )
    def test_get_branches(self, branches, status_code, expected):
        flexmock(PagureAPI, get_status_and_dict_from_request=(status_code, branches))
        assert self.pa.get_branches() == expected

    @pytest.mark.parametrize(
        "json_file,branch,check_user,return_code",
        [
            (no_pullrequest(), "upstream/f30", False, None),
            (one_pullrequest(), "f30", False, None),
            (one_pullrequest(), "f30", False, None),
            (one_pullrequest(), "f28", False, 5),
            (one_pullrequest(), "f28", True, 5),
        ],
    )
    def test_downstream_pull_requests(self, json_file, branch, check_user, return_code):
        flexmock(self.pa).should_receive("get_status_and_dict_from_request").with_args(
            url="https://src.fedoraproject.org/api/0/container/foobar/pull-requests"
        ).and_return(200, json_file)
        self.pa.betka_config = self.betka_config()
        assert (
            self.pa.check_downstream_pull_requests(branch=branch, check_user=check_user)
            == return_code
        )
