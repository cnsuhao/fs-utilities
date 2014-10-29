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
import shutil
import re

from transfer_base import TransferBase


class ImageTransfer(TransferBase):
    u"""
    图片文件迁移工具

    可将目标模块依赖的所有图片文件迁移至指定目录，并自动替换所有代码中引用的图片路径。

    .. caution:: 本工具目前不支持拼接调用的图片路径，相关路径需要使用
        ``target_exclude_dirs`` 参数进行排除。

    .. note:: `ImageTransfer` 是 :class:`~FSUtils.transfer.TransferBase` 的子类。

    图片迁移工具调用方式：

    .. code:: python

        trans = ImageTransfer(
            root="./project",
            modules=["fschedule", "fservice", "fmobile"],
            target_base="com/fr/fs",
            target_excludes=["com/fr/fs/web/images/mobile/cover/"],
            target_dir="./project/fservice/src/com/fr/fs/resources/images/",
            log_dir="./log",
            log_level=logging.INFO
        )
        trans.transfer()

    :ivar list _module_dependencies: 目标模块依赖的图片索引列表，存储
        ``{"代码相对路径": [代码引用的所有图片]}`` 构成的字典。
    :ivar list _exclude_dependencies: 其余模块依赖的图片索引列表，存储
        ``{"代码相对路径": [代码引用的所有图片]}`` 构成的字典。
    :ivar set _module_images: 目标模块所用到的所有图片集合。
    :ivar set _exclude_images: 其余模块所用到的所有图片集合。
    :ivar dict _module_image_map: 目标模块中引用图片相对路径与绝对路径关系字典，key 为相对
        路径。
    :ivar list _module_in_use_images: 目标模块引用来自自身模块的图片列表。
    :ivar list _module_unused_images: 目标模块中存储的未被自身使用的图片列表。
    :ivar list _module_dependent_images: 目标模块引用的其他模块图片列表。
    :ivar list _transferred_images: 经过迁移的图片列表，储存
        ``(迁移前的调用相对路径， 迁移后的调用相对路径)`` 构成的元组。

    :ivar list source_pattern: 代码文件类型的通配符列表，形如 ``["*.java", "*.js"]``
    :ivar list img_pattern: 图片文件类型的通配符列表，形如 ``["*.jpg", "*.png"]``
    :ivar str base_dir_pattern: 工程项目中使用的非第三方图片删选基准目录，默认为
        ``com/fr`` 。
    :ivar str target_dir_pattern: 目标模块图片基础引用相对路径，如平台模块使用
        ``com/fr/fs`` 。此路径用于区分引用模块。
    :ivar list target_exclude_dirs: 目标模块中需要排除的图片引用目录列表，用于排除对合成路
        径的处理。
    :ivar str target_dir: 迁移图片的目标路径。
    """
    _img_dir_sep = ["images", "web/core"]

    _module_dependencies = []
    _exclude_dependencies = []
    _module_images = set()
    _exclude_images = set()
    _module_image_map = {}
    _module_in_use_images = []
    _module_unused_images = []
    _module_dependent_images = []
    _transferred_images = []

    source_pattern = ["*.java", "*.js", "*.css", "*.cpt", "*.frm", "*.html"]
    img_pattern = ["*.jpg", "*.png", "*.gif"]
    base_dir_pattern = "com/fr"
    target_dir_pattern = base_dir_pattern
    target_exclude_dirs = []
    target_dir = "./"

    def __init__(self, root, modules, target_base, target_excludes,
                 target_dir=None, exclude_dirs=None, log_dir=None,
                 log_level=logging.INFO):
        u"""
        初始化图片迁移工具

        :param root: 工程文件的根目录( ``project`` 目录)
        :type root: str
        :param modules: 迁移图片的目标模块目录列表，如 ``["base", "base-data"]`` 。
        :type modules: list
        :param target_base: 目标模块图片基础引用相对路径，如平台模块使用 ``com/fr/fs`` 。
            此路径用于区分引用模块。
        :type target_base: str
        :param target_excludes: 目标模块中需要排除的图片引用目录列表，用于排除对合成路径的
            处理。
        :type target_excludes: list
        :param target_dir: 迁移图片的目标路径，不设置则使用当前工作目录。
        :type target_dir: str
        :param exclude_dirs: ``project`` 下需要排除的子目录，不设置保留默认配置。
        :type exclude_dirs: list
        :param log_dir: 日志文件输出路径
        :type log_dir: str
        :param log_level: 日志记录等级
        :type log_level: int
        """
        super(ImageTransfer, self).__init__(
            root, modules, exclude_dirs=exclude_dirs, log_dir=log_dir,
            log_level=log_level)
        self.target_dir_pattern = target_base
        self.target_exclude_dirs = target_excludes
        if target_dir is not None:
            self.target_dir = target_dir
        # 按代码及工程文件路径初始化数据
        self._filter_images()
        self._filter_module_images()

    def get_source_image_path(self, src_file):
        u"""
        取出当前代码中的所有图片引用路径

        :param src_file: 代码文件路径
        :type src_file: str
        :return: 当前代码中的所有图片的引用路径
        :rtype: list
        """
        images = []
        with open(src_file) as src:
            codes = src.read()
            # 替换CR换行符
            if "\n" not in codes:
                codes = codes.replace("\r", "\n")
            extension_pattern = "|".join(
                [ext.replace("*.", "") for ext in self.img_pattern])
            regex = "(com/fr.+\.(?:%s))" % extension_pattern
            images.extend(re.findall(regex, codes))
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
            src_path = os.path.join(self.project_root, module, self._src_dir)
            img_path = os.path.join(src_path, self.target_dir_pattern)
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
                rel_path = self.reformat_path(os.path.relpath(img, src_path))
                if not self._check_target_exclude(rel_path):
                    self._module_image_map[rel_path] = img
        image_files = set(self._module_image_map.keys())
        # 引用自己模块的图片
        self._module_in_use_images = list(image_files & self._module_images)
        # 未使用的图片
        self._module_unused_images = list(image_files - self._module_images)
        # 引用其他模块的图片
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

    def transfer(self):
        u"""
        迁移图片文件
        """
        # 复制目标模块引用其他模块的图片
        for img in self._module_dependent_images:
            if not self._transfer_image(img):
                self.logger.error('Image "%s" not found.' % img)
            else:
                self.logger.info('"%s" transferred.' % img)
        # 删除目标模块中未使用图片
        for img in self._module_unused_images:
            if not self._remove_image(img):
                self.logger.error('Image "%s" not found.' % img)
            else:
                self.logger.info('"%s" removed.' % img)
        # 迁移模块自身引用的图片
        target_call_path = self.generate_call_path(self.target_dir)
        for img in self._module_in_use_images:
            # 略过已经在目标路径中的
            if img.startswith(target_call_path):
                continue
            if not self._transfer_image(img, False):
                self.logger.error('Image "%s" not found.' % img)
            else:
                self.logger.info('"%s" transferred.' % img)
        # 修改代码调用
        for img, target in self._transferred_images:
            if not self._change_source_call(img, target):
                self.logger.error('Replace "%s" error.' % img)
            else:
                self.logger.info('"%s" replaced.' % img)
        # 清理
        self.clear_target_dirs()

    def _change_source_call(self, image, target):
        u"""
        修改代码中的图片调用

        :param image: 先前的图片调用路径
        :type image: str
        :param target: 当前的图片调用路径
        :type target: str
        :return: 是否成功替换所有代码中对相关图片的引用
        :rtype: bool
        """
        success = False
        for src, src_images in self._module_dependencies:
            if image in src_images:
                src_path = os.path.join(self.project_root, src)
                # 替换代码中的图片调用
                with open(src_path, "r") as f:
                    code = f.read()
                try:
                    code = code.decode("utf-8").replace(image, target).\
                        encode("utf-8")
                except UnicodeDecodeError:
                    code = code.decode("gbk").replace(image, target).\
                        encode("gbk")
                with open(src_path, "w") as f:
                    f.write(code)
                success = True
        return success

    def _transfer_image(self, rel_path, is_copy=True):
        u"""
        基于图片调用路径迁移图片

        :param rel_path: 图片基于src目录的相对路径
        :type rel_path: str
        :param is_copy: 是否为复制模式，若为 ``False`` ，则使用移动模式。默认值为 ``True``
        :type is_copy: bool
        :return: 是否成功找到并迁移图片
        :rtype: bool
        """
        # 获取图片在目标目录的相对路径
        img_rel_path = ""
        for sep in self._img_dir_sep:
            if sep in rel_path:
                rel_split = rel_path.split(sep)
                if len(rel_split) > 1:
                    img_rel_path = rel_split[1]
                break
        # 未取出相对路径
        if not img_rel_path:
            self.logger.error('Image "%s" not found' % rel_path)
            return False
        target_path = os.path.join(self.target_dir,
                                   self.trim_rel_path(img_rel_path))
        # 通过路径搜索并完成图片迁移
        success = False
        for module in os.listdir(self.project_root):
            image_path = os.path.join(
                self.project_root, module, self._src_dir, rel_path)
            target_dir = os.path.dirname(target_path)
            if os.path.exists(image_path):
                # 检查目标路径是否存在，不存在则自动创建
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                t_path = image_path.replace(self.project_root, "(project)")
                self.logger.debug("Copy %s\n  -> %s" % (t_path, target_dir))
                shutil.copy2(image_path, target_dir)
                # 移动操作删除原图片
                if not is_copy:
                    os.remove(image_path)
                    self.logger.debug("Delete " + t_path)
                success = True
                break
        # 记录调用路径
        target_call_path = self.generate_call_path(target_path)
        self._transferred_images.append((rel_path, target_call_path))
        return success

    def _remove_image(self, rel_path):
        u"""
        基于图片调用路径搜索并移除指定图片文件

        :param rel_path: 图片基于src目录的相对路径
        :type rel_path: str
        :return: 是否成功找到并删除文件
        :rtype: bool
        """
        # 通过路径搜索删除未使用的图片
        success = False
        for module in self.target_modules:
            image_path = os.path.join(
                self.project_root, module, self._src_dir, rel_path)
            if os.path.exists(image_path):
                os.remove(image_path)
                t_path = image_path.replace(self.project_root, "(project)")
                self.logger.debug("Delete %s" % t_path)
                success = True
        return success

    def generate_call_path(self, path):
        u"""
        根据图片路径计算图片的调用相对路径

        :param path: 图片的路径，可以为相对路径或绝对路径
        :type path: str
        :return: 调用图片的相对路径，形如 ``com/fr/web/images/img.jpg``
        :rtype: str
        """
        rel = self.reformat_path(path).split(self.base_dir_pattern)[1]
        call = os.path.join(self.base_dir_pattern, self.trim_rel_path(rel))
        return self.reformat_path(call)


if __name__ == '__main__':
    trans = ImageTransfer(
        root="E:/temp/project",
        modules=["fschedule", "fservice", "fmobile"],
        target_base="com/fr/fs",
        target_excludes=["com/fr/fs/web/images/mobile/cover/"],
        target_dir="E:/temp/project/fservice/src/com/fr/fs/resources/images/",
        log_dir="E:/temp",
        log_level=logging.ERROR
    )
    trans.transfer()
