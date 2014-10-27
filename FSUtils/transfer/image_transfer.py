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
import shutil
import re

from transfer_base import TransferBase


class ImageTransfer(TransferBase):
    u"""
    :ivar list source_pattern: 代码文件类型的通配符列表
    """
    __src_dir = "src"

    _module_dependencies = []
    _exclude_dependencies = []
    _module_images = set()
    _exclude_images = set()
    _module_image_map = {}
    _module_unused_images = []
    _module_dependent_images = []
    _not_found_images = []

    source_pattern = ["*.java", "*.js", "*.css", "*.cpt", "*.frm", "*.html"]
    img_pattern = ["*.jpg", "*.png", "*.gif"]
    exclude_base_dir = "com/fr"
    target_base_dir = "com/fr"
    target_exclude_dirs = []
    work_dir = "./"

    def __init__(self, root, modules, target_base, target_excludes, work_dir,
                 exclude_dirs=None):
        u"""
        :param root: 工程文件的根目录("project"目录)
        :type root: str
        :param modules: 迁移图片的目标模块列表
        :type modules: list
        :param target_base:
        :type target_base: str
        :param target_excludes:
        :type target_excludes: list
        :param work_dir: 输出路径
        :type work_dir: str
        :param exclude_dirs: "project"下需要排除的子目录
        :type exclude_dirs: list
        """
        super(ImageTransfer, self).__init__(root, modules, exclude_dirs)
        self.target_base_dir = target_base
        self.target_exclude_dirs = target_excludes
        self.work_dir = work_dir
        self._filter_images()
        self._filter_module_images()

    @staticmethod
    def get_source_image_path(src_file):
        u"""
        取出当前代码中的所有图片引用路径

        :param src_file: 代码文件路径
        :type src_file: str
        :return: 当前代码中的所有图片引用路径
        ：:rtype: list
        """
        images = []
        with open(src_file) as src:
            codes = src.read()
            # 替换CR换行符
            if "\n" not in codes:
                codes = codes.replace("\r", "\n")
            images.extend(
                re.findall('(com/fr.+\.(?:png|jpg|gif))', codes))
        return images

    def _filter_images(self):
        u"""
        取出代码中的图片调用信息
        """
        # 收集代码文件路径
        self.collect_source_files()
        # 搜索图片调用
        for src in self._module_files:
            images = self.get_source_image_path(src)
            src_path = os.path.relpath(src, self.project_root)
            if len(images) > 0:
                self._module_dependencies.append((src_path, images))
        for src in self._exclude_files:
            images = self.get_source_image_path(src)
            src_path = os.path.relpath(src, self.project_root)
            if len(images) > 0:
                self._exclude_dependencies.append((src_path, images))
        # 整理目标模块以及其余模块的图片调用
        for src, dep in self._module_dependencies:
            self._module_images |= set(dep)
        for src, dep in self._exclude_dependencies:
            self._exclude_images |= set(dep)
        # 去除目标模块需排除下的图片
        self._module_images = set(
            [img for img in self._module_images
             if not self._check_target_exclude(img)])

    def _filter_module_images(self):
        u"""
        检索目标模块依赖的其他模块图片以及目标模块中未使用的图片文件
        """
        for module in self.target_modules:
            module_images = []
            src_path = os.path.join(self.project_root, module, self.__src_dir)
            img_path = os.path.join(src_path, self.target_base_dir)
            # 取出所有图片文件信息
            for root, dirs, files in os.walk(img_path):
                if ".svn" in root:
                    continue
                for d in dirs:
                    file_path = lambda p: os.path.join(root, d, p)
                    for pattern in self.img_pattern:
                        files = glob.glob(file_path(pattern))
                        module_images.extend(files)
            # 建立相对路径与绝对路径映关系
            for img in module_images:
                rel_path = os.path.relpath(img, src_path).replace("\\", "/")
                if not self._check_target_exclude(rel_path):
                    self._module_image_map[rel_path] = img
        image_files = set(self._module_image_map.keys())
        self._module_unused_images = list(image_files - self._module_images)
        self._module_dependent_images = list(self._module_images - image_files)

    def _check_target_exclude(self, rel_path):
        u"""
        判断当前图片所在路径是否需要排除

        :param rel_path: 待判断图片的相对路径
        :type rel_path: str
        :return: 是否需要排除该图片
        :rtype: bool
        """
        for ex_dir in self.target_exclude_dirs:
            if rel_path.startswith(ex_dir):
                return True
        return False

    def copy_module_images(self):
        u"""

        """
        for img in self._module_dependent_images:
            if not self._copy_image(img):
                self._not_found_images.append(img)

    def _copy_image(self, img):
        u"""
        将图片按层级复制到目标路径

        :param img: 图片基于src目录的相对路径
        :type img: str
        :return: 是否成功复制图片
        :rtype: bool
        """
        copied = False
        for module in os.listdir(self.project_root):
            if module in self.exclude_dirs:
                continue
            if module not in self.target_modules:
                image_path = os.path.join(
                    self.project_root, module, self.__src_dir, img)
                target_dir = os.path.join(self.work_dir, os.path.dirname(img))
                if os.path.exists(image_path):
                    # 检查目标路径是否存在，不存在则自动创建
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    print("copy: "
                          + image_path.replace(self.project_root, "(project)")
                          + "\n  -> " + target_dir)
                    shutil.copy2(image_path, target_dir)
                    copied = True
                    break
        return copied

    def output_module_dependent(self):
        dependencies = {}
        for src, dep in self._module_dependencies:
            src_dep = list(set(dep) & set(self._module_dependent_images))
            if len(src_dep) > 0:
                dependencies[src] = src_dep
        outfile = os.path.join(self.work_dir, "fr_images.txt")
        with open(outfile, "w+") as f:
            f.write("Module Dependencies: " + self._eol)
            for src, src_dep in dependencies.iteritems():
                f.write(src + self._eol)
                for dep in src_dep:
                    f.write(self._indent + dep + self._eol)
            f.write(self._eol)
            if len(self._not_found_images) > 0:
                f.write("Not found:" + self._eol)
                for img in self._not_found_images:
                    f.write(img + self._eol)

if __name__ == '__main__':
    PROJECT_ROOT = u"D:/工作/FineReport/SVN/code/project"
    FS_MODULES = ["fschedule", "fservice", "fmobile"]
    FS_IMG_BASE = "com/fr/fs"
    EXCLUDE_IMG_DIRS = ["com/fr/fs/web/images/mobile/cover/"]
    OUTPUT_DIR = "E:/temp"

    trans = ImageTransfer(PROJECT_ROOT, FS_MODULES, FS_IMG_BASE,
                          EXCLUDE_IMG_DIRS, OUTPUT_DIR)
    trans.copy_module_images()
    trans.output_module_dependent()
