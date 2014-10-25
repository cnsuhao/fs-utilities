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

import os
import re

from transfer_base import TransferBase


class ImageTransfer(TransferBase):
    u"""
    :ivar list source_pattern: 代码文件类型的通配符列表
    """
    source_pattern = ["*.java", "*.js", "*.css", "*.cpt", "*.frm"]
    target_image_path = ""

    def __init__(self, root, modules, exclude_dirs=None):
        super(ImageTransfer, self).__init__(root, modules, exclude_dirs)
        self._filter_images()

    @staticmethod
    def get_source_image_path(src_file):
        images = []
        with open(src_file) as src:
            codes = src.read()
            images.extend(
                re.findall('(com/fr.+\.(png|jpg|gif))', codes))
        return images

    def _filter_images(self):
        module_images = []
        exclude_images = []
        # 收集代码文件路径
        self.collect_source_files()
        for src in self._module_files:
            images = self.get_source_image_path(src)
            src_path = os.path.relpath(src, self.project_root)
            if len(images) > 0:
                module_images.append((src_path, images))
        for src in self._exclude_files:
            images = self.get_source_image_path(src)
            src_path = os.path.relpath(src, self.project_root)
            if len(images) > 0:
                exclude_images.append((src_path, images))
        for src in exclude_images:
            print(src)


if __name__ == '__main__':
    PROJECT_ROOT = "D:/Work/FineReport/SVN/code/project"
    FS_MODULES = ["fschedule", "fservice", "fmobile"]
    trans = ImageTransfer(PROJECT_ROOT, FS_MODULES)
