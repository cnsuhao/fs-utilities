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


class LocaleTransfer(TransferBase):
    u"""
    国际化文本迁移工具

    用于国际化内容的模块间迁移，减少在分离模块后跨模块的国际化调用，减少模块间不必要的依赖。

    .. note:: `LocaleTransfer` 是 :class:`~FSUtils.transfer.TransferBase` 的子类。

    :ivar list locales: 支持的国际化标识符
    :ivar str locale_suffix: 国际化资源文件扩展名
    :ivar list source_pattern: 代码文件类型的通配符列表
    :ivar str original_locale_rel_path: 源国际化资源文件到根目录的相对路径
    :ivar str original_locale_name: 源国际化资源文件名，如 ``fr``

    :ivar str target_locale_rel_path: 目标模块国际化资源文件到根目录的相对路径
    :ivar str target_locale_name: 目标模块国际化资源文件名，如 ``fr``
    :ivar str log_path: 输出信息的位置

    :ivar dict all_locales: 缓存的国际化
    :ivar list move_keys: 需要移动的国际化列表
    :ivar list duplicate_keys: 模块共用的国际化列表
    :ivar list fragmented_keys: 不完整的国际化列表
    :ivar tuple locale_files: 缓存的国际化文件路径
    """
    __main_locale_tag = "main"

    locales = ["en_US", "zh_CN", "zh_TW", "ja_JP"]
    locale_suffix = ".properties"
    source_pattern = ["*.java", "*.js"]
    original_locale_rel_path = "base-file/src/com/fr/general/locale"
    original_locale_name = "fr"

    target_locale_rel_path = ""
    target_locale_name = ""
    log_path = "./"

    all_locales = {}
    move_keys = []
    duplicate_keys = []
    fragmented_keys = []
    locale_files = ()

    def __init__(self, root, modules, target_rel_path, target_locale,
                 work_dir="./", exclude_dirs=None):
        u"""
        对国际化文本迁移工具初始化

        :param root: 工程文件的根目录( ``project`` 目录)
        :type root: str
        :param modules: 迁移国际化内容的目标模块列表
        :type modules: list
        :param target_rel_path: 目标模块国际化资源文件到根目录的相对路径
        :type target_rel_path: str
        :param target_locale: 目标模块国际化资源文件名，如 ``fr``
        :type target_locale: str
        :param work_dir: 输出信息的位置
        :type work_dir: str
        :param exclude_dirs: ``project`` 下需要排除的子目录
        :type exclude_dirs: list
        """
        super(LocaleTransfer, self).__init__(
            root, modules, exclude_dirs=exclude_dirs, log_dir=work_dir)
        self.target_locale_rel_path = target_rel_path
        self.target_locale_name = target_locale
        self.log_path = work_dir
        # 从国际化资源文件初始化数据
        self._load_all_locale()
        self._load_locale_files()
        self._filter_locale_keys()

    @staticmethod
    def get_source_locale_keys(src_file):
        u"""
        取出当前代码中的所有国际化查询键

        :param src_file: 代码文件路径
        :type src_file: str
        :return: 当前代码中的所有国际化查询键
        :rtype: list
        """
        locale_keys = []
        with open(src_file) as src:
            codes = src.readlines()
            for line in codes:
                locale_keys.extend(re.findall(
                    'Inter\.getLocText\("(.+?)"\)', line))
                locale_keys.extend(re.findall(
                    'FR\.i18nText\("(.+?)"\)', line))
        return locale_keys

    def _get_locale_filename(self, base, locale=None):
        u"""
        生成国际化资源文件名

        :param base: 国际化主资源文件名
        :type base: str
        :param locale: 本地化标识
        :type locale: str
        :return: 国际化资源文件名
        :rtype: str
        """
        if locale is not None:
            filename = base + "_" + locale + self.locale_suffix
        else:
            filename = base + self.locale_suffix
        return filename

    def _load_locale_map(self, path, base, locale=None):
        u"""
        读取指定国际化文件中的键值映射

        :param path: 国际化资源文件在工程文件中的相对路径
        :type path: str
        :param base: 国际化主资源文件名
        :type base: str
        :param locale: 本地化标识
        :type locale: str
        :return: 国际化键值映射
        :rtype: dict
        """
        locale_map = {}
        filename = self._get_locale_filename(base, locale)
        with open(os.path.join(path, filename)) as loc:
            lines = loc.readlines()
            for line in lines:
                l = line.split("=", 1)
                if len(l) < 2:
                    continue
                (k, v) = tuple(l)
                locale_map[k] = v.strip('\n')
        return locale_map

    def _load_all_locale(self):
        u"""
        读取并缓存所有原国际化文件中的国际化内容
        """
        all_locales = {}
        old_locale_path = os.path.join(
            self.project_root, self.original_locale_rel_path)
        # 默认国际化文件中的内容
        for k, v in self._load_locale_map(
                old_locale_path, self.original_locale_name
        ).iteritems():
            all_locales[k] = {self.__main_locale_tag: v}
        # 本地化的文件内容
        for locale in self.locales:
            for k, v in self._load_locale_map(
                    old_locale_path, self.original_locale_name, locale
            ).iteritems():
                all_locales[k][locale] = v
        self.all_locales = all_locales

    def _filter_locale_keys(self):
        u"""
        取出需要处理的国际化信息
        """
        module_keys = []
        exclude_keys = []
        # 收集代码文件路径
        self.collect_source_files()
        # 搜索国际化查询键
        for src in self._module_files:
            module_keys.extend(
                self.get_source_locale_keys(os.path.abspath(src)))
        for src in self._exclude_files:
            exclude_keys.extend(
                self.get_source_locale_keys(os.path.abspath(src)))
        # 去重
        module_keys = set(module_keys)
        exclude_keys = set(exclude_keys)
        # 取出需要移动、模块共用的国际化查询键
        move_keys = module_keys - exclude_keys
        move_keys = list(set(self.all_locales.keys()) & move_keys)
        shared_keys = list(module_keys & exclude_keys)
        move_keys.sort()
        shared_keys.sort()
        # 不完整的国际化内容
        for k in move_keys:
            if not self._check_locale_complete(k):
                self.fragmented_keys.append(k)
        self.move_keys, self.duplicate_keys = move_keys, shared_keys

    def _check_locale_complete(self, key):
        u"""
        按键检查国际化字符串是否完整

        :param key: 查询键
        :type key: str
        :return: 国际化字符串是否完整
        :rtype: bool
        """
        locale = self.all_locales[key]
        if len(locale) < 5:
            return False
        for k, v in locale.iteritems():
            if len(v) == 0:
                return False
        return True

    def transfer(self):
        u"""
        移动国际化文本
        """
        original, target = self.locale_files
        # 移除模块独立的国际化内容
        for path in original.values():
            with open(path, "r") as f:
                lines = f.readlines()
            with open(path, "w") as f:
                for line in lines:
                    k = line.split("=", 1)
                    # 跳过无关行
                    if len(k) < 2:
                        f.write(line)
                        continue
                    k = tuple(k)[0]
                    # 删除行
                    if k not in self.move_keys:
                        f.write(line)
        # 将移动的国际化内容增加到目标模块
        for locale, path in target.iteritems():
            with open(path, "r+") as f:
                add_keys = self.move_keys
                lines = f.readlines()
                for line in lines:
                    k = line.split("=", 1)
                    # 跳过无关行
                    if len(k) < 2:
                        continue
                    k = tuple(k)[0]
                    # 去重
                    if k in self.move_keys:
                        add_keys.remove(k)
                # 追加
                for k in add_keys:
                    line_buffer = [
                        k, "=", self.all_locales[k][locale], self._eol]
                    f.write("".join(line_buffer))

    def _load_locale_files(self):
        u"""
        加载国际化资源文件路径
        """
        # 源国际化资源文件
        original_path = os.path.join(
            self.project_root, self.original_locale_rel_path)
        # 默认的国际化文件
        original_main = os.path.join(
            original_path, self._get_locale_filename(self.original_locale_name)
        )
        original_files = {self.__main_locale_tag: original_main}
        # 本地化的国际化文件
        for locale in self.locales:
            original_locale_file = os.path.join(
                original_path,
                self._get_locale_filename(self.original_locale_name, locale))
            original_files[locale] = original_locale_file
        # 目标国际化资源文件
        target_path = os.path.join(
            self.project_root, self.target_locale_rel_path)
        # 默认的国际化文件
        target_main = os.path.join(
            target_path, self._get_locale_filename(self.target_locale_name))
        target_files = {self.__main_locale_tag: target_main}
        # 本地化的国际化文件
        for locale in self.locales:
            target_locale_file = os.path.join(
                target_path,
                self._get_locale_filename(self.target_locale_name, locale))
            target_files[locale] = target_locale_file
        self.locale_files = (original_files, target_files)

    def dump_warning(self):
        u"""
        输出需要注意的国际化内容
        """
        # 目标模块与其他模块共用的内容
        dup_file = os.path.join(self.log_path, "shared.txt")
        with open(dup_file, "w+") as f:
            for k in self.duplicate_keys:
                f.write(k + self._eol)
        # 本地化不完整的内容
        frag_file = os.path.join(self.log_path, "fragmented.txt")
        with open(frag_file, "w+") as f:
            for k in self.fragmented_keys:
                f.write(k + self._eol)


if __name__ == "__main__":
    PROJECT_ROOT = "../../FineReport/SVN/code/project/"
    TARGET_REL_PATH = "fservice/src/com/fr/fs/resources"
    LOG_PATH = "./"
    FS_LOCALE_NAME = "fs"
    FS_MODULES = ["fschedule", "fservice", "fmobile"]
    EXCLUDE_DIRS = ["out", ".svn"]

    trans = LocaleTransfer(PROJECT_ROOT, FS_MODULES, TARGET_REL_PATH,
                           FS_LOCALE_NAME, LOG_PATH, EXCLUDE_DIRS)
    trans.transfer()
    trans.dump_warning()
