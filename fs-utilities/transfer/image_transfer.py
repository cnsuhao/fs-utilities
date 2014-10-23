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
import re


class ImageTransfer(object):
    _source_pattern = ["*.java", "*.js", "*.css"]

    project_root = "./"
    target_image_path = ""

    @staticmethod
    def get_source_image_path(src_file):
        with open(src_file) as src:
            codes = src.readlines()
            for line in codes:
                re.findall('com.+\.(png|jpg|gif)', line)

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
                for pattern in self._source_pattern:
                    # filter source code
                    files = glob.glob(file_path(pattern))
                    for src_file in files:
                        src_files.append(src_file)
        return src_files
