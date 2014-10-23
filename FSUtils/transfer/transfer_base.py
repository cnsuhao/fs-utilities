#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyleft (C) 2014 - kyle <kyle@finereport.com>
# =============================================================================
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# =============================================================================

__author__ = 'kyle'

import glob
import os


class TransferBase(object):
    source_pattern = ["*.*"]
    project_root = "./"

    def __init__(self, root):
        self.project_root = root

    def get_module_files(self, module):
        u"""
        获取模块中的所有代码文件

        :param module: 模块包目录名称，如`base`
        :type module: str
        """
        src_files = []
        module_path = os.path.join(self.project_root, module)
        for root, dirs, files in os.walk(module_path):
            for d in dirs:
                if ".svn" in d:
                    continue
                file_path = lambda rel_path: os.path.join(root, d, rel_path)
                for pattern in self.source_pattern:
                    # filter source code
                    files = glob.glob(file_path(pattern))
                    for src_file in files:
                        src_files.append(src_file)
        return src_files
