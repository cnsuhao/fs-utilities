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
import logging
import os


class TransferBase(object):
    u"""
    :ivar list _module_files:
    :ivar list _exclude_files:
    :ivar
    :ivar list source_pattern: 代码文件类型的通配符列表
    :ivar str project_root: 工程文件的根目录("project"目录)
    :ivar list target_modules: 迁移国际化内容的目标模块列表
    :ivar list exclude_dirs: "project"下需要排除的子目录
    """
    _eol = "\n"
    _indent = " " * 4

    _module_files = []
    _exclude_files = []

    logger = None

    source_pattern = []
    project_root = "./"
    target_modules = []
    exclude_dirs = ["out", ".svn", ".idea"]

    def __init__(self, root, modules, exclude_dirs=None,
                 log_dir=None, log_level=logging.INFO):
        u"""

        :param root: 工程文件的根目录("project"目录)
        :type root: str
        :param modules: 迁移国际化内容的目标模块列表
        :type modules: list
        :param exclude_dirs: "project"下需要排除的子目录
        :type exclude_dirs: list
        """
        self.project_root = root
        self.target_modules = modules
        self.__init_logger(log_dir, log_level)
        if exclude_dirs is not None:
            self.exclude_dirs = exclude_dirs

    def __init_logger(self, log_dir=None, level=logging.INFO):
        if not log_dir:
            log_dir = "./"
        fmt = logging.Formatter(
            fmt='%(asctime)s \n%(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        file_handler = logging.FileHandler(
            filename=os.path.join(log_dir, 'log.txt'), mode='a')
        file_handler.setFormatter(fmt)
        logging.basicConfig(
            level=level,
            format='%(asctime)s \n%(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger("fr")
        self.logger.addHandler(file_handler)

    def collect_source_files(self):
        u"""
        收集代码文件路径
        """
        for module in self.target_modules:
            self._module_files.extend(self.get_module_files(module))
        for module in os.listdir(self.project_root):
            if module in self.exclude_dirs:
                continue
            if module not in self.target_modules:
                self._exclude_files.extend(self.get_module_files(module))

    def get_module_files(self, module):
        u"""
        获取模块中的所有代码文件

        :param module: 模块包目录名称，如`base`
        :type module: str
        """
        src_files = []
        module_path = os.path.join(self.project_root, module)
        for root, dirs, files in os.walk(module_path):
            if ".svn" in root:
                continue
            for d in dirs:
                file_path = lambda p: os.path.join(root, d, p)
                for pattern in self.source_pattern:
                    # 检索代码文件
                    files = glob.glob(file_path(pattern))
                    src_files.extend(files)
        return src_files

    @staticmethod
    def reformat_path(path):
        return path.replace("\\", "/")

    @staticmethod
    def trim_rel_path(rel_path):
        if rel_path.startswith("/"):
            return rel_path[1:]
        return rel_path
