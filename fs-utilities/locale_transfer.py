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


class LocaleTransfer(object):
    """

    """
    __main_locale_tag = "main"
    __eol = "\n"

    _locales = ["en_US", "zh_CN", "zh_TW", "ja_JP"]
    _locale_suffix = ".properties"
    _source_pattern = ["*.java", "*.js"]
    _original_locale_rel_path = "base-file/src/com/fr/general/locale"
    _original_locale_name = "fr"

    target_modules = []
    target_locale_rel_path = ""
    target_locale_name = ""
    project_root = "./"
    log_path = "./"

    all_locales = {}
    move_keys = []
    duplicate_keys = []
    fragmented_keys = []
    locale_files = ()

    def __init__(self, root, modules, target_rel_path, target_locale,
                 log_path="./"):
        self.project_root = root
        self.target_modules = modules
        self.target_locale_rel_path = target_rel_path
        self.target_locale_name = target_locale
        self.log_path = log_path
        # initialize locale data from source file
        self.load_all_locale()
        self.load_locale_files()
        self.filter_locale_keys()

    @staticmethod
    def get_source_locale_keys(src_file):
        locale_keys = []
        with open(src_file) as src:
            codes = src.readlines()
            for line in codes:
                locale_keys.extend(re.findall(
                    'Inter\.getLocText\("(.+?)"\)', line))
                locale_keys.extend(re.findall(
                    'FR\.i18nText\("(.+?)"\)', line))
        return locale_keys

    def get_locale_filename(self, base, locale=None):
        if locale is not None:
            filename = base + "_" + locale + self._locale_suffix
        else:
            filename = base + self._locale_suffix
        return filename

    def load_locale_map(self, path, base, locale=None):
        locale_map = {}
        filename = self.get_locale_filename(base, locale)
        with open(os.path.join(path, filename)) as loc:
            lines = loc.readlines()
            for line in lines:
                l = line.split("=", 1)
                if len(l) < 2:
                    continue
                (k, v) = tuple(l)
                locale_map[k] = v.strip('\n')
        return locale_map

    def load_all_locale(self):
        all_locales = {}
        old_locale_path = os.path.join(
            self.project_root, self._original_locale_rel_path)
        for k, v in self.load_locale_map(
                old_locale_path, self._original_locale_name
        ).iteritems():
            all_locales[k] = {self.__main_locale_tag: v}
        for locale in self._locales:
            for k, v in self.load_locale_map(
                    old_locale_path, self._original_locale_name, locale
            ).iteritems():
                all_locales[k][locale] = v
        self.all_locales = all_locales

    def get_module_files(self, module):
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

    def filter_locale_keys(self):
        module_keys = []
        exclude_keys = []
        module_files = []
        exclude_files = []
        # collect i18n files
        for module in self.target_modules:
            module_files.extend(self.get_module_files(module))
        for module in os.listdir(self.project_root):
            if module not in self.target_modules:
                exclude_files.extend(self.get_module_files(module))
        # search i18n keys
        for src in module_files:
            module_keys.extend(
                self.get_source_locale_keys(os.path.abspath(src)))
        for src in exclude_files:
            exclude_keys.extend(
                self.get_source_locale_keys(os.path.abspath(src)))
        # distinct
        module_keys = set(module_keys)
        exclude_keys = set(exclude_keys)
        # filter keys
        move_keys = module_keys - exclude_keys
        move_keys = list(set(self.all_locales.keys()) & move_keys)
        duplicate_keys = list(module_keys & exclude_keys)
        move_keys.sort()
        duplicate_keys.sort()
        # fragmented keys
        for k in move_keys:
            if not self.check_locale_complete(k):
                self.fragmented_keys.append(k)
        self.move_keys, self.duplicate_keys = move_keys, duplicate_keys

    def check_locale_complete(self, key):
        locale = self.all_locales[key]
        if len(locale) < 5:
            return False
        for k, v in locale.iteritems():
            if len(v) == 0:
                return False
        return True

    def transfer(self):
        original, target = self.locale_files
        # remove from original
        for path in original.values():
            with open(path, "r") as f:
                lines = f.readlines()
            with open(path, "w") as f:
                for line in lines:
                    k = line.split("=", 1)
                    if len(k) < 2:
                        f.write(line)
                        continue
                    k = tuple(k)[0]
                    if k not in self.move_keys:
                        f.write(line)
        # append to target
        for locale, path in target.iteritems():
            with open(path, "r+") as f:
                add_keys = self.move_keys
                lines = f.readlines()
                for line in lines:
                    k = line.split("=", 1)
                    if len(k) < 2:
                        continue
                    k = tuple(k)[0]
                    if k in self.move_keys:
                        add_keys.remove(k)
                for k in add_keys:
                    line_buffer = [
                        k, "=", self.all_locales[k][locale], self.__eol]
                    f.write("".join(line_buffer))
        self.dump_warning()

    def load_locale_files(self):
        # original locale
        original_path = os.path.join(
            self.project_root, self._original_locale_rel_path)
        original_main = os.path.join(
            original_path, self.get_locale_filename(self._original_locale_name))
        original_files = {self.__main_locale_tag: original_main}
        for locale in self._locales:
            original_locale_file = os.path.join(
                original_path,
                self.get_locale_filename(self._original_locale_name, locale))
            original_files[locale] = original_locale_file
        # target locale
        target_path = os.path.join(
            self.project_root, self.target_locale_rel_path)
        target_main = os.path.join(
            target_path, self.get_locale_filename(self.target_locale_name))
        target_files = {self.__main_locale_tag: target_main}
        for locale in self._locales:
            target_locale_file = os.path.join(
                target_path,
                self.get_locale_filename(self.target_locale_name, locale))
            target_files[locale] = target_locale_file
        self.locale_files = (original_files, target_files)

    def dump_warning(self):
        dup_file = os.path.join(self.log_path, "duplicate.txt")
        with open(dup_file, "w+") as f:
            for k in self.duplicate_keys:
                f.write(k + self.__eol)
        frag_file = os.path.join(self.log_path, "fragmented.txt")
        with open(frag_file, "w+") as f:
            for k in self.fragmented_keys:
                f.write(k + self.__eol)


if __name__ == "__main__":
    PROJECT_ROOT = "../../FineReport/SVN/code/project/"
    TARGET_REL_PATH = "fservice/src/com/fr/fs/resources"
    LOG_PATH = "./"
    FS_LOCALE_NAME = "fs"
    FS_MODULES = ["fschedule", "fservice", "fprocess", "fmobile"]

    trans = LocaleTransfer(PROJECT_ROOT, FS_MODULES, TARGET_REL_PATH,
                           FS_LOCALE_NAME, LOG_PATH)
    trans.transfer()
